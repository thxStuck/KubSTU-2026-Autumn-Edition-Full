# madk1dify

> **श्रेणी:** Web · **इवेंट:** KubSTU CTF 2026 Autumn
> टीम **mpei_larpers** का सामुदायिक (उपयोगकर्ता) राइटअप · स्रोत: https://ctftime.org/writeup/41130 (CTFtime)

## 📌 कार्य

फ़्लैग किसी कलाकार के अनरिलीज़्ड (अप्रकाशित) मटेरियल में छिपा है — देखते हैं कौन इस लालच के आगे टिकता है।

कथन: «Listen, I really like madk1d, and his album is just incredible. I'm looking forward to sexyswag 2»।

दो मिरर दिए गए हैं:

- http://141.133.198.7:8080
- http://159.194.249.251:8080

**क्या दिया गया है।** कलाकार madk1d के Spotify का एक क्लोन:

- रिलीज़ और प्लेलिस्ट का एक सार्वजनिक कैटलॉग;
- एक आर्टिस्ट-वर्कस्पेस `/studio` (किसी भी उपयोगकर्ता के रजिस्टर करने पर खुलता है);
- एक पार्टनर API: GraphQL `/api-partner/pathfinder/graphql` + REST `/api/v1/...`।

स्टूडियो में एक «Release queue» तालिका है: अनरिलीज़्ड मटेरियल की 14 प्रविष्टियाँ, तायटल छिपे हुए («Scheduled — details withheld»), इस नोट के साथ «Titles and references are served by the partner API, not by this page»। फ़्लैग अनरिलीज़्ड एल्बम sexyswag 2 का «download code» है।

## 🏁 समाधान

### चरण 1. टोह और स्टूडियो में प्रवेश

- `robots.txt` स्वयं दिलचस्प चीज़ें गिना देता है: `/api/`, `/studio`, `/internal/`, `/.env.example`; पेजों के फ़ुटर में एक छिपी `admin backup` लिंक → `/internal/admin-backup` (403)।
- रजिस्ट्रेशन: `POST /register` (username/password) → सेशन कुकी → `/studio`।
- स्टूडियो 5 रिलीज़ का एक कैटलॉग देता है (हर एक के पास एक `catalogRef` और एक `credits.json` लिंक) और 14 अनरिलीज़्ड प्रविष्टियों वाला एक «Release queue»: ब्योरे रोके गए हैं, पर कहा गया है कि तायटल और संदर्भ partner API देता है।

### चरण 2. एंटी-बॉट-टिकट (bootstrap → PoW → hs)

सभी `/api/*` को एक `mdk_sid` टिकट चाहिए, जो हैंडशेक जारी करता है:

- पेज `meta mdk-c`, `:root` में यादृच्छिक CSS-चर और यादृच्छिक `data-*` एट्रिब्यूट लाता है;
- `GET /api/bootstrap?c=<mdk-c>` → एक JIT-पज़ल `p`, एक seed `s`, कठिनाई `d=3`;
- `a = new Function(p)()` — पज़ल बस पेज से चर/एट्रिब्यूट पढ़ता है;
- `n`: `sha256(s + ":" + n)` `d` शून्यों से शुरू होता है;
- `POST /api/hs {s,g,n,c,a,f}` → `{ok,k}` + `Set-Cookie: mdk_sid=...`।

```
GET  /api/bootstrap?c=<meta mdk-c>
     -> {"p": "...", "s": "<seed>", "g": "<gate>", "d": 3}
a = eval(payload)                     # значения берутся со страницы
n: sha256(s + ":" + n) = 000...       # d ведущих нулей
POST /api/hs {"s","g","n","c","a","f"} -> {"ok":true,"k":"..."} + cookie mdk_sid
```

इसके बाद एक रजिस्टर्ड सेशन के साथ API खुल जाता है।

### चरण 3. Partner API: releaseQueue

इंट्रोस्पेक्शन चालू वाला GraphQL (पूरा पथ और टैग «introspection: on» उस partner-कंसोल में दिखते हैं, जिसे स्टूडियो हैंडशेक के बाद लोड करता है)। क्वेरी के फ़ील्ड: `artist`, `release`, `search`, `releaseQueue`, `schemaDebug`।

```
POST /api-partner/pathfinder/graphql
{"query": "{ releaseQueue { catalogRef stage windowOpensAt } }"}
```

→ 14 `catalogRef`, उनमें `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` — «madk1dify Originals», स्टेज EMBARGO, विंडो 2026-11-07 को खुलेगी। फ़ील्ड पर ख़ुद लेखक की टिप्पणी है: «Internal tooling only — the artist dashboard does not call this»।

### चरण 4. IDOR: credits स्टेज नहीं जाँचता

स्टूडियो में `credits.json` लिंक एक REST-एंडपॉइंट की ओर ले जाती हैं:

