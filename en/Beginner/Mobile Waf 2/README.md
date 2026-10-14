# Mobile Waf 2

> **Category:** Beginner / PPC · **Event:** KubSTU CTF 2026 Autumn
> Author team: mpei_larpers · Source: https://ctftime.org/writeup/41135 (CTFtime community writeup)

## 📌 Task

The service at 193.168.46.146:31832 is the "WAF Gauntlet". It plays 100 rounds: it sends JSON describing a request (method, path, query, headers, body) and expects one string in reply — `allow` or `block`. You must block only requests that carry a real, executable attack (XSS, SQLi, SSTI, SSRF, command injection, XXE/NoSQL/deserialization, HTTP abuses, LFI/path traversal), and let everything else through, including tricky but harmless lookalikes. One mistake and the game is over. You get 3 seconds per round and 150 per connection.

## 🏁 Solution

The service's main weakness is that it explains its own errors. On a wrong answer you get `# wrong at round N: expected block (xss)` and the connection closes — that is, the round's attack class leaks right there in the error text. That is where the dataset collection comes from: the "allow everything" strategy fails on the very first round that contains an attack (and the service tells you which one), while the "block everything" strategy fails on the first harmless one. A round counts as confirmed only once the next one arrives, so the labels are not guesses but exact.

That builds up a corpus: 325 confirmed samples plus around 500 more rounds with an attack type assigned. There is no binary to reverse — the whole task turns into classification.

Next comes a rule-based classifier (waf_filter.py). Each field is expanded into several representations — raw, url-decode up to three times, with SQL comments stripped, %uXXXX, HTML entities, base64 blobs — and run through rule sets per class. Among the more interesting rules: a JWT with `alg:none`, Shellshock, tar with `--checkpoint-action=exec`, `powershell -enc`, ImageMagick with `-write`, Log4Shell, .NET BinaryFormatter and Ruby Marshal blobs, base64-wrapped SSRF targets, CRLF, request smuggling, X-Forwarded-Host, HTTP parameter pollution, path confusion. Just as important is not tripping up on harmless lookalikes: escaped markup inside text, template variables like `{{customer_name}}`, SQL words inside ordinary speech, `file://` in prose, sensitive-looking names in normal URLs.

Offline validation: 0 discrepancies on 497 typed samples and 0 on the 325 confirmed ones. Live run: `python3 solve.py` cleared 100/100 on the first attempt, the service sent `# cleared 100/100` and the flag in JSON:

```
{"flag": "kubstu{w4f_g4untl3t_100_r0unds_e7075354d674}"}
```

**Flag:** `kubstu{w4f_g4untl3t_100_r0unds_e7075354d674}`
