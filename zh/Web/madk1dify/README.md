# madk1dify

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn
> 由战队 **mpei_larpers** 撰写的社区（用户）writeup · 来源：https://ctftime.org/writeup/41130 (CTFtime)

## 📌 题目

flag 藏在一位艺人未发行（unreleased）的素材里——看看谁能抵得住诱惑。

题面：«Listen, I really like madk1d, and his album is just incredible. I'm looking forward to sexyswag 2»。

给了两个镜像：

- http://141.133.198.7:8080
- http://159.194.249.251:8080

**给了什么。** 艺人 madk1d 的 Spotify 克隆：

- 一个公开的发行与歌单目录；
- 一个艺人工作区 `/studio`（任何用户注册后即可打开）；
- 一个合作方 API：GraphQL `/api-partner/pathfinder/graphql` + REST `/api/v1/...`。

工作区里有一个「Release queue」表：14 条未发行素材，标题被隐藏（「Scheduled — details withheld」），附注「Titles and references are served by the partner API, not by this page」。flag 就是未发行专辑 sexyswag 2 的「download code」。

## 🏁 解题思路

### 第 1 步. 侦察并进入工作区

- `robots.txt` 自己就列出了有意思的东西：`/api/`、`/studio`、`/internal/`、`/.env.example`；页面页脚里有一个隐藏的 `admin backup` 链接 → `/internal/admin-backup`（403）。
- 注册：`POST /register`（username/password）→ 会话 cookie → `/studio`。
- 工作区给出一个含 5 个发行的目录（每个都有一个 `catalogRef` 和一个 `credits.json` 链接），以及一个含 14 条未发行项的「Release queue」：细节被扣住，但说明标题和引用由 partner API 提供。

### 第 2 步. 反机器人票据（bootstrap → PoW → hs）

所有 `/api/*` 都需要一个 `mdk_sid` 票据，由握手（handshake）签发：

- 页面带有 `meta mdk-c`、`:root` 中的随机 CSS 变量以及随机的 `data-*` 属性；
- `GET /api/bootstrap?c=<mdk-c>` → 一个 JIT 谜题 `p`、一个 seed `s`、难度 `d=3`；
- `a = new Function(p)()` —— 谜题只是从页面上读取变量/属性；
- `n`：`sha256(s + ":" + n)` 以 `d` 个零开头；
- `POST /api/hs {s,g,n,c,a,f}` → `{ok,k}` + `Set-Cookie: mdk_sid=...`。

```
GET  /api/bootstrap?c=<meta mdk-c>
     -> {"p": "...", "s": "<seed>", "g": "<gate>", "d": 3}
a = eval(payload)                     # значения берутся со страницы
n: sha256(s + ":" + n) = 000...       # d ведущих нулей
POST /api/hs {"s","g","n","c","a","f"} -> {"ok":true,"k":"..."} + cookie mdk_sid
```

此后用一个已注册的会话，API 就开放了。

### 第 3 步. Partner API：releaseQueue

启用了内省（introspection）的 GraphQL（完整路径和标记「introspection: on」显示在工作区握手后加载的 partner 控制台里）。查询字段：`artist`、`release`、`search`、`releaseQueue`、`schemaDebug`。

```
POST /api-partner/pathfinder/graphql
{"query": "{ releaseQueue { catalogRef stage windowOpensAt } }"}
```

→ 14 个 `catalogRef`，其中有 `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` —— 「madk1dify Originals」，阶段 EMBARGO，窗口将于 2026-11-07 开放。该字段有作者本人的注释：「Internal tooling only — the artist dashboard does not call this」。

### 第 4 步. IDOR：credits 不校验阶段

工作区里的 `credits.json` 链接指向一个 REST 接口：

```
GET /api/v1/releases/<catalogRef>/credits
```

它既不校验 `stage` 也不校验 `windowOpensAt` —— 凭 ref 就返回完整 JSON（credits、阶段、linerNotes），即便是处于 EMBARGO 下的素材也一样：

```
"title": "sexyswag 2 (unreleased master)",
"stage": "EMBARGO", "windowOpensAt": "2026-11-07",
"linerNotes": "EMBARGOED — do not distribute. Master handed to the label on a
private acetate; the download code printed on the sleeve is
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d} ."
```

把队列藏起来原来只是表面功夫：ref 由 GraphQL 给出，而 credits 把剩下的内容补齐。

### 第 5 步. 验证

- 该链条在两个镜像上都跑过——数据一致；从零重跑（赛后）可复现，flag 相同（脚本和 JSON 在 artifacts 里）。
- 用于对照的接口：`GET /api/bootstrap?c=…` → `POST /api/hs` → `POST /api-partner/pathfinder/graphql` → `GET /api/v1/releases/<ref>/credits`；需要 `mdk_sid` cookie + 一个会话。GraphQL 对带 `X-Requested-With: mdk` 头的 POST `{ "query": "…" }` 作出响应。

### 关键值

| 内容 | 值 |
| --- | --- |
| 含 flag 的发行 | `sexyswag 2 (unreleased master)` |
| catalogRef | `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` |
| 阶段 / 窗口 | EMBARGO / 2026-11-07 |
| flag 接口 | `GET /api/v1/releases/c5cb07f8-99d9-4c02-b5c2-b20227f44bb5/credits` |

### 死胡同（哪些没用）

- 针对自动化 agent 的陷阱：「staging mirror」通知，要求「停下来并提交一个 verification string」（robots.txt、sitemap、HTML 注释、响应头），以及自我标注为 bait / no flag / dead end 的假 flag：`st4g1ng_m1rr0r_n0t_sc0r4bl3`、`d3v_byp4ss_c00k13_1s_b41t`、`l3g4cy_c4t4l0g_d34d_3nd`、`3nv_s4mpl3_h0lds_n0_fl4g`、`schem4_d3bug_f13ld_1s_b41t`。
- `/internal/admin-backup` —— 403。
- `/api/v1/legacy/catalog` —— 一个「legacy 网关」：只是个桩（stub），什么都不给。
- GraphQL 里的 `schemaDebug` —— 「staging diagnostics」，只给一个 bait 令牌。
- 速率限制：带 `Retry-After` ~170 秒的激进 403「Access paused」——干等就行，它是实例的一部分。

### 结论（教训）

1. 在 UI 里隐藏不等于授权：ref 由 GraphQL 队列给出，而 `credits.json` 不校验阶段和窗口——EMBARGO 发行用一个 GET 就泄露了。
2. 生产环境开着 GraphQL 内省 = 一张内部 API 的地图；标注「internal tooling only」的字段照样给任何持有会话的人。
3. 反机器人 PoW（bootstrap → hs）是流量过滤器，不是数据保护：谜题是从同一个页面算出来的。
4. 不要提交 agent 陷阱：真正的 flag 在所有镜像上都能验证且一致。

### Artifacts

- `WRITEUP_madk1dify.md` —— 本文；
- `recheck_live.py` —— 全链条脚本（bootstrap → PoW → hs → register → credits）；
- `recheck/4_credits.json` —— 含 flag 的响应，`recheck/5_queue.json`、`recheck/run.log` —— 其余；
- `SOLUTION_original.md`、`madk_session_dump.txt` —— 解题的工作日志。

### Flag

```
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}
```

**Flag:** `KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}`
