# AES Is Secure, Right

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

एक इंटर्न ने AES-128 को एक घरेलू सायफर (`intern_cipher.py`) में लपेट दिया और उसका आउटपुट `output.txt` में छोड़ दिया: सायफरटेक्स्ट `ct` और एक संकेत जो PIN का पहला अंक बता देता है। AES कुंजी एक 4-अंकीय PIN से व्युत्पन्न होती है। फ़्लैग को पुनः प्राप्त करें।

**फ़ाइलें:** [generate.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/generate.py), [solve.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/solve.py), [SECRETS.txt](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/SECRETS.txt)

## 🏁 समाधान

### सार
प्रिमिटिव स्वयं ईमानदार है — AES-128। कमज़ोरी उसके चारों ओर की हर चीज़ में है: कुंजी एक **4-अंकीय PIN** (`sha256(pin)[:16]`) से व्युत्पन्न होती है, और `output.txt` का संकेत पहला अंक तक बता देता है। कुंजी-स्थान घटकर 1000 विकल्पों तक सिमट जाता है — AES तोड़ने की ज़रूरत नहीं, बस PIN के अनुसार ब्रूट-फोर्स किया जाता है।

### विश्लेषण
`intern_cipher.py` एन्क्रिप्ट करने से पहले दो गैर-मानक काम करता है:

1. **स्वयं की पैडिंग** `prepare()`: डेटा को 16 के गुणज तक भरता है, लेकिन भराव-बाइट के रूप में **ब्लॉकों की संख्या** का उपयोग होता है, पैडिंग की लंबाई का नहीं (PKCS#7 नहीं)। इसका मतलब `Crypto.Util.Padding.unpad()` उपयुक्त नहीं — उल्टा ऑपरेशन हम स्वयं लिखते हैं।
2. **ब्लॉक क्रमपरिवर्तन**: `shift = sum(PIN के अंक) % ब्लॉकों_की_संख्या` से चक्रीय शिफ्ट, फिर सूची को उल्टा किया जाता है।

एन्क्रिप्शन: `plaintext → prepare → ब्लॉक → shift → reverse → AES-ECB`।

समाधान — `2000..2999` के हर PIN के लिए सब कुछ उल्टा करें:

```
ciphertext → AES-ECB decrypt → reverse → उल्टा shift → जोड़ें → unpad
```

जो एन्क्रिप्ट किया गया है वह नंगा फ़्लैग नहीं, बल्कि प्रमाणपत्र-निरसन की एक छोटी सूचना है (फ़्लैग अंदर, अंतिम पंक्ति में) — 9 ब्लॉक। 9 ब्लॉकों पर `shift` वास्तव में अलग-अलग मान लेता है, इसलिए क्रमपरिवर्तन को ईमानदारी से उलटना पड़ता है, दो में से एक परिणाम का अनुमान नहीं लगाया जा सकता (जो 2 ब्लॉकों पर संभव होता)।

### समाधान

```python
from hashlib import sha256
from Crypto.Cipher import AES

def unprepare(d, bs=16):
    tb = len(d)//bs; pb = tb & 0xff; pl = 0
    for b in reversed(d):
        if b != pb: break
        pl += 1
    return None if (pl == 0 or pl > bs) else d[:-pl]

def decrypt(ct, pin):
    c = AES.new(sha256(pin.encode()).digest()[:16], AES.MODE_ECB)
    bl = [c.decrypt(ct[i:i+16]) for i in range(0, len(ct), 16)]
    bl.reverse()
    sh = sum(int(x) for x in pin) % len(bl)
    if sh: bl = bl[-sh:] + bl[:-sh]
    return unprepare(b"".join(bl))

# первая цифра PIN известна из подсказки -> 1000 кандидатов
for rest in range(1000):
    pin = f"2{rest:03d}"
    pt = decrypt(ct, pin)
    if pt and b"KubSTU{" in pt:
        print(pt.decode()); break
```

**फ़्लैग:** `KubSTU{c3rt1f1c4t3_r3v0k3d}`