```
GET /api/v1/releases/<catalogRef>/credits
```

यह न `stage` जाँचता है, न `windowOpensAt` — ref के ज़रिए पूरा JSON (credits, स्टेज, linerNotes) दे देता है, EMBARGO के तहत वाले मटेरियल के लिए भी:

```
"title": "sexyswag 2 (unreleased master)",
"stage": "EMBARGO", "windowOpensAt": "2026-11-07",
"linerNotes": "EMBARGOED — do not distribute. Master handed to the label on a
private acetate; the download code printed on the sleeve is
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d} ."
```

क्यू को छिपाना महज़ दिखावटी निकला: ref GraphQL देता है, और credits बाक़ी सामग्री बता देता है।

### चरण 5. सत्यापन

- शृंखला दोनों मिररों पर चलाई गई — डेटा समान है; शून्य से दोबारा चलाने पर (ईवेंट के बाद) परिणाम दोहराता है, फ़्लैग वही है (स्क्रिप्ट और JSON — आर्टिफ़ैक्ट्स में)।
- सत्यापन के लिए एंडपॉइंट: `GET /api/bootstrap?c=…` → `POST /api/hs` → `POST /api-partner/pathfinder/graphql` → `GET /api/v1/releases/<ref>/credits`; `mdk_sid` कुकी + एक सेशन चाहिए। GraphQL `X-Requested-With: mdk` हेडर के साथ POST `{ "query": "…" }` का उत्तर देता है।

### मुख्य मान

| क्या | मान |
| --- | --- |
| फ़्लैग वाला रिलीज़ | `sexyswag 2 (unreleased master)` |
| catalogRef | `c5cb07f8-99d9-4c02-b5c2-b20227f44bb5` |
| स्टेज / विंडो | EMBARGO / 2026-11-07 |
| फ़्लैग का एंडपॉइंट | `GET /api/v1/releases/c5cb07f8-99d9-4c02-b5c2-b20227f44bb5/credits` |

### गतिरोध (जो काम नहीं आया)

- स्वचालित एजेंटों के लिए जाल: «staging mirror»-सूचनाएँ जो «रुको और एक verification string सबमिट करो» की माँग करती हैं (robots.txt, sitemap, HTML-टिप्पणियाँ, प्रतिक्रिया-हेडर) और फ़र्ज़ी फ़्लैग, जो ख़ुद bait / no flag / dead end के रूप में चिह्नित हैं: `st4g1ng_m1rr0r_n0t_sc0r4bl3`, `d3v_byp4ss_c00k13_1s_b41t`, `l3g4cy_c4t4l0g_d34d_3nd`, `3nv_s4mpl3_h0lds_n0_fl4g`, `schem4_d3bug_f13ld_1s_b41t`।
- `/internal/admin-backup` — 403।
- `/api/v1/legacy/catalog` — एक «legacy-गेटवे»: केवल एक stub, कुछ नहीं देता।
- GraphQL में `schemaDebug` — «staging diagnostics», केवल एक bait-टोकन देता है।
- रेट-लिमिट: आक्रामक 403 «Access paused» `Retry-After` ~170 सेकंड के साथ — बस इंतज़ार कर लो, यह इंस्टेंस का हिस्सा है।

### निष्कर्ष (सबक)

1. UI में छिपाना अधिकरण (authorization) नहीं है: ref GraphQL-क्यू देता है, और `credits.json` स्टेज और विंडो नहीं जाँचता — EMBARGO-रिलीज़ एक GET से लीक हो जाता है।
2. प्रोड में GraphQL इंट्रोस्पेक्शन = आंतरिक API का नक़्शा; «internal tooling only» टिप्पणी वाला फ़ील्ड सेशन वाले किसी को भी मिल जाता है।
3. एंटी-बॉट PoW (bootstrap → hs) एक ट्रैफ़िक-फ़िल्टर है, डेटा-सुरक्षा नहीं: पज़ल उसी पेज से गणना होती है।
4. एजेंट-जाल सबमिट न करें: असली फ़्लैग सभी मिररों पर सत्यापित होता है और मेल खाता है।

### आर्टिफ़ैक्ट्स

- `WRITEUP_madk1dify.md` — यही टेक्स्ट;
- `recheck_live.py` — पूरी शृंखला की स्क्रिप्ट (bootstrap → PoW → hs → register → credits);
- `recheck/4_credits.json` — फ़्लैग वाली प्रतिक्रिया, `recheck/5_queue.json`, `recheck/run.log` — बाक़ी;
- `SOLUTION_original.md`, `madk_session_dump.txt` — समाधान का कार्यशील लॉग।

### फ़्लैग

```
KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}
```

**फ्लैग:** `KubSTU{1ntr0sp3ct_th3n_1d0r_unr3l34s3d}`
