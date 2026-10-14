# What do you know about Perelman

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

You are given three files:
- `cascade.py` — code for a "discrete Ricci flow" on the moduli space of elliptic curves over `F_p`. It fixes `p = 4003`, `N = 30`, `η = 1`.
- `curve.png` — a 4003×4003 scatter plot of the points of the final curve `E_N`, corrupted with noise, two **decoy curves** and white "holes".
- `encrypted.txt` — the `iv`, `ct` of the AES-CBC-encrypted flag **and the explicitly stated key-derivation scheme** (scrypt with parameters).

**Files:** [gen.py](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/gen.py), [solve.py](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/solve.py), [gen.log](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/gen.log)

## 🏁 Solution

### Observations
The docstring in `cascade.py` piles on mathematical terminology about Ricci flow / Perelman / surgery — this is **window dressing**. By the code, `ricci_step` is just a pair of polynomial updates modulo `p`, linked by a shared "curvature" `K = 4a³ + 27b²` (the discriminant). The only secret usable as a key is `(a₀, b₀)`; the cascade `(a₀,b₀) → (a_N,b_N)` is deterministic.

### Step 1 — extract the points from the PNG
Each point `E_N: y² = x³ + a·x + b` over `F_p` is a darkened 3×3 marker. The marker center = a pixel with all 8 dark neighbors (3×3 erosion).

```python
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
img = np.array(Image.open("curve.png"))
centers = binary_erosion(img < 128, structure=np.ones((3, 3)))
ys, xs = np.where(centers)
points = list(zip(xs.tolist(), ys.tolist()))
```

### Step 2 — recover `(a_N, b_N)` from the points (RANSAC)
From two points `(a, b)` is solved uniquely:

```
a = ((y₁² - y₂²) - (x₁³ - x₂³)) · (x₁ - x₂)⁻¹  (mod p)
b = y₁² - x₁³ - a·x₁                              (mod p)
```

We try many random pairs and take the curve with the most inliers. The **decoy curves** are drawn sparsely (~35 % of points), so the real `E_N` has noticeably more inliers (3562 in the reference against ~1400 for the decoys) and RANSAC confidently picks it. Noise (~2500 points) and 55 "holes" reduce the inlier fraction, so more pairs are needed (several thousand trials).

### Step 3 — forward-search for preimages
The cascade is not separable (the update of `a` depends on `b` and vice versa), so it cannot be solved per coordinate — pairs have to be enumerated. There are `p² = 16 032 009` pairs, each with `N = 30` iterations; in numpy this takes ~30 s:

```python
a = np.arange(p, dtype=np.int64)[:, None].repeat(p, axis=1)
b = np.arange(p, dtype=np.int64)[None, :].repeat(p, axis=0)
for _ in range(N):
    Kv = (4 * ((a*a) % p) * a + 27 * ((b*b) % p)) % p
    a, b = (a - 12*((a*a) % p)*Kv) % p, (b - 54*b*Kv) % p
cand = list(zip(*np.where((a == aN) & (b == bN))))   # ~10-30 прообразов
```

### Step 4 — decrypt (slow KDF)
The key comes from a **slow memory-hard KDF**, the scheme is published in `encrypted.txt`:

```
key = scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
             salt=b'perelman/ricci/v2', n=65536, r=8, p=1, dklen=32)
```

scrypt is applied **only to a handful of preimages** (20 in the reference) — ~0.2 s each, a few seconds in total:

```python
for a0, b0 in cand:
    key = hashlib.scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
                         salt=SALT, n=65536, r=8, p=1, maxmem=256*1024*1024, dklen=32)
    try:
        pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
        if pt.startswith(b"KubSTU{"): print(pt.decode()); break
    except ValueError: pass
```

**Flag:** `KubSTU{45_a_m4773r_0f_f4c7_h3_b3c4m3_7he_f1r57_p3rs0n_to_s01v3_0n3_0f_th3_m1ll3nn1um_pr1z3_pr0bl3m5}`
