#!/usr/bin/env sage
# solve.sage  —  "It really isn't enough"
#
# Run inside the folder containing challenge.txt and bd_core.sage:
#     sage: cd /path/to/folder
#     sage: load("solve.sage")
#
# bd_core.sage = canonical Boneh-Durfee (David Wong,
#   https://github.com/mimoo/RSA-and-LLL-attacks) with the __main__ autorun removed.

load("bd_core.sage")

import hashlib, re
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

debug = False          # silence bd_core's lattice chatter

# ---- parse challenge.txt ----
ns = {}
exec(open("challenge.txt").read().split("enc_key")[0], ns)   # loads A=(N,e), B=(N,e)
rest = open("challenge.txt").read()
def grab(name):
    return re.search(rf"{name}\s*=\s*([0-9a-f]+)", rest).group(1)

N, e = Integer(ns["A"][0]), Integer(ns["A"][1])
enc_key   = bytes.fromhex(grab("enc_key"))
src_nonce = bytes.fromhex(grab("src_nonce"))
src_ct    = bytes.fromhex(grab("src_ct"))
src_tag   = bytes.fromhex(grab("src_tag"))

# ---- Boneh-Durfee (real d ~ N^0.26) ----
P.<x, y> = PolynomialRing(ZZ)
A = int((N + 1) / 2)
pol = 1 + x * (A + y)

solx = soly = 0
for delta, m in [(0.27, 4), (0.27, 5), (0.28, 5), (0.28, 6), (0.29, 6), (0.30, 7)]:
    t = max(1, int((1 - 2 * delta) * m))
    X = 2 * floor(N^delta)
    Y = floor(N^(1/2))
    print(f"[*] Boneh-Durfee: delta={delta}, m={m}, t={t}")
    solx, soly = boneh_durfee(pol, e, m, t, X, Y)
    if solx and solx > 0:
        break

if not solx or solx <= 0:
    print("[-] Boneh-Durfee failed; raise m in the sweep list.")
    raise SystemExit

d = int(pol(solx, soly) / e)
print(f"[+] recovered private exponent d ({Integer(d).nbits()} bits)")

# ---- factor N from (e, d) ----
def factor_from_d(N, e, d):
    kphi = e * d - 1
    r = kphi
    while r % 2 == 0:
        r //= 2
    import random as _r
    for _ in range(200):
        g = _r.randrange(2, N - 1)
        xx = power_mod(g, r, N)
        if xx in (1, N - 1):
            continue
        cur = r
        while cur != kphi:
            yy = (xx * xx) % N
            if yy == 1:
                f = gcd(xx - 1, N)
                if 1 < f < N:
                    return f, N // f
                break
            if yy == N - 1:
                break
            xx = yy
            cur *= 2
    return None

fac = factor_from_d(int(N), int(e), int(d))
assert fac, "could not factor N"
p, q = Integer(fac[0]), Integer(fac[1])
assert p * q == N

# ---- layer 1: RSA-OAEP -> AES-GCM -> source.py ----
rsa = RSA.construct((int(N), int(e), int(d), int(p), int(q)))
src_aes_key = PKCS1_OAEP.new(rsa).decrypt(enc_key)
source = AES.new(src_aes_key, AES.MODE_GCM, nonce=src_nonce).decrypt_and_verify(src_ct, src_tag).decode()
print("[+] source recovered")

# ---- layer 2: nonce reuse + broken tag ----
nonce = bytes.fromhex(re.search(r'NONCE = bytes.fromhex\("([0-9a-f]+)"\)', source).group(1))
ct1 = bytes.fromhex(re.search(r'"ct1": "([0-9a-f]+)"', source).group(1))
ct2 = bytes.fromhex(re.search(r'"ct2": "([0-9a-f]+)"', source).group(1))

key = hashlib.sha256(str(int(d)).encode()).digest()      # REAL d, not the decoy in source

fake = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct1[:-16], ct1[-16:])
print(f"[trap] ct1 -> {fake.decode()}")

real = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(ct2[:-16])   # decrypt without verify
print(f"\n[+] FLAG: {real.decode()}")
