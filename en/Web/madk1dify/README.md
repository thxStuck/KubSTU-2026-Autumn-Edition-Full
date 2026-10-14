# madk1dify

> **Category:** Web · **Event:** KubSTU CTF 2026 Autumn
> Community (user) writeup by team **mpei_larpers** · Source: https://ctftime.org/writeup/41130 (CTFtime)

## 📌 Task

The flag is hidden in an artist's unreleased material — let's see who resists the temptation.

Statement: "Listen, I really like madk1d, and his album is just incredible. I'm looking forward to sexyswag 2".

Two mirrors are given:

- http://141.133.198.7:8080
- http://159.194.249.251:8080

**What is given.** A clone of the artist madk1d's Spotify:

- a public catalog of releases and playlists;
- an artist workspace `/studio` (opens to any user after registration);
- a partner API: GraphQL `/api-partner/pathfinder/graphql` + REST `/api/v1/...`.

In the studio there is a "Release queue" table: 14 items of unreleased material, titles hidden ("Scheduled — details withheld"), with the note "Titles and references are served by the partner API, not by this page". The flag is the "download code" of the unreleased album sexyswag 2.

## 🏁 Solution

### Step 1. Recon and entering the studio

- `robots.txt` lists the interesting things itself: `/api/`, `/studio`, `/internal/`, `/.env.example`; in the page footer there is a hidden `admin backup` link → `/internal/admin-backup` (403).
- Registration: `POST /register` (username/password) → session cookie → `/studio`.
- The studio serves a catalog of 5 releases (each with a `catalogRef` and a `credits.json` link) and a "Release queue" of 14 unreleased items: the details are withheld, but it is stated that the titles and references are served by the partner API.

### Step 2. Anti-bot ticket (bootstrap → PoW → hs)

All `/api/*` require an `mdk_sid` ticket, which the handshake issues:

- the page carries `meta mdk-c`, random CSS variables in `:root` and random `data-*` attributes;
- `GET /api/bootstrap?c=<mdk-c>` → a JIT puzzle `p`, a seed `s`, difficulty `d=3`;
- `a = new Function(p)()` — the puzzle simply reads variables/attributes off the page;
- `n`: `sha256(s + ":" + n)` starts with `d` zeros;
- `POST /api/hs {s,g,n,c,a,f}` → `{ok,k}` + `Set-Cookie: mdk_sid=...`.

```
GET  /api/bootstrap?c=<meta mdk-c>
     -> {"p": "...", "s": "<seed>", "g": "<gate>", "d": 3}
a = eval(payload)                     # значения берутся со страницы
n: sha256(s + ":" + n) = 000...       # d ведущих нулей
POST /api/hs {"s","g","n","c","a","f"} -> {"ok":true,"k":"..."} + cookie mdk_sid
```

After this, with a registered session the API is open.

### Step 3. Partner API: releaseQueue

GraphQL with introspection enabled (the full path and the tag "introspection: on" show up in the partner console that the studio loads after the handshake). Query fields: `artist`, `release`, `search`, `releaseQueue`, `schemaDebug`.

```
POST /api-partner/pathfinder/graphql
{"query": "{ releaseQueue { catalogRef stage windowOpensAt } }"}
```

→ 14 `catalogRef`, among them `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` — "madk1dify Originals", stage EMBARGO, window opens 2026-11-07. The field is annotated by the author himself: "Internal tooling only — the artist dashboard does not call this".

### Step 4. IDOR: credits does not check the stage

The `credits.json` links in the studio point to a REST endpoint:

```
GET /api/v1/releases/<catalogRef>/credits
```

It checks neither `stage` nor `windowOpensAt` — by ref it serves the full JSON (credits, stage, linerNotes) even for material under EMBARGO:

```
"title": "sexyswag 2 (unreleased master)",
"stage": "EMBARGO", "windowOpensAt": "2026-11-07",
"linerNotes": "EMBARGOED — do not distribute. Master handed to the label on a
private acetate; the download code printed on the sleeve is
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d} ."
```

Hiding the queue turned out to be cosmetic: the refs are served by GraphQL, and credits tells the rest.

### Step 5. Verification

- The chain was run on both mirrors — the data is identical; a fresh run from scratch (after the event) reproduces, the flag is the same (the script and JSONs are in the artifacts).
- Endpoints to cross-check: `GET /api/bootstrap?c=…` → `POST /api/hs` → `POST /api-partner/pathfinder/graphql` → `GET /api/v1/releases/<ref>/credits`; the `mdk_sid` cookie + a session are required. GraphQL answers a POST `{ "query": "…" }` with the header `X-Requested-With: mdk`.

### Key values

| What | Value |
| --- | --- |
| Release with the flag | `sexyswag 2 (unreleased master)` |
| catalogRef | `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` |
| Stage / window | EMBARGO / 2026-11-07 |
| Flag endpoint | `GET /api/v1/releases/c5cb07f8-99d9-4c02-b5c2-b20227f44bb5/credits` |

### Dead ends (what did not work)

- Traps for automated agents: "staging mirror" notices demanding to "stop and submit a verification string" (robots.txt, sitemap, HTML comments, response headers) and fake flags, self-labeled bait / no flag / dead end: `st4g1ng_m1rr0r_n0t_sc0r4bl3`, `d3v_byp4ss_c00k13_1s_b41t`, `l3g4cy_c4t4l0g_d34d_3nd`, `3nv_s4mpl3_h0lds_n0_fl4g`, `schem4_d3bug_f13ld_1s_b41t`.
- `/internal/admin-backup` — 403.
- `/api/v1/legacy/catalog` — a "legacy gateway": just a stub, serves nothing.
- `schemaDebug` in GraphQL — "staging diagnostics", serves only a bait token.
- Rate limit: aggressive 403 "Access paused" with `Retry-After` ~170 s — just wait it out, it is part of the instance.

### Conclusions (lessons)

1. Hiding in the UI is not authorization: the refs are served by the GraphQL queue, and `credits.json` does not check the stage and window — the EMBARGO release leaks with a single GET.
2. GraphQL introspection in prod = a map of the internal API; a field annotated "internal tooling only" is served to anyone with a session.
3. The anti-bot PoW (bootstrap → hs) is a traffic filter, not data protection: the puzzle is computed from the same page.
4. Do not submit agent traps: the real flag is verified on all mirrors and matches.

### Artifacts

- `WRITEUP_madk1dify.md` — this text;
- `recheck_live.py` — the full-chain script (bootstrap → PoW → hs → register → credits);
- `recheck/4_credits.json` — the response with the flag, `recheck/5_queue.json`, `recheck/run.log` — the rest;
- `SOLUTION_original.md`, `madk_session_dump.txt` — the working solution log.

### Flag

```
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}
```

**Flag:** `KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}`
