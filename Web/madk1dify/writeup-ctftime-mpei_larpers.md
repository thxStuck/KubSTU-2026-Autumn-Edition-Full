# madk1dify — Community Writeup

> **Команда-автор:** mpei_larpers
> **Источник:** https://ctftime.org/writeup/41130 (CTFtime, пользовательский райтап)
> **Событие:** KubSTU CTF 2026: Autumn
> _Это командный (пользовательский) райтап, скачан с CTFtime._

---

# KubSTU CTF 2026 Autumn — madk1dify (Web)

**Флаг: `KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}`**

---

## Условие задачи

Флаг спрятан в невышедшем материале артиста — посмотрим, кто устоит перед искушением.

Формулировка: «Listen, I really like madk1d, and his album is just incredible.  
I'm looking forward to sexyswag 2».

Дано два зеркала:

- http://141.133.198.7:8080  
- http://159.194.249.251:8080

## Что дано

Клон Spotify артиста madk1d:

- публичный каталог релизов и плейлистов;  
- артист-воркспейс `/studio` (открывается после регистрации любым юзером);  
- партнёрский API: GraphQL `/api-partner/pathfinder/graphql` + REST `/api/v1/...`.

В студии — таблица «Release queue»: 14 позиций нерелизнутого материала,  
тайтлы скрыты («Scheduled — details withheld»), с подписью «Titles and references  
are served by the partner API, not by this page». Флаг — это «download code»  
невышедшего альбома sexyswag 2.

---

## Шаг 1. Разведка и вход в студию

- `robots.txt` сам перечисляет интересное: `/api/`, `/studio`, `/internal/`,  
  `/.env.example`; в футере страниц — скрытая ссылка `admin backup` →  
  `/internal/admin-backup` (403).  
- Регистрация: `POST /register` (username/password) → сессионная кука → `/studio`.  
- Студия отдаёт каталог из 5 релизов (у каждого `catalogRef` и ссылка  
  `credits.json`) и «Release queue» из 14 нерелизнутых позиций: детали  
  придержаны, но сказано, что тайтлы и ссылки отдаёт partner API.

## Шаг 2. Анти-бот-тикет (bootstrap → PoW → hs)

Все `/api/*` требуют тикет `mdk_sid`, который выдаёт хендшейк:

- страница приносит `meta mdk-c`, случайные CSS-переменные в `:root` и случайные  
  `data-*` атрибуты;  
- `GET /api/bootstrap?c=<mdk-c>` → JIT-пазл `p`, seed `s`, сложность `d=3`;  
- `a = new Function(p)()` — пазл просто читает переменные/атрибуты со страницы;  
- `n`: `sha256(s + ":" + n)` начинается с `d` нулей;  
- `POST /api/hs {s,g,n,c,a,f}` → `{ok,k}` + `Set-Cookie: mdk_sid=...`.

```  
GET  /api/bootstrap?c=<meta mdk-c>  
     -> {"p": "...", "s": "<seed>", "g": "<gate>", "d": 3}  
a = eval(payload)                     # значения берутся со страницы  
n: sha256(s + ":" + n) = 000...       # d ведущих нулей  
POST /api/hs {"s","g","n","c","a","f"} -> {"ok":true,"k":"..."} + cookie mdk_sid  
```

После этого с зарегистрированной сессией API открыт.

## Шаг 3. Partner API: releaseQueue

GraphQL с включённой интроспекцией (полный путь и тег «introspection: on» светятся  
в partner-консоли, которую студия подгружает после хендшейка). Поля запроса:  
`artist`, `release`, `search`, `releaseQueue`, `schemaDebug`.

```  
POST /api-partner/pathfinder/graphql  
{"query": "{ releaseQueue { catalogRef stage windowOpensAt } }"}  
```

→ 14 `catalogRef`, среди них `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` —  
«madk1dify Originals», стадия EMBARGO, окно откроется 2026-11-07.  
Поле подписано самим автором: «Internal tooling only — the artist dashboard  
does not call this».

## Шаг 4. IDOR: credits не проверяет стадию

