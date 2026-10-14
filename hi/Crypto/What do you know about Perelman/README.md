# What do you know about Perelman

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

आपको तीन फ़ाइलें दी गई हैं:
- `cascade.py` — `F_p` पर एलिप्टिक कर्व्स के मॉड्यूलाई-स्पेस पर एक «असतत Ricci flow» का कोड। यह `p = 4003`, `N = 30`, `η = 1` तय करता है।
- `curve.png` — अंतिम कर्व `E_N` के बिंदुओं का 4003×4003 scatter plot, जो शोर, दो **छलावा कर्व्स** और सफ़ेद «छेदों» से दूषित है।
- `encrypted.txt` — AES-CBC-एन्क्रिप्टेड फ़्लैग का `iv`, `ct` **और स्पष्ट रूप से दी गई कुंजी-व्युत्पन्न योजना** (पैरामीटरों सहित scrypt)।

**फ़ाइलें:** [gen.py](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/gen.py), [solve.py](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/solve.py), [gen.log](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/gen.log)

## 🏁 समाधान

### अवलोकन
`cascade.py` का docstring Ricci flow / Perelman / surgery के बारे में गणितीय शब्दावली से भरा है — यह **दिखावा** है। कोड के अनुसार `ricci_step` बस मॉड्यूलो `p` के दो बहुपद अद्यतन हैं, जो एक साझा «वक्रता» `K = 4a³ + 27b²` (विविक्तकर / discriminant) से जुड़े हैं। कुंजी में उपयोगी एकमात्र सीक्रेट है `(a₀, b₀)`; कैस्केड `(a₀,b₀) → (a_N,b_N)` नियतात्मक (deterministic) है।

### चरण 1 — PNG से बिंदु निकालें
`F_p` पर हर बिंदु `E_N: y² = x³ + a·x + b` एक गहरा 3×3 मार्कर है। मार्कर का केंद्र = वह पिक्सेल जिसके सभी 8 पड़ोसी गहरे हैं (3×3 erosion)।

```python
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
img = np.array(Image.open("curve.png"))
centers = binary_erosion(img < 128, structure=np.ones((3, 3)))
ys, xs = np.where(centers)
points = list(zip(xs.tolist(), ys.tolist()))
```

### चरण 2 — बिंदुओं से `(a_N, b_N)` पुनः प्राप्त करें (RANSAC)
दो बिंदुओं से `(a, b)` अद्वितीय रूप से हल होता है:

```
a = ((y₁² - y₂²) - (x₁³ - x₂³)) · (x₁ - x₂)⁻¹  (mod p)
b = y₁² - x₁³ - a·x₁                              (mod p)
```

हम कई यादृच्छिक जोड़े आज़माते हैं और सबसे अधिक inliers वाली कर्व लेते हैं। **छलावा कर्व्स** विरल रूप से खींची गई हैं (~35 % बिंदु), इसलिए असली `E_N` के inliers काफ़ी अधिक होते हैं (संदर्भ में 3562 बनाम छलावों के ~1400) और RANSAC आत्मविश्वास से उसे चुन लेता है। शोर (~2500 बिंदु) और 55 «छेद» inlier अनुपात घटाते हैं, इसलिए अधिक जोड़े चाहिए (कई हज़ार प्रयास)।

### चरण 3 — पूर्व-प्रतिबिम्बों की forward-search
कैस्केड separable नहीं है (`a` का अद्यतन `b` पर निर्भर करता है और इसके विपरीत), इसलिए निर्देशांकों के अनुसार अलग-अलग हल नहीं किया जा सकता — जोड़ों को गणना करना पड़ता है। कुल जोड़े `p² = 16 032 009`, प्रत्येक पर `N = 30` पुनरावृत्तियाँ; numpy में यह ~30 सेकंड लेता है:

```python
a = np.arange(p, dtype=np.int64)[:, None].repeat(p, axis=1)
b = np.arange(p, dtype=np.int64)[None, :].repeat(p, axis=0)
for _ in range(N):
    Kv = (4 * ((a*a) % p) * a + 27 * ((b*b) % p)) % p
    a, b = (a - 12*((a*a) % p)*Kv) % p, (b - 54*b*Kv) % p
cand = list(zip(*np.where((a == aN) & (b == bN))))   # ~10-30 прообразов
```

### चरण 4 — डिक्रिप्ट करें (धीमा KDF)
कुंजी एक **धीमे memory-hard KDF** से मिलती है, योजना `encrypted.txt` में प्रकाशित है:

```
key = scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
             salt=b'perelman/ricci/v2', n=65536, r=8, p=1, dklen=32)
```

scrypt **केवल मुट्ठी भर पूर्व-प्रतिबिम्बों** पर लागू होता है (संदर्भ में 20) — प्रत्येक ~0.2 से, कुल मिलाकर कुछ सेकंड:

```python
for a0, b0 in cand:
    key = hashlib.scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
                         salt=SALT, n=65536, r=8, p=1, maxmem=256*1024*1024, dklen=32)
    try:
        pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
        if pt.startswith(b"KubSTU{"): print(pt.decode()); break
    except ValueError: pass
```

**फ़्लैग:** `KubSTU{45_a_m4773r_0f_f4c7_h3_b3c4m3_7he_f1r57_p3rs0n_to_s01v3_0n3_0f_th3_m1ll3nn1um_pr1z3_pr0bl3m5}`
