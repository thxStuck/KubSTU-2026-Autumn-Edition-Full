# default

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

`output.txt` में दो बड़ी संख्याएँ हैं — RSA मॉड्यूलस `n` और सायफरटेक्स्ट `c`। पब्लिक एक्सपोनेंट `e` नहीं दिया गया है। प्लेनटेक्स्ट को पुनः प्राप्त करें।

**फ़ाइलें:** [solve.py](../../../assets/Crypto/default/solve.py)

## 🏁 समाधान

### अवलोकन
- दो बड़ी संख्याएँ + नाम "Default" → यह बिना पैडिंग वाला RSA है।
- `e` नहीं दिया गया → सबसे संभव है कि वह छोटा है (वरना छिपाने की क्या ज़रूरत)।
- छोटे एक्सपोनेंट के क्लासिक उम्मीदवार: `3, 5, 7, 11, 13, 17`।

### भेद्यता
एक ही सायफरटेक्स्ट पर small-exponent attack (बिना पैडिंग के Håstad हमले का एक विशेष मामला)।

यदि संदेश `m` पर्याप्त छोटा है, तो `m^e < n`, और मॉड्यूलर घातांक वास्तव में wrap-around नहीं करता:

```
c = m^e mod n = m^e   (क्योंकि m^e < n)
```

अतः `m` को पुनः प्राप्त करने के लिए `c` का साधारण पूर्णांक `e`-वाँ मूल लेना ही पर्याप्त है।

आयाम-जाँच: फ़्लैग ≈ 480 बिट, `n` = 4096 बिट → `e ∈ {3, 5, 7}` के लिए `m^e < n`।

### समाधान
छोटे `e` पर पुनरावृत्ति करें, हर एक के लिए सटीक पूर्णांक मूल आज़माएँ और फ़्लैग फ़ॉर्मेट जाँचें:

```python
from Crypto.Util.number import long_to_bytes
import gmpy2

# from output.txt: n, c
for e in [3, 5, 7, 11, 13, 17, 19, 23]:
    m, exact = gmpy2.iroot(c, e)
    if not exact:
        continue
    try:
        flag = long_to_bytes(int(m)).decode()
    except UnicodeDecodeError:
        continue
    if "KubSTU{" in flag:
        print(f"e = {e}")
        print(flag)
        break
```