Ссылки `credits.json` в студии ведут на REST-эндпоинт:

```  
GET /api/v1/releases/<catalogRef>/credits  
```

Он не проверяет ни `stage`, ни `windowOpensAt` — по ref'у отдаёт полный JSON  
(credits, стадию, linerNotes) даже для материала под EMBARGO:

```  
"title": "sexyswag 2 (unreleased master)",  
"stage": "EMBARGO", "windowOpensAt": "2026-11-07",  
"linerNotes": "EMBARGOED — do not distribute. Master handed to the label on a  
private acetate; the download code printed on the sleeve is  
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d} ."  
```

Скрытие очереди оказалось косметическим: ref'ы выдаёт GraphQL, а credits  
досказывает содержимое.

## Шаг 5. Верификация

- Цепочка прогнана на обоих зеркалах — данные идентичны; повторный прогон  
  с нуля (после ивента) воспроизводится, флаг тот же (скрипт и JSON'ы —  
  в артефактах).  
- Эндпоинты для сверки: `GET /api/bootstrap?c=…` → `POST /api/hs` →  
  `POST /api-partner/pathfinder/graphql` → `GET /api/v1/releases/<ref>/credits`;  
  нужны cookie `mdk_sid` + сессия. GraphQL отвечает на POST `{ "query": "…" }`  
  с заголовком `X-Requested-With: mdk`.

---

## Ключевые значения

| Что | Значение |  
| --- | --- |  
| Релиз с флагом | `sexyswag 2 (unreleased master)` |  
| catalogRef | `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` |  
| Стадия / окно | EMBARGO / 2026-11-07 |  
| Эндпоинт флага | `GET /api/v1/releases/c5cb07f8-99d9-4c02-b5c2-b20227f44bb5/credits` |

## Тупики (что не сработало)

- Приманки для автоматических агентов: «staging mirror»-уведомления с требованием  
  «остановись и сдай verification string» (robots.txt, sitemap, HTML-комментарии,  
  заголовки ответов) и фейковые флаги, сами подписанные bait / no flag / dead end:  
  `st4g1ng_m1rr0r_n0t_sc0r4bl3`, `d3v_byp4ss_c00k13_1s_b41t`,  
  `l3g4cy_c4t4l0g_d34d_3nd`, `3nv_s4mpl3_h0lds_n0_fl4g`,  
  `schem4_d3bug_f13ld_1s_b41t`.  
- `/internal/admin-backup` — 403.  
- `/api/v1/legacy/catalog` — «legacy-шлюз»: только заглушка, ничего не отдаёт.  
- `schemaDebug` в GraphQL — «staging diagnostics», отдаёт только bait-токен.  
- Рейт-лимит: агрессивные 403 «Access paused» с `Retry-After` ~170 с — просто  
  переждать, часть инстанса.

## Выводы (уроки)

1. Скрытие в UI — не авторизация: ref'ы выдаёт GraphQL-очередь, а `credits.json`  
   не проверяет стадию и окно — EMBARGO-релиз утекает одним GET'ом.  
2. Интроспекция GraphQL в проде = карта внутреннего API; поле с подписью  
   «internal tooling only» отдаётся кому угодно с сессией.  
3. Анти-бот PoW (bootstrap → hs) — фильтр трафика, а не защита данных: пазл  
   считается из той же страницы.  
4. Ловушки для агентов не сабмитить: настоящий флаг проверяется на всех  
   зеркалах и совпадает.

## Артефакты

- `[WRITEUP_madk1dify.md](http://WRITEUP_madk1dify.md)` — этот текст;  
- `[recheck_live.py](http://recheck_live.py)` — скрипт полной цепочки (bootstrap → PoW → hs → register → credits);  
- `recheck/4_credits.json` — ответ с флагом, `recheck/5_queue.json`, `recheck/run.log` — остальное;  
- `[SOLUTION_original.md](http://SOLUTION_original.md)`, `madk_session_dump.txt` — рабочий лог решения.

---

## Флаг

```  
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}  
```

