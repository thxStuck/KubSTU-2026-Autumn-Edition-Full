#!/usr/bin/env python3
"""
Generator for "What do you know about Perelman?" (KubSTU CTF, Crypto, hard).

1. Pick (a0, b0) such that E_0 and E_N are both non-singular.
2. Run the Ricci cascade forward N steps → (a_N, b_N).
3. Enumerate points of E_N over F_p, plot as p×p scatter; add decoy curves,
   random noise and white holes so recovering (a_N, b_N) is real CV work.
4. Derive the AES key from (a0, b0) with a SLOW, memory-hard KDF (scrypt) and
   AES-CBC encrypt the flag.  The KDF parameters are published in
   encrypted.txt, so the derivation is unambiguous for the solver.

Why scrypt and not SHA256:  (a0, b0) live in F_p² with p = 4003, i.e. the key
has only ~24 bits of entropy.  With a plain hash the flag's key is recoverable
by a direct ~16M brute in minutes, bypassing the image and the cascade
entirely.  A memory-hard KDF at ~0.2 s/derivation turns that brute into weeks
of single-core, memory-bound work, so the intended path (read the image →
recover (a_N,b_N) → invert/forward-search the cascade → ONE key derivation)
becomes the only practical route.
"""
import os
import random
import hashlib
import numpy as np
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# --- параметры каскада (совпадают с cascade.py) ---
p, N, eta = 4003, 30, 1

# --- параметры KDF (публикуются игроку в encrypted.txt) ---
KDF_SALT = b"perelman/ricci/v2"
KDF_N, KDF_R, KDF_P, KDF_DKLEN = 1 << 16, 8, 1, 32
KDF_MAXMEM = 256 * 1024 * 1024

FLAG = b"KubSTU{45_a_m4773r_0f_f4c7_h3_b3c4m3_7he_f1r57_p3rs0n_to_s01v3_0n3_0f_th3_m1ll3nn1um_pr1z3_pr0bl3m5}"


def K(a, b):
    return (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p


def cascade(a, b):
    for _ in range(N):
        k = K(a, b)
        a = (a - 12 * eta * pow(a, 2, p) * k) % p
        b = (b - 54 * eta * b * k) % p
    return a, b


def derive_key(a0, b0):
    pw = a0.to_bytes(4, "big") + b0.to_bytes(4, "big")
    return hashlib.scrypt(pw, salt=KDF_SALT, n=KDF_N, r=KDF_R, p=KDF_P,
                          maxmem=KDF_MAXMEM, dklen=KDF_DKLEN)


def curve_points(a, b):
    pts = []
    for x in range(p):
        rhs = (pow(x, 3, p) + a * x + b) % p
        if rhs == 0:
            pts.append((x, 0))
        elif pow(rhs, (p - 1) // 2, p) == 1:
            y = pow(rhs, (p + 1) // 4, p)
            if pow(y, 2, p) == rhs:
                pts.append((x, y))
                pts.append((x, (p - y) % p))
    return pts


# --- 1. Ищем подходящую пару (a0, b0) ---
assert p % 4 == 3
while True:
    a0 = random.randint(1, p - 1)
    b0 = random.randint(1, p - 1)
    if K(a0, b0) == 0:
        continue                                # singular E_0
    aN, bN = cascade(a0, b0)
    if K(aN, bN) == 0:
        continue                                # singular E_N
    break

print(f"[+] (a0, b0) = ({a0}, {b0})  ->  (aN, bN) = ({aN}, {bN})")

# --- 2. Точки E_N над F_p ---
points = curve_points(aN, bN)
print(f"[+] точек на E_N: {len(points)}")

# --- 3. Строим изображение ---
img = np.full((p, p), 255, dtype=np.uint8)

def stamp(cy, cx):
    y0, y1 = max(0, cy - 1), min(p, cy + 2)
    x0, x1 = max(0, cx - 1), min(p, cx + 2)
    img[y0:y1, x0:x1] = 0

for x, y in points:
    stamp(y, x)

# 3a. кривые-обманки: ещё 2 случайные неособые кривые, но разрежённо (~35%),
#     чтобы по числу инлайнеров настоящая E_N всё же доминировала.
n_decoys = 2
decoys = []
while len(decoys) < n_decoys:
    da = random.randint(1, p - 1); db = random.randint(1, p - 1)
    if (da, db) == (aN, bN) or K(da, db) == 0:
        continue
    dpts = curve_points(da, db)
    decoys.append((da, db))
    for x, y in dpts:
        if random.random() < 0.35:
            stamp(y, x)
print(f"[+] decoy curves: {decoys}")

# 3b. фейковые точки-шум (3x3, не отличить по форме)
n_noise = 2500
for _ in range(n_noise):
    stamp(random.randint(0, p - 1), random.randint(0, p - 1))

# 3c. белые прямоугольники (дыры)
n_rect = 55
for _ in range(n_rect):
    x0 = random.randint(0, p - 50)
    y0 = random.randint(0, p - 50)
    w  = random.randint(80, 320)
    h  = random.randint(80, 320)
    img[y0:min(y0 + h, p), x0:min(x0 + w, p)] = 255

Image.fromarray(img, mode='L').save('curve.png', optimize=True)
print(f"[+] curve.png сохранён ({p}x{p})")

# --- 5. Шифруем флаг медленным KDF ---
key = derive_key(a0, b0)
iv = os.urandom(16)
ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(FLAG, 16))

with open('encrypted.txt', 'w') as f:
    f.write("# AES-256-CBC.  key = scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),\n")
    f.write(f"#   salt={KDF_SALT!r}, n={KDF_N}, r={KDF_R}, p={KDF_P}, dklen={KDF_DKLEN})\n")
    f.write(f"iv = {iv.hex()}\n")
    f.write(f"ct = {ct.hex()}\n")
print("[+] encrypted.txt сохранён")

with open('gen.log', 'w') as f:
    f.write(f"a0={a0}\nb0={b0}\naN={aN}\nbN={bN}\n")
    f.write(f"decoys={decoys}\n")
    f.write(f"key={key.hex()}\n")
