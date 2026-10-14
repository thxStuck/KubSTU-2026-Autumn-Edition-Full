# The Deterministic Fog

> **श्रेणी:** Crypto (LWE + LCG) · **इवेंट:** KubSTU CTF 2026 Autumn
> टीम mpei_larpers का विस्तृत राइटअप ([CTFtime](https://ctftime.org/writeup/41123))

## 📌 कार्य

`output.json` में मैट्रिक्स `A`, `R`, वेक्टर `b`, `ciphertext`, पैरामीटर और कैलिब्रेशन हैं। LWE पैरामीटर: 40-तत्व का सीक्रेट, 200 सार्वजनिक समीकरण, `q=257`, `[-100,100]` परास में शोर। LCG का 48-बिट स्टेट है। फ़्लैग पुनः प्राप्त करें।

**फ़ाइलें:** [generate.py](../../../assets/Crypto/The%20Deterministic%20Fog/generate.py), [solution_fog.py](../../../assets/Crypto/The%20Deterministic%20Fog/solution_fog.py), [SECRETS.txt](../../../assets/Crypto/The%20Deterministic%20Fog/SECRETS.txt), [स्क्रीनशॉट](../../../assets/Crypto/The%20Deterministic%20Fog/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20234600.png)

## 🏁 समाधान

### सार
बाहर से — ईमानदार LWE (`n=40, m=200, q=257`, शोरयुक्त सिस्टम)। वास्तव में LWE हल करने की ज़रूरत नहीं: शोर **नियतात्मक (deterministic)** है। इसका स्रोत एक सार्वजनिक **ट्रंकेटेड LCG** है

```
x_{i+1} = (mult · x_i + inc) mod 2^48      (mult, inc, mod_bits — в output.json)
```

जिसका सीक्रेट 48-बिट सीड `x_0` है। डिवाइस एक छोटा **कैलिब्रेशन ट्रेस** `calibration` प्रकाशित करता है — पहले 24 स्टेट के ऊपरी 8 बिट (`x_i >> 40`)। इस ट्रेस से सीड को **जाली (lattice) द्वारा** पुनः प्राप्त किया जाता है (ट्रंकेटेड-LCG की क्लासिक पुनर्रचना, FHKLLS)।

### «सीधे-सीधे» क्यों नहीं निकलता
- **शोर की सीमा `bound = 100 > q/4 = 64`।** शोर को «राउंड» नहीं किया जा सकता, अर्थात् यह सामान्य small-noise LWE **नहीं** है — LWE पर सामान्य BDD हमला काम नहीं करता, सटीक शोर-धारा को फिर से उत्पन्न करना पड़ता है।
- **सीड 48-बिट** → `2⁴⁸` का ब्रूट-फोर्स असंभव।
- **कैलिब्रेशन में हर आउटपुट के निचले 40 बिट छिपे हैं** (केवल ऊपरी 8 दिखाए गए) → निचले बिट `2⁴⁰` का ब्रूट-फोर्स भी असंभव। केवल जाली शेष रहती है।
- इसलिए फ़्लैग तक एकमात्र रास्ता जाली से होकर जाता है; इसे टाला नहीं जा सकता।

### विश्लेषण
**चरण 1. जाली से सीड पुनः प्राप्त करें।** स्टेट `x_0` में रैखिक है: `x_i = α_i·x_0 + β_i (mod M)`, और `x_0 = (calib[0]·2⁴⁰) + l_0`, जहाँ `l_0` छिपे हुए 40 बिट हैं। `x_i = (calib[i]·2⁴⁰) + l_i`, `0 ≤ l_i < 2⁴⁰` से हम अज्ञातों `(l_0, …)` पर जाली बनाते हैं और एक छोटा वेक्टर (LLL) खोजते हैं। 24 नमूने गुंजाइश के साथ पर्याप्त हैं; आउटपुट की जाँच LCG को आगे चलाकर और ऊपरी बिट मिलाकर करते हैं।

**चरण 2. शोर-धारा फिर से उत्पन्न करें।** `x_0` से LCG चलाते हैं: कैलिब्रेशन स्टेट `x_0…x_{23}` लेता है, कार्यशील शोर-धारा `x_{24}` से जारी रहती है (केंद्रित: `e = x mod 201 − 100`)। पहले `m=200` मान `b` में गए, अगले `len(flag)·8` — सायफरटेक्स्ट में।

**चरण 3. LWE हटाएँ (अब यह एक रैखिक सिस्टम है)।** शोर `e` जानने पर, सार्वजनिक नमूने देते हैं `A·s = b − e (mod q)` — `F₂₅₇` पर एक सामान्य रैखिक सिस्टम, जिसे गाउस विधि से हल किया जाता है (`m=200 ≫ n=40`, हल अद्वितीय)।

**चरण 4. डिक्रिप्ट करें।** सायफरटेक्स्ट की हर पंक्ति के लिए `val = (c_j − e_{m+j} − ⟨R_j, s⟩) mod q`; बिट `0` यदि `val` `0` के निकट है, अन्यथा `1` (कोडिंग `bit·⌊q/2⌋`)। बिट को फ़्लैग में जोड़ते हैं।

---

### विस्तृत टीम राइटअप (mpei_larpers)

**सार:** LWE शोर एक नियतात्मक 48-बिट LCG देता है। कैलिब्रेशन पहले 24 स्टेट के ऊपरी 8 बिट उजागर करता है। seed को जाली से पुनः प्राप्त करते हैं, शोर-धारा दोहराते हैं और LWE सिस्टम से शोर हटाते हैं।

#### 1. स्रोत डेटा
`output.json` में मैट्रिक्स `A`, `R`, वेक्टर `b`, `ciphertext`, पैरामीटर और कैलिब्रेशन हैं। LWE पैरामीटर: 40-तत्व का सीक्रेट, 200 सार्वजनिक समीकरण, `q=257`, `[-100,100]` में शोर। LCG का 48-बिट स्टेट है।

सार्वजनिक समीकरण:

```text
b[i] = dot(A[i], secret) + noise[i] mod q
```

शोर जनरेटर:

```text
x[i+1] = (mult * x[i] + inc) mod 2^48
noise[i] = x[i] mod 201 - 100
```

`mult` और `inc` ज्ञात हैं। केवल `x[0]` पुनः प्राप्त करना है।

#### 2. LCG का प्रारंभिक स्टेट पुनः प्राप्त करते हैं
कैलिब्रेशन मान है `y[i]=x[i]>>40`। मान लें `B=2^40`, `M=2^48`। तब:

```text
x[i] = y[i] * B + z[i]
0 <= z[i] < B
```

`z[i]` अज्ञात निचले 40 बिट हैं। रिकर्शन खोलें:

```text
x[i] = A[i] * x[0] + C[i] mod M
```

गुणांक:

```text
A[0] = 1                 C[0] = 0
A[i+1] = A[i] * mult mod M
C[i+1] = C[i] * mult + inc mod M
```

`x[0]=y[0]*B+z[0]` प्रतिस्थापित करने पर, हर कैलिब्रेशन मान के लिए मिलता है:

```text
A[i] * z[0] + D[i] = k[i] * M + u[i]
0 <= u[i] < B
```

अवशेष `u[i]` `B` से छोटे हैं, इसलिए सिस्टम को जाली के रूप में निरूपित करते हैं और LLL व Babai CVP के माध्यम से एक निकट वेक्टर खोजते हैं। उम्मीदवार को पूरे LCG रन से जाँचने पर मिलता है:

```text
seed = 194990846919092
```

##### seed की पुनर्प्राप्ति
निर्भरताएँ स्थापित करें:

```bash
python3 -m pip install fpylll cysignals
```

स्क्रिप्ट आर्काइव से कैलिब्रेशन पढ़ती है, जाली बनाती है और उम्मीदवार को तभी स्वीकारती है जब सभी मान मिलते हैं:

```python
import json
from zipfile import ZipFile

from fpylll import CVP, IntegerMatrix, LLL

ARCHIVE = "The Deterministic Fog.zip"
MEMBER = "The Deterministic Fog/output.json"

with ZipFile(ARCHIVE) as archive:
    data = json.loads(archive.read(MEMBER))

sampler = data["sampler"]
mult = sampler["mult"]
inc = sampler["inc"]
M = 1 << sampler["mod_bits"]
B = 1 << sampler["hide"]
ys = data["calibration"]
n = len(ys)

# Коэффициенты в x[i] = A[i]*x[0] + C[i] (mod M).
A, C = [], []
aa, cc = 1, 0
for _ in ys:
    A.append(aa)
    C.append(cc)
    aa = aa * mult % M
    cc = (cc * mult + inc) % M

# После подстановки x[0] = y[0]*B + z[0] получаем
# общую неизвестную z[0] и ограниченные остатки для каждой строки.
D = [(A[i] * ys[0] * B + C[i] - ys[i] * B) % M
     for i in range(n)]

# Базис порождает координаты A[i]*z + k[i]*M и последнюю координату z.
basis = IntegerMatrix(n + 1, n + 1)
for i in range(n):
    basis[i, i] = M
for i in range(n):
    basis[n, i] = A[i]
basis[n, n] = 1

LLL.reduction(basis)
target = [-value for value in D] + [0]
nearest = CVP.babai(basis, target)
low_part = int(nearest[-1])

def calibration(seed):
    x = seed
    trace = []
    for _ in ys:
        trace.append(x >> sampler["hide"])
        x = (mult * x + inc) % M
    return trace

seed = None
for candidate_low in (low_part, -low_part):
    if 0 <= candidate_low < B:
        candidate = ys[0] * B + candidate_low
        if calibration(candidate) == ys:
            seed = candidate
            break

if seed is None:
    raise ValueError("Кандидат решётки не совпал с калибровочной трассой")

print("Recovered seed:", seed)
```

पूरी ट्रेस की जाँच ग़लत निकटतम वेक्टरों को हटा देती है।

#### 3. शोर-धारा फिर से बनाते हैं
पहले `x[24]` तक 24 संक्रमण करते हैं। फिर `b` की 200 पंक्तियों के लिए शोर उत्पन्न करते हैं, फिर `ciphertext` के हर बिट के लिए एक-एक मान। क्रम कार्य के कोड से मेल खाना चाहिए।

```python
mask = M - 1
x = seed
for _ in range(sampler["calib"]):
    x = (mult * x + inc) & mask

count = len(data["b"]) + len(data["ciphertext"])
noise = []
for _ in range(count):
    noise.append(
        x % (2 * data["params"]["bound"] + 1)
        - data["params"]["bound"]
    )
    x = (mult * x + inc) & mask
```

अब पूरी शोर-धारा ज्ञात है।

#### 4. मॉड्यूलो 257 पर LWE सीक्रेट खोजते हैं
`b` से शोर के पहले 200 मान घटाते हैं। एक रैखिक समीकरण-प्रणाली शेष रहती है:

```text
A * secret = b - noise mod 257
```

इसे क्षेत्र `F_257` पर गाउस विधि से हल करते हैं। मैट्रिक्स का रैंक 40 है, इसलिए सीक्रेट अद्वितीय रूप से निर्धारित होता है।

```python
q = data["params"]["q"]
rows = data["A"]
rhs = [
    (value - error) % q
    for value, error in zip(data["b"], noise)
]
n_secret = data["params"]["n"]
matrix = [
    [value % q for value in row] + [target]
    for row, target in zip(rows, rhs)
]

pivots = []
r = 0
for col in range(n_secret):
    pivot = next(
        (i for i in range(r, len(matrix)) if matrix[i][col] % q),
        None,
    )
    if pivot is None:
        continue

    matrix[r], matrix[pivot] = matrix[pivot], matrix[r]
    inverse = pow(matrix[r][col], -1, q)
    matrix[r] = [(value * inverse) % q for value in matrix[r]]

    for i in range(len(matrix)):
        if i != r and matrix[i][col]:
            factor = matrix[i][col]
            matrix[i] = [
                (a - factor * b) % q
                for a, b in zip(matrix[i], matrix[r])
            ]

    pivots.append(col)
    r += 1
    if r == n_secret:
        break

if r != n_secret:
    raise ValueError(f"Неожиданный ранг матрицы: {r}")

secret = [0] * n_secret
for row_index, col in enumerate(pivots):
    secret[col] = matrix[row_index][-1]

# Проверяем найденный секрет во всех 200 публичных уравнениях.
assert all(
    sum(a * b for a, b in zip(row, secret)) % q == value
    for row, value in zip(rows, rhs)
)
```

`assert` सीक्रेट को सभी 200 समीकरणों पर जाँचता है।

#### 5. एन्क्रिप्शन हटाकर फ़्लैग बनाते हैं
हर `ciphertext` मान प्लेनटेक्स्ट का एक बिट कोड करता है। बिट `m`, पंक्ति `R` और शोर `e` के लिए एन्क्रिप्शन गणना करता है:

```text
c = dot(R, secret) + e + m*(q//2) mod q
```

`c` से ज्ञात `dot(R, secret)` और शोर `e` घटाते हैं। अवशेष `0` का अर्थ बिट 0, `128` का अर्थ बिट 1। बाइट को ऊपरी बिट से निचले बिट की ओर जोड़ते हैं।

```python
bit_errors = noise[len(data["b"]):]
bits = []

for value, row, error in zip(
    data["ciphertext"], data["R"], bit_errors
):
    phase = (
        value
        - sum(a * b for a, b in zip(row, secret))
        - error
    ) % q
    bits.append(1 if q // 4 < phase < 3 * q // 4 else 0)

plaintext = bytes(
    sum(bits[offset + j] << (7 - j) for j in range(8))
    for offset in range(0, len(bits), 8)
)
flag = plaintext.decode("ascii")

assert flag.startswith("KubSTU{") and flag.endswith("}")
print(flag)
```

परिणाम:

```text
KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}
```

#### परिणाम की जाँच
1. Seed सभी 24 `calibration` मानों को पुनः उत्पन्न करता है।
2. सीक्रेट 200 LWE समीकरणों को संतुष्ट करता है।
3. हर साफ़ किया गया बिट `0` या `128` के बराबर है।
4. बाइट `KubSTU{...}` प्रारूप का ASCII फ़्लैग बनाते हैं।

**भेद्यता का कारण:** शोर नियतात्मक है, और कैलिब्रेशन LCG स्टेट को आंशिक रूप से उजागर करता है।

**फ़्लैग:** `KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}`
