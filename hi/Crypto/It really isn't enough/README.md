# It really isn't enough

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

`challenge.txt` आपको दो RSA पब्लिक कुंजियाँ (A और B), एक RSA-OAEP-एन्क्रिप्टेड कुंजी, और दो AES-GCM सायफरटेक्स्ट देती है। तीन परतें, हर एक के लिए अलग हमला चाहिए, साथ ही कई जाल (decoys)। नाम परत 1 का सीधा संकेत है: साधारण Wiener **it really isn't enough**। असली फ़्लैग पुनः प्राप्त करें।

**फ़ाइलें:** [solve.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/solve.sage), [bd_core.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/bd_core.sage), [source_reference.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/source_reference.py), [gen.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.py), [gen.log](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.log)

## 🏁 समाधान

### कार्य की संरचना
तीन परतें, हर एक के लिए अलग हमला चाहिए, साथ ही चार झूठे रास्ते।

| परत / जाल | तंत्र | क्या होता है |
|---|---|---|
| परत 1 (RSA A) | `d ≈ N^0.26` | Wiener पर्याप्त नहीं → Boneh-Durfee चाहिए |
| जाल: कुंजी B | `d ≈ N^0.24` | Wiener इसे एक सेकंड में तोड़ देता है → `blob` = ताना |
| परत 2a (ct1) | AES-GCM, वैध टैग | फ़र्ज़ी फ़्लैग `k3ep_1o0k1ng` |
| परत 2b (ct2) | AES-GCM, टैग टूटा हुआ | भोला `decrypt_and_verify` विफल हो जाता है |
| जाल: source में `d` | फ़र्ज़ी स्थिरांक | हैश ग़लत कुंजी देता है |

नाम परत 1 का सीधा संकेत है: साधारण Wiener **it really isn't enough**।

### परत 1 — Boneh-Durfee
कुंजी A की प्राइवेट एक्सपोनेंट `d ≈ N^0.26`:
- Wiener केवल `d < N^0.25` पर काम करता है → **नहीं पकड़ता**;
- Boneh-Durfee `d < N^0.292` पर काम करता है → **पकड़ लेता है**।

कुंजी B एक जाल है जिसमें `d ≈ N^0.24`: क्लासिक Wiener इसे तुरंत तोड़ देता है, पर इसके नीचे का `blob` एक ताना-मारती स्ट्रिंग में डिक्रिप्ट होता है। यह उन लोगों को काट देता है जो सहज-प्रवृत्ति से पहले परिचित पैटर्न पर झपट पड़ते हैं (विशेषकर LLM)।

**हमले का सार।** `e·d ≡ 1 (mod φ)` और `φ = N + 1 − (p+q)` से हमें छोटे मूलों वाला एक समीकरण मिलता है:

```
f(x, y) = 1 + x·(A + y) ≡ 0  (mod e),   A = (N+1)/2,  y ≈ -(p+q)/2
```

`|x| ~ N^delta`, `|y| ~ N^0.5`। हम x- और y-shift बहुपदों (Herrmann–May) से एक जाली बनाते हैं, LLL से रिड्यूस करते हैं, दो छोटे वेक्टरों का resultant लेते हैं, मूल खोजते हैं → `d` पुनः प्राप्त करते हैं, फिर `(e, d)` से `N` का गुणनखंड करते हैं।

`enc_key` (RSA-OAEP) और `src_ct` (AES-GCM) डिक्रिप्ट करके हमें `source.py` मिलता है।

### परत 2 — nonce पुनः-प्रयोग + टूटा टैग
`source.py` दिखाता है:
- `key = SHA256(str(d))` — **असली** `d` से। पास ही एक स्थिरांक `d = 0x...` है जिसकी टिप्पणी "private exponent" है — यह **फ़र्ज़ी** है (जाल); उपयोग Boneh-Durfee से प्राप्त `d` का करना है।
- एक ही nonce वाले **दो GCM सायफरटेक्स्ट**।

**ct1** — वैध टैग → फ़र्ज़ी फ़्लैग `k3ep_1o0k1ng` में डिक्रिप्ट होता है। स्लॉपर इसे जमा करता है और "ग़लत" पाता है।

**ct2** — वही nonce, पर टैग जान-बूझकर दूषित। `decrypt_and_verify` एक `ValueError` फेंकेगा। मुख्य अंतर्दृष्टि: **GCM = CTR + GMAC**। केवल अखंडता टूटी है, गोपनीयता नहीं — टैग को दरकिनार कर डिक्रिप्ट किया जा सकता है:

```python
real = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(ct2[:-16])  # без verify
```

→ असली फ़्लैग।

```
sage: cd /path/to/folder        # тут challenge.txt, bd_core.sage, solve.sage
sage: load("solve.sage")
```

पाइपलाइन: Boneh-Durfee → `d` → गुणनखंडन → RSA-OAEP → AES-GCM(source) → nonce/ct पार्स → `SHA256(str(d))` → ct2 पर बिना verify के `decrypt`।

फ़र्ज़ी फ़्लैग (ct1): `KubSTU{7h15_15_n07_7h3_r34l_0n3_k3ep_1o0k1ng}`

**फ़्लैग:** `KubSTU{50met1me5_7h3_m057_c0mp13x_7h1ng5_turn_0ut_70_b3_51mpl3_y0u_ju57_n33d_t0_74k3_4_cl053r_lo0k}`
