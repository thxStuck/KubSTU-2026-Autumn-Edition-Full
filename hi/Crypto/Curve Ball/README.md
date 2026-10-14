# Curve Ball

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

दो कसकर जुड़ी एलिप्टिक कर्व्स की एक श्रृंखला (साथ में एक छलावा कर्व C3) और एक AES-एन्क्रिप्टेड फ़्लैग। हर परत एक अलग, गैर-तुच्छ हमला है, और श्रृंखला केवल सख़्ती से क्रम में ही हल होती है। फ़्लैग को पुनः प्राप्त करें।

**फ़ाइलें:** [gen.py](../../../assets/Crypto/Curve%20Ball/gen.py), [solve.sage](../../../assets/Crypto/Curve%20Ball/solve.sage), [gen.log](../../../assets/Crypto/Curve%20Ball/gen.log), [स्क्रीनशॉट](../../../assets/Crypto/Curve%20Ball/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-02%20022018.png)

## 🏁 समाधान

### सिंहावलोकन
दो एलिप्टिक कर्व्स की श्रृंखला, कसकर जुड़ी हुई। हर परत एक अलग, गैर-तुच्छ हमला है। पूरी तरह केवल क्रमिक रूप से हल होती है।

```
C1 (general Weierstrass)
   -> привести к короткой форме
   -> посчитать #E1, обнаружить #E1 = p1  (АНОМАЛЬНАЯ)
   -> Smart's attack -> k1
k1 -> SHA256 -> ключ AES -> расшифровать параметры C2
C2 (supersingular, embedding degree 2)
   -> MOV attack (distortion map + Weil pairing)
   -> smooth DLP в GF(p2^2)* (Pohlig-Hellman) -> k2
AES(key = SHA256("k1:k2")) -> флаг
```

छलावा: C3 एक सामान्य कर्व है जिस पर खिलाड़ी हमला करने की कोशिश कर सकता है, पर वह फ़्लैग तक नहीं ले जाती (उस पर कोई भी हमला उपयोगी परिणाम नहीं देता)।

---

### परत 0 — पहचान
C1 **पूर्ण Weierstrass रूप** में दी गई है: `y² + a1·xy + a3·y = x³ + a2·x² + a4·x + a6`। खिलाड़ी इसे संक्षिप्त रूप `y² = x³ + Ax + B` में लाता है (मानक b/c-इनवेरिएंट) और क्रम गणना करता है (Sage में `E.order()`)।

मुख्य अवलोकन: **#E1 = p1**। यह एक अनॉमलस (anomalous) कर्व है, और इसके लिए ECDLP को Smart's attack के द्वारा रैखिक समय में हल किया जाता है। क्रम गणना किए बिना, कर्व एक सामान्य अनलिफ़्टेबल 256-बिट ECDLP जैसा दिखता है — यही परत 0 का जाल है।

---

### परत 1 — Smart's attack (SSSA)
अनॉमलस कर्व (`#E = p`) के लिए p-एडिक क्षेत्र `Q_p` में लिफ़्ट और औपचारिक लघुगणक के माध्यम से योज्य समूह `F_p` में एक समाकृतिकता (isomorphism) मौजूद होती है।

```python
def smart_attack(G, P, p):
    E = G.curve()
    Eqp = EllipticCurve(Qp(p, 2), [ZZ(t) for t in E.a_invariants()])
    Gl = Eqp.lift_x(ZZ(G.xy()[0]))
    if (ZZ(Gl.xy()[1]) % p) != (ZZ(G.xy()[1]) % p): Gl = -Gl
    Pl = Eqp.lift_x(ZZ(P.xy()[0]))
    if (ZZ(Pl.xy()[1]) % p) != (ZZ(P.xy()[1]) % p): Pl = -Pl
    pG, pP = p*Gl, p*Pl                    # push into the formal group
    tG = -(pG.xy()[0]) / (pG.xy()[1])      # p-adic elliptic log
    tP = -(pP.xy()[0]) / (pP.xy()[1])
    return Integer((tP / tG) % p)
```

परिणाम — `k1`, C1 का गुप्त अदिश (scalar)।

---

### परतों का संबंध
C2 के पैरामीटर AES-CBC से एन्क्रिप्टेड हैं, कुंजी `k1` से व्युत्पन्न होती है:

```python
key1 = SHA256(b"C1->C2:" + str(k1).encode())
plaintext = JSON {p2, a, b, G2, P2}
```

C1 पर Smart's के बिना C2 के पैरामीटर अनुपलब्ध हैं — k1 (258 बिट) का अनुमान लगाना असंभव है। इससे श्रृंखला सख़्ती से क्रमिक बन जाती है।

---

### परत 2 — MOV attack
डिक्रिप्शन के बाद C2 supersingular निकलती है: `p2 ≡ 3 (mod 4)` पर `y² = x³ + x`, `#E2 = p2 + 1`, embedding degree 2। क्रम **smooth** है (जान-बूझकर निर्मित), इसलिए स्थानांतरण के बाद DLP हल हो जाती है।

MOV, Weil pairing के माध्यम से ECDLP को `GF(p2²)*` में स्थानांतरित करता है। सहायक बिंदु की यादृच्छिक खोज के बजाय एक **distortion map** `φ(x,y) = (−x, i·y)` (जहाँ `i² = −1`) का उपयोग होता है, जो एक अविकृत (non-degenerate) pairing की गारंटी देता है:

```python
F2e = GF(p2**2, 'i', modulus=x**2 + 1); i = F2e.gen()
E2e = EllipticCurve(F2e, [a, b])
def distort(P):
    x, y = P.xy(); return E2e(-x, i*y)
alpha = G2e.weil_pairing(distort(G2e), n)
beta  = P2e.weil_pairing(distort(G2e), n)

# beta = alpha^k2 в GF(p2^2)* ; порядок гладкий -> Pohlig-Hellman
ord_alpha = alpha.multiplicative_order()
k2_partial = discrete_log(beta, alpha, ord=ord_alpha, operation='*')

# Weil pairing может потерять часть 2-компоненты порядка, так что
# discrete_log даёт k2 только по модулю ord_alpha. Недостающий кофактор
# n/ord_alpha крошечный (делитель 2-части) — добираем полный k2
# коротким перебором (максимум ~16 итераций):
cof = n // ord_alpha
for j in range(cof):
    cand = k2_partial + j * ord_alpha
    if cand * G2 == P2:
        k2 = cand; break
```

परिणाम — `k2`।

**सूक्ष्मता (स्थिरता के लिए महत्वपूर्ण):** supersingular के लिए Weil pairing `e(G, φ(G))` का क्रम `ord_alpha < n` हो सकता है, जिससे दो की घात का एक हिस्सा खो जाता है (`p2+1` में `2^k` समाहित है)। इसलिए `discrete_log` केवल `k2 mod ord_alpha` पुनः प्राप्त करता है, और दुर्भाग्यपूर्ण `k2` पर पूरा सीक्रेट सीधे नहीं मिलता। एक छोटा कोफ़ैक्टर-सर्च छूटे हुए बिट पूरे कर देता है। इस चरण के बिना सॉल्वर कुछ यादृच्छिक कुंजियों पर विफल हो जाता है।

---

### परत 3 — फ़्लैग

```python
key = SHA256(f"{k1}:{k2}")
flag = AES-CBC-decrypt(iv, ct, key)
```

**फ़्लैग:** `KubSTU{45_f0r_311ip71c_curv3_g30m37ry_4nd_cryp70gr4phy_1n_g3ner41_1_63l13v3_y0u_w3re_46l3_70_501ve_i7}`
