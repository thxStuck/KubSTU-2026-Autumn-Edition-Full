# Shiffted

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

`cipher.txt` में एक ही पंक्ति है: `RbiZAB{j43z4y_d0bsk_i3_wy0bk}`

फ़्लैग को पुनः प्राप्त करें।

**फ़ाइलें:** [gen.py](../../../assets/Crypto/Shiffted/gen.py), [solve.py](../../../assets/Crypto/Shiffted/solve.py)

## 🏁 समाधान

### विचार
यह सीज़र सायफर (शिफ्ट) है: हर अक्षर वर्णमाला में एक निश्चित संख्या में स्थान आगे खिसका दिया गया है। अंक, ब्रेसेस और अंडरस्कोर अछूते रहते हैं।

संकेत तुरंत दिख जाता है: फ़्लैग `KubSTU{` से शुरू होते हैं, जबकि सायफरटेक्स्ट `RbiZAB{` से शुरू होता है। यानी `R→K`, `b→u`, … — शिफ्ट हर जगह समान है। `R`(17) → `K`(10): 7 स्थान पीछे की शिफ्ट।

### समाधान
हर अक्षर को 7 स्थान पीछे खिसकाएँ। या बस सभी 26 शिफ्ट आज़माएँ और वह लें जो `KubSTU{` देता है:

```python
def caesar(t, s):
    r = ""
    for c in t:
        if c.isupper(): r += chr((ord(c)-65+s)%26+65)
        elif c.islower(): r += chr((ord(c)-97+s)%26+97)
        else: r += c
    return r

enc = open("cipher.txt").read().strip()
for s in range(26):
    g = caesar(enc, -s)
    if g.startswith("KubSTU{"):
        print(g); break
```

**फ़्लैग:** `KubSTU{c43s4r_w0uld_b3_pr0ud}`
