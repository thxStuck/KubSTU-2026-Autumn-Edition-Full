# L. Lawliet - L

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

`params.txt` gives `n = 64`, a list `w` of 64 weights (~84 bits each), and `ciphertexts` — 7 numbers. You must recover the encryption scheme from the data and get the flag back.

**Files:** [gen.py](../../../assets/Crypto/L.%20Lawliet%20-%20L/gen.py), [solve.py](../../../assets/Crypto/L.%20Lawliet%20-%20L/solve.py), [SECRETS.txt](../../../assets/Crypto/L.%20Lawliet%20-%20L/SECRETS.txt), [screenshot](../../../assets/Crypto/L.%20Lawliet%20-%20L/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20212314.png)

## 🏁 Solution

### The gist
The scheme (which has to be reconstructed from the data): the message is padded, split into 64-bit blocks (MSB first), and each block is encrypted with the same public key `w` as

    c = Σ w[i] · bit[i]   (i = 0..63)

This is a **low-density subset-sum (knapsack)**. Its density is `d = n / log2(max w) ≈ 64/84 ≈ 0.76`.

### Why LLL alone is not enough
The theoretical CJLOSS bound — `d < 0.9408` — is asymptotic and assumes a perfect SVP oracle. In practice **plain LLL** reliably solves a knapsack only up to about `d ≈ 0.64` (the Lagarias–Odlyzko bound). At `d ≈ 0.76` LLL finds only "junk" short vectors, and the real `(±1)` vector never surfaces. A stronger reduction is needed — **BKZ**.

### Solution
For each block we build a CJLOSS lattice `(n+1)×(n+1)`:

```
rows i<n:  [ 2·e_i ,  K·w_i ]
row  n  :  [ 1 … 1 ,  K·s   ]
```

(`K` is a large multiplier that forces the sum-coordinate to zero). The short vector `(±1, …, ±1, 0)` = `2·bit_i − 1` → the block's bits.

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

We collect the bits of all 7 blocks, convert them to bytes and strip the zero padding.

**Flag:** `KubSTU{y0u_n33d_70_6e_4_re41_d373ct1ve_7o_5o1v3_7h15}`
