# Do you like reading

> **श्रेणी:** Crypto · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

`reading.txt` एक विशाल टेक्स्ट फ़ाइल है। फ़्लैग उसमें बाइट-क्लस्टर के रूप में छिपा है जो सामान्य `[a-z\n]` टेक्स्ट के बीच से अलग दिखते हैं — हर असली क्लस्टर फ़्लैग का एक हिस्सा है जो अपने स्वयं के Caesar-शिफ्ट से एन्क्रिप्ट किया गया है, लेकिन अधिकांश क्लस्टर फ़र्ज़ी (fakes) हैं। फ़्लैग को पुनः प्राप्त करें।

**फ़ाइलें:** [gen.py](../../../assets/Crypto/Do%20you%20like%20reading/gen.py), [solve.py](../../../assets/Crypto/Do%20you%20like%20reading/solve.py), [gen.log](../../../assets/Crypto/Do%20you%20like%20reading/gen.log)

## 🏁 समाधान

### अवलोकन
- फ़ाइल नोटपैड / `less` के लिए बहुत बड़ी है।
- `tr -d 'a-z\n' < reading.txt | xxd | less` `[a-z\n]` के बाहर के बाइट दिखाता है — अपरकेस, अंक, विराम-चिह्न, control-बाइट।
- विसंगतियाँ बहुत हैं (~90 क्लस्टर), लंबाई अलग-अलग (7 से 20 बाइट तक)।
- इनमें से अधिकांश **फ़र्ज़ी** हैं। फ़्लैग के असली हिस्से केवल 10 हैं।

### विचार
हर असली क्लस्टर फ़्लैग का एक हिस्सा है, जो प्रति-बाइट अपने Caesar-शिफ्ट से एन्क्रिप्ट किया गया है। फ़र्ज़ी इस तरह बनाए गए हैं कि **कोई भी** शिफ्ट फ़्लैग के वर्ण-परास में आउटपुट नहीं देता — यह भोले "सभी क्लस्टर आज़माओ" तरीके को तोड़ देता है।

फ़ाइल में असली हिस्सों का क्रम = फ़्लैग में क्रम।

### समाधान
तीन बातें समझनी हैं:
1. फ़ाइल बहुत बड़ी है → स्ट्रीम प्रोसेसिंग चाहिए (mmap आदर्श है)।
2. क्लस्टर बहुत हैं (फ़र्ज़ी असली से कई गुना ज़्यादा) → एक anchor चाहिए: पहला हिस्सा `KubSTU{` से शुरू होता है, आख़िरी `}` पर समाप्त होता है।
3. बीच के हिस्सों के लिए — संकीर्ण charset `[a-z0-9_]` पर फ़िल्टर; अस्पष्टता की स्थिति में हम अधिकतम अंडरस्कोर वाली शिफ्ट चुनते हैं (असली फ़्लैग में वे बार-बार आते हैं, यादृच्छिक शिफ्ट में दुर्लभ होते हैं)।

```python
import mmap, re

CORE  = set(b"abcdefghijklmnopqrstuvwxyz0123456789_")
CLOSE = CORE | {ord("}")}
HEAD, TAIL = b"KubSTU{", b"}"

def dec(blob, s): return bytes((b - s) % 256 for b in blob)

# 1. Поиск кластеров: mmap + regex по всему файлу.
#    Ядро само подгрузит нужные страницы, ничего не держим в RAM целиком.
clusters = []
with open("reading.txt", "rb") as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        for match in re.finditer(rb"[^a-z\n\r ]+", m):
            clusters.append((match.start(), match.group()))

# 2. HEAD: первый кластер, декодящийся во что-то с префиксом KubSTU{
head_i, head_dec = None, None
for i, (_, blob) in enumerate(clusters):
    for s in range(256):
        d = dec(blob, s)
        if d.startswith(HEAD):
            head_i, head_dec = i, d; break
    if head_i is not None: break

# 3. TAIL: последний кластер, декодящийся во что-то с суффиксом }
tail_i, tail_dec = None, None
for i in range(len(clusters) - 1, -1, -1):
    _, blob = clusters[i]
    for s in range(256):
        d = dec(blob, s)
        if d.endswith(TAIL) and all(c in CLOSE for c in d):
            tail_i, tail_dec = i, d; break
    if tail_i is not None: break

# 4. MIDDLE: между head и tail оставляем только кластеры с валидным
# CORE-декодом. Фейки естественно отфильтруются (нет валидного сдвига).
# Среди валидных сдвигов выбираем с максимумом подчёркиваний.
middle = []
for i in range(head_i + 1, tail_i):
    _, blob = clusters[i]
    best = None
    for s in range(1, 256):
        d = dec(blob, s)
        if all(c in CORE for c in d):
            score = d.count(b"_")
            if best is None or score > best[0]:
                best = (score, d)
    if best: middle.append(best[1])

print((head_dec + b"".join(middle) + tail_dec).decode())
```

**फ़्लैग:** `KubSTU{r34d1n6_r3411y_d0e5_m4k3_my_br4in_w0rk_be77er_but_th1s_t45k_1sn7_0ne_0f_7h0s3_c4535}`
