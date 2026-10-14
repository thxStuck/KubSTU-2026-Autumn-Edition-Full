# L. Lawliet - L

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

`params.txt` में `n = 64`, 64 भारों (~84 बिट प्रत्येक) की सूची `w`, और `ciphertexts` — 7 संख्याएँ दी गई हैं। आपको डेटा से एन्क्रिप्शन स्कीम को फिर से बनाकर फ़्लैग प्राप्त करना है।

**फ़ाइलें:** [gen.py](../../../assets/Crypto/L.%20Lawliet%20-%20L/gen.py), [solve.py](../../../assets/Crypto/L.%20Lawliet%20-%20L/solve.py), [SECRETS.txt](../../../assets/Crypto/L.%20Lawliet%20-%20L/SECRETS.txt), [स्क्रीनशॉट](../../../assets/Crypto/L.%20Lawliet%20-%20L/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20212314.png)

## 🏁 समाधान

### सार
स्कीम (जिसे डेटा से फिर से बनाना है): संदेश को पैड किया जाता है, 64-बिट ब्लॉकों में बाँटा जाता है (MSB first), और हर ब्लॉक को उसी सार्वजनिक कुंजी `w` से इस प्रकार एन्क्रिप्ट किया जाता है:

    c = Σ w[i] · bit[i]   (i = 0..63)

यह एक **low-density subset-sum (knapsack / नैपसैक)** है। इसका घनत्व `d = n / log2(max w) ≈ 64/84 ≈ 0.76` है।

### अकेला LLL क्यों पर्याप्त नहीं
सैद्धांतिक CJLOSS सीमा — `d < 0.9408` — एसिम्प्टोटिक है और एक आदर्श SVP ओरेकल मानती है। व्यवहार में **सादा LLL** नैपसैक को विश्वसनीय रूप से केवल लगभग `d ≈ 0.64` तक हल करता है (Lagarias–Odlyzko सीमा)। `d ≈ 0.76` पर LLL केवल "कूड़ा" छोटे वेक्टर पाता है, और असली `(±1)` वेक्टर कभी सामने नहीं आता। एक मज़बूत रिडक्शन चाहिए — **BKZ**।

### समाधान
हर ब्लॉक के लिए हम एक CJLOSS जाली (lattice) `(n+1)×(n+1)` बनाते हैं:

```
rows i<n:  [ 2·e_i ,  K·w_i ]
row  n  :  [ 1 … 1 ,  K·s   ]
```

(`K` एक बड़ा गुणक है जो योग-निर्देशांक को शून्य पर ले जाता है)। छोटा वेक्टर `(±1, …, ±1, 0)` = `2·bit_i − 1` → ब्लॉक के बिट।

```python
from fpylll import IntegerMatrix, LLL, BKZ
K = 1 << 64
def rec(s):
    B = IntegerMatrix(n+1, n+1)
    for i in range(n): B[i,i]=2; B[i,n]=w[i]*K
    for j in range(n): B[n,j]=1
    B[n,n]=s*K
    LLL.reduction(B)
    BKZ.reduction(B, BKZ.Param(block_size=30))   # LLL alone НЕ хватает
    for r in range(n+1):
        row=[B[r,j] for j in range(n+1)]
        if row[n]==0 and all(abs(x)==1 for x in row[:n]):
            for sg in (1,-1):
                bits=[(sg*row[j]+1)//2 for j in range(n)]
                if all(b in (0,1) for b in bits) and sum(w[i]*bits[i] for i in range(n))==s:
                    return bits
```

हम सभी 7 ब्लॉकों के बिट इकट्ठा करते हैं, उन्हें बाइट में बदलते हैं और शून्य पैडिंग हटाते हैं।

**फ़्लैग:** `KubSTU{y0u_n33d_70_6e_4_re41_d373ct1ve_7o_5o1v3_7h15}`
