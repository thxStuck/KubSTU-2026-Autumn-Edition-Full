# default

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

`output.txt` contains two large numbers — the RSA modulus `n` and the ciphertext `c`. The public exponent `e` is not given. Recover the plaintext.

**Files:** [solve.py](../../../assets/Crypto/default/solve.py)

## 🏁 Solution

### Observations
- Two large numbers + the name "Default" → this is RSA without padding.
- `e` is not given → most likely it is small (otherwise why hide it).
- Classic small-exponent candidates: `3, 5, 7, 11, 13, 17`.

### Vulnerability
A small-exponent attack on a single ciphertext (a special case of Håstad's attack without padding).

If the message `m` is short enough, then `m^e < n`, and the modular exponentiation effectively does not wrap around:

```
c = m^e mod n = m^e   (because m^e < n)
```

So to recover `m` it is enough to take an ordinary integer `e`-th root of `c`.

Dimension check: the flag is ≈ 480 bits, `n` = 4096 bits → `m^e < n` for `e ∈ {3, 5, 7}`.

### Solution
Iterate over small `e`, for each try an exact integer root and check the flag format:

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
