# AES Is Secure, Right

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

An intern wrapped AES-128 in a home-grown cipher (`intern_cipher.py`) and left you its output in `output.txt`: the ciphertext `ct` plus a hint that reveals the first digit of the PIN. The AES key is derived from a 4-digit PIN. Recover the flag.

**Files:** [generate.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/generate.py), [solve.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/solve.py), [SECRETS.txt](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/SECRETS.txt)

## 🏁 Solution

### The gist
The primitive itself is honest — AES-128. The weakness is in everything around it: the key is derived from a **4-digit PIN** (`sha256(pin)[:16]`), and the hint in `output.txt` even tells you the first digit. The key space collapses to 1000 variants — there is no need to break AES, you simply brute-force it by PIN.

### Analysis
`intern_cipher.py` does two non-standard things before encrypting:

1. **Custom padding** `prepare()`: pads the data up to a multiple of 16, but the filler byte is the **number of blocks**, not the padding length (not PKCS#7). This means `Crypto.Util.Padding.unpad()` does not apply — we write the inverse operation ourselves.
2. **Block permutation**: a cyclic shift by `shift = sum(digits of PIN) % number_of_blocks`, then the list is reversed.

Encryption: `plaintext → prepare → blocks → shift → reverse → AES-ECB`.

The solution is to reverse all of it for each PIN in `2000..2999`:

```
ciphertext → AES-ECB decrypt → reverse → inverse shift → concatenate → unpad
```

What is encrypted is not the bare flag but a short certificate-revocation note (the flag inside, on the last line) — 9 blocks. Over 9 blocks `shift` really does take different values, so the permutation has to be honestly inverted, not guessed as one of two outcomes (which would be the case with 2 blocks).

### Solution

```python
from hashlib import sha256
from Crypto.Cipher import AES

def unprepare(d, bs=16):
    tb = len(d)//bs; pb = tb & 0xff; pl = 0
    for b in reversed(d):
        if b != pb: break
        pl += 1
    return None if (pl == 0 or pl > bs) else d[:-pl]

def decrypt(ct, pin):
    c = AES.new(sha256(pin.encode()).digest()[:16], AES.MODE_ECB)
    bl = [c.decrypt(ct[i:i+16]) for i in range(0, len(ct), 16)]
    bl.reverse()
    sh = sum(int(x) for x in pin) % len(bl)
    if sh: bl = bl[-sh:] + bl[:-sh]
    return unprepare(b"".join(bl))

# первая цифра PIN известна из подсказки -> 1000 кандидатов
for rest in range(1000):
    pin = f"2{rest:03d}"
    pt = decrypt(ct, pin)
    if pt and b"KubSTU{" in pt:
        print(pt.decode()); break
```

**Flag:** `KubSTU{c3rt1f1c4t3_r3v0k3d}`
