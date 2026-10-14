# Shiffted

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

`cipher.txt` holds a single line: `RbiZAB{j43z4y_d0bsk_i3_wy0bk}`

Recover the flag.

**Files:** [gen.py](../../../assets/Crypto/Shiffted/gen.py), [solve.py](../../../assets/Crypto/Shiffted/solve.py)

## 🏁 Solution

### Idea
This is a Caesar cipher (shift): every letter is moved a fixed number of positions through the alphabet. Digits, braces and underscores are left untouched.

The hint is visible right away: flags start with `KubSTU{`, while the ciphertext starts with `RbiZAB{`. So `R→K`, `b→u`, … — the shift is the same everywhere. `R`(17) → `K`(10): a shift of 7 backwards.

### Solution
Shift every letter 7 positions back. Or simply try all 26 shifts and take the one that yields `KubSTU{`:

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

**Flag:** `KubSTU{c43s4r_w0uld_b3_pr0ud}`
