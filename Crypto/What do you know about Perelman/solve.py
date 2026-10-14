#!/usr/bin/env python3
"""
Solve for "What do you know about Perelman?"

1. Load curve.png, extract dark 3x3 cluster centres.
2. RANSAC-fit (a_N, b_N): the real E_N is the curve with the most inliers
   (decoys are rendered sparsely, so they rank below it).
3. Forward-search all (a0, b0) in F_p^2 via a numpy-vectorised cascade and
   collect the preimages of (a_N, b_N).
4. For each preimage derive the key with scrypt (parameters from
   encrypted.txt) and AES-decrypt; accept the KubSTU{...} plaintext.

The slow KDF is applied only to the handful of surviving preimages, so the
intended path costs a few scrypt calls; a key-space brute would cost ~16M.
"""
import hashlib, random, re, time
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

p, N, eta = 4003, 30, 1

# --- robustly locate curve.png / encrypted.txt (same folder as script, or cwd) ---
HERE = Path(__file__).resolve().parent
def _find(fname):
    for d in (HERE, HERE.parent / "player", HERE / "player", Path.cwd()):
        if (d / fname).exists():
            return d / fname
    return Path(fname)

# --- 1. извлекаем центры кластеров ---
img = np.array(Image.open(_find("curve.png")))
dark = (img < 128)
centers = binary_erosion(dark, structure=np.ones((3, 3)))
ys, xs = np.where(centers)
points = list(zip(xs.tolist(), ys.tolist()))
print(f"[*] cluster centres: {len(points)}")


# --- 2. RANSAC-фит y^2 = x^3 + a x + b (mod p) ---
def fit_pair(p1, p2):
    x1, y1 = p1; x2, y2 = p2
    if x1 == x2:
        return None
    try:
        inv = pow((x1 - x2) % p, -1, p)
    except ValueError:
        return None
    a = ((y1*y1 - y2*y2 - x1**3 + x2**3) * inv) % p
    b = (y1*y1 - x1**3 - a*x1) % p
    return a, b

pts_arr = np.array(points, dtype=np.int64)
PX = pts_arr[:, 0]; PY = pts_arr[:, 1]
def inliers(a, b):
    return int(np.count_nonzero((PY*PY - PX**3 - a*PX - b) % p == 0))

random.seed(0)
best = (0, 0, 0)
for _ in range(6000):
    p1, p2 = random.sample(points, 2)
    fit = fit_pair(p1, p2)
    if fit is None:
        continue
    a, b = fit
    if (4*a**3 + 27*b**2) % p == 0:
        continue
    m = inliers(a, b)
    if m > best[2]:
        best = (a, b, m)
aN, bN, m = best
print(f"[+] fit: a_N={aN}, b_N={bN}  ({m}/{len(points)} inliers)")

# --- 3. forward-search preimages (numpy) ---
t = time.perf_counter()
a = np.arange(p, dtype=np.int64)[:, None].repeat(p, axis=1)
b = np.arange(p, dtype=np.int64)[None, :].repeat(p, axis=0)
for _ in range(N):
    Kv = (4 * ((a*a) % p) * a + 27 * ((b*b) % p)) % p
    a, b = (a - 12*eta * ((a*a) % p) * Kv) % p, (b - 54*eta * b * Kv) % p
hit = np.where((a == aN) & (b == bN))
cand = list(zip(hit[0].tolist(), hit[1].tolist()))
print(f"[+] forward-search {time.perf_counter()-t:.1f}s, {len(cand)} preimage(s)")

# --- 4. slow KDF only on the survivors ---
txt = open(_find("encrypted.txt")).read()
salt = eval(re.search(r"salt=(b'[^']*')", txt).group(1))
n = int(re.search(r"n=(\d+)", txt).group(1))
r = int(re.search(r"r=(\d+)", txt).group(1))
pp = int(re.search(r"p=(\d+)", txt).group(1))
iv = bytes.fromhex(re.search(r"iv = (\w+)", txt).group(1))
ct = bytes.fromhex(re.search(r"ct = (\w+)", txt).group(1))

for a0, b0 in cand:
    key = hashlib.scrypt(a0.to_bytes(4, "big") + b0.to_bytes(4, "big"),
                         salt=salt, n=n, r=r, p=pp, maxmem=256*1024*1024, dklen=32)
    try:
        pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
    except ValueError:
        continue
    if pt.startswith(b"KubSTU{"):
        print(f"[+] a0={a0}, b0={b0}")
        print("[+] FLAG:", pt.decode())
        break
else:
    print("[-] no candidate decrypted")
