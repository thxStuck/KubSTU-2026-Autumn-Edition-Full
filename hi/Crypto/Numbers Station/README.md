# Numbers Station

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

`codes.txt` में स्पेस से अलग की गई संख्याओं की एक पंक्ति है:
`75 117 98 83 84 85 123 ...`

संदेश को डिकोड करें।

**फ़ाइलें:** [gen.py](../../../assets/Crypto/Numbers%20Station/gen.py), [solve.py](../../../assets/Crypto/Numbers%20Station/solve.py)

## 🏁 समाधान

### विचार
ये दशमलव में वर्णों के ASCII कोड हैं। हर संख्या एक ही अक्षर का कोड है। संकेत: `75` = `K`, `117` = `u`, `98` = `b` → पहले से ही `Kub…` पढ़ा जा सकता है।

### समाधान
हर संख्या को एक वर्ण में बदलें:

```python
codes = open("codes.txt").read().split()
flag = "".join(chr(int(x)) for x in codes)
print(flag)
```

**फ़्लैग:** `KubSTU{d3c1m4l_15_my_l4n6u4g3}`
