# The Deterministic Fog

> **Category:** Crypto (LWE + LCG) · **Event:** KubSTU CTF 2026 Autumn
> Detailed writeup by team mpei_larpers ([CTFtime](https://ctftime.org/writeup/41123))

## 📌 Task

`output.json` contains the matrices `A`, `R`, the vectors `b`, `ciphertext`, the parameters and the calibration. LWE parameters: a 40-element secret, 200 public equations, `q=257`, noise in the range `[-100,100]`. The LCG has a 48-bit state. Recover the flag.

**Files:** [generate.py](../../../assets/Crypto/The%20Deterministic%20Fog/generate.py), [solution_fog.py](../../../assets/Crypto/The%20Deterministic%20Fog/solution_fog.py), [SECRETS.txt](../../../assets/Crypto/The%20Deterministic%20Fog/SECRETS.txt), [screenshot](../../../assets/Crypto/The%20Deterministic%20Fog/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20234600.png)

## 🏁 Solution

### The gist
Outwardly it is honest LWE (`n=40, m=200, q=257`, a noisy system). In reality you do not need to solve LWE: the noise is **deterministic**. Its source is a public **truncated LCG**

```
x_{i+1} = (mult · x_i + inc) mod 2^48      (mult, inc, mod_bits — в output.json)
```

with a secret 48-bit seed `x_0`. The device publishes a short **calibration trace** `calibration` — the top 8 bits of the first 24 states (`x_i >> 40`). From this trace the seed is recovered **with a lattice** (the classic truncated-LCG reconstruction, FHKLLS).

### Why it can't be taken head-on
- **The noise bound `bound = 100 > q/4 = 64`.** The noise cannot be "rounded away", so this is **not** ordinary small-noise LWE — a generic BDD attack on LWE does not work, you must reproduce the exact noise stream.
- **The seed is 48-bit** → brute force `2⁴⁸` is dead.
- **The calibration hides the low 40 bits** of each output (only the top 8 are shown) → brute-forcing the low bits `2⁴⁰` is also dead. Only the lattice remains.
- Therefore the only path to the flag goes through the lattice; it cannot be bypassed.

### Breakdown
**Step 1. Recover the seed with a lattice.** The state is linear in `x_0`: `x_i = α_i·x_0 + β_i (mod M)`, and `x_0 = (calib[0]·2⁴⁰) + l_0`, where `l_0` are the hidden 40 bits. From `x_i = (calib[i]·2⁴⁰) + l_i`, `0 ≤ l_i < 2⁴⁰`, we build a lattice over the unknowns `(l_0, …)` and look for a short vector (LLL). 24 samples are more than enough; we verify the output by running the LCG forward and comparing the top bits.

**Step 2. Reproduce the noise stream.** From `x_0` we run the LCG: the calibration takes states `x_0…x_{23}`, the working noise stream continues from `x_{24}` (centered: `e = x mod 201 − 100`). The first `m=200` values went into `b`, the next `len(flag)·8` into the ciphertext.

**Step 3. Strip the LWE (now a linear system).** Knowing the noise `e`, the public samples give `A·s = b − e (mod q)` — an ordinary linear system over `F₂₅₇`, solved by Gaussian elimination (`m=200 ≫ n=40`, the solution is unique).

**Step 4. Decrypt.** For each row of the ciphertext `val = (c_j − e_{m+j} − ⟨R_j, s⟩) mod q`; the bit is `0` if `val` is closer to `0`, otherwise `1` (encoding `bit·⌊q/2⌋`). Assemble the bits into the flag.

---

### Detailed community writeup (mpei_larpers)

**The gist:** the LWE noise is produced by a deterministic 48-bit LCG. The calibration reveals the top 8 bits of the first 24 states. We recover the seed with a lattice, replay the noise stream and strip the noise off the LWE system.

#### 1. Source data
`output.json` holds the matrices `A`, `R`, the vectors `b`, `ciphertext`, the parameters and the calibration. LWE parameters: a 40-element secret, 200 public equations, `q=257`, noise in `[-100,100]`. The LCG has a 48-bit state.

Public equations:

```text
b[i] = dot(A[i], secret) + noise[i] mod q
```

Noise generator:

```text
x[i+1] = (mult * x[i] + inc) mod 2^48
noise[i] = x[i] mod 201 - 100
```

`mult` and `inc` are known. Only `x[0]` needs to be recovered.

#### 2. Recovering the LCG initial state
The calibration value is `y[i]=x[i]>>40`. Let `B=2^40`, `M=2^48`. Then:

```text
x[i] = y[i] * B + z[i]
0 <= z[i] < B
```

`z[i]` are the unknown low 40 bits. Unrolling the recursion:

```text
x[i] = A[i] * x[0] + C[i] mod M
```

Coefficients:

```text
A[0] = 1                 C[0] = 0
A[i+1] = A[i] * mult mod M
C[i+1] = C[i] * mult + inc mod M
```

Substituting `x[0]=y[0]*B+z[0]`, for each calibration value we get:

```text
A[i] * z[0] + D[i] = k[i] * M + u[i]
0 <= u[i] < B
```

The residues `u[i]` are smaller than `B`, so we represent the system as a lattice and look for a close vector via LLL and the Babai CVP. Verifying the candidate with a full LCG run gives:

```text
seed = 194990846919092
```

##### Recovering the seed
Install the dependencies:

```bash
python3 -m pip install fpylll cysignals
```

The script reads the calibration from the archive, builds the lattice and accepts a candidate only if all values match:

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

The full trace check discards false nearest vectors.

#### 3. Recreating the noise stream
First we make 24 transitions up to `x[24]`. Then we generate the noise for the 200 rows of `b`, then one value per bit of `ciphertext`. The order must match the task's code.

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

Now the whole noise stream is known.

#### 4. Finding the LWE secret modulo 257
We subtract the first 200 noise values from `b`. A system of linear equations remains:

```text
A * secret = b - noise mod 257
```

We solve it by Gaussian elimination over the field `F_257`. The matrix rank is 40, so the secret is uniquely determined.

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

The `assert` checks the secret against all 200 equations.

#### 5. Stripping the encryption and assembling the flag
Each `ciphertext` value encodes one bit of plaintext. For a bit `m`, a row `R` and noise `e`, the encryption computes:

```text
c = dot(R, secret) + e + m*(q//2) mod q
```

We subtract the known `dot(R, secret)` and the noise `e` from `c`. A remainder of `0` means bit 0, `128` means bit 1. Bytes are assembled MSB first.

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

Result:

```text
KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}
```

#### Result verification
1. The seed reproduces all 24 `calibration` values.
2. The secret satisfies the 200 LWE equations.
3. Each cleaned bit equals `0` or `128`.
4. The bytes form an ASCII flag of the form `KubSTU{...}`.

**Cause of the vulnerability:** the noise is deterministic, and the calibration partially reveals the LCG state.

**Flag:** `KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}`
