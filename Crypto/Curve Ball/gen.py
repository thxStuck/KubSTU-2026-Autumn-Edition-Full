#!/usr/bin/env python3
"""
Generator — "Curve Ball" (KubSTU CTF, Crypto, grob).  Admin-only.

Chain:
  Layer 0 : E1 given in GENERAL Weierstrass form (player reduces to short form).
  Layer 1 : E1 is anomalous (#E1 = p1)  -> Smart's attack recovers k1.
  Layer 2 : k1 seeds E2 (supersingular, embedding degree 2) -> MOV recovers k2.
  Layer 3 : AES key = SHA256(f"{k1}:{k2}") -> flag.
  Decoy   : E3 looks weak but Smart's on it yields garbage.

Anomalous E1 built via CM (D = -11, class number 1, j = -32768).
Supersingular E2: y^2 = x^3 + x over p2 = 3 (mod 4).
"""
import os
import json
import random
import hashlib
from sympy import isprime, sqrt_mod, nextprime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

FLAG = b"KubSTU{45_f0r_311ip71c_curv3_g30m37ry_4nd_cryp70gr4phy_1n_g3ner41_1_63l13v3_y0u_w3re_46l3_70_501ve_i7}"


# ---------- EC arithmetic over F_p (short form) ----------
def ec_add(P, Q, a, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    if P == Q:
        m = (3*x1*x1 + a) * pow(2*y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m*m - x1 - x2) % p
    y3 = (m*(x1 - x3) - y1) % p
    return (x3, y3)

def ec_mul(k, P, a, p):
    R = None
    while k:
        if k & 1: R = ec_add(R, P, a, p)
        P = ec_add(P, P, a, p); k >>= 1
    return R

def find_point(a, b, p):
    for _ in range(5000):
        x = random.randrange(p)
        rhs = (x**3 + a*x + b) % p
        if pow(rhs, (p-1)//2, p) == 1:
            y = sqrt_mod(rhs, p)
            if y:
                return (x, y)
    raise RuntimeError("no point found")


# ---------- build anomalous curve E1 (CM, D=-11) ----------
def gen_anomalous():
    D_abs, j_D = 11, -32768
    f = (1 << 128) | 1
    for _ in range(500000):
        num = D_abs * f * f + 1
        if num % 4 == 0:
            cand = num // 4
            if isprime(cand):
                p = cand
                j = j_D % p
                inv = pow((1728 - j) % p, -1, p)
                k = (j * inv) % p
                A, B = (3*k) % p, (2*k) % p
                G = find_point(A, B, p)
                if ec_mul(p, G, A, p) is None:      # confirm #E = p
                    return p, A, B, G
        f += 2
    raise RuntimeError("failed to build anomalous curve")


# ---------- build supersingular curve E2 from seed ----------
def gen_supersingular(seed):
    # Need p2 = 3 mod 4 (so y^2=x^3+x is supersingular, #E=p2+1) AND
    # p2+1 SMOOTH, so that after MOV the DLP in GF(p2^2)* is solvable
    # via Pohlig-Hellman. Build p2+1 = 2^a * (small primes).
    from sympy import primerange
    rng = random.Random(seed)              # deterministic from k1
    sp = list(primerange(3, 10000))
    for _ in range(5_000_000):
        prod = 1 << rng.randint(2, 8)
        while prod.bit_length() < 256:
            prod *= rng.choice(sp)
        p2 = prod - 1
        if 254 <= p2.bit_length() <= 258 and p2 % 4 == 3 and isprime(p2):
            A2, B2 = 1, 0
            G2 = find_point(A2, B2, p2)
            assert ec_mul(p2 + 1, G2, A2, p2) is None, "E2 not supersingular"
            return p2, A2, B2, G2
    raise RuntimeError("failed to build smooth supersingular curve")


# ---------- short form -> general Weierstrass (masking) ----------
def to_general(A, B, p):
    r, s, t = [random.randrange(p) for _ in range(3)]
    a1 = (2*s) % p
    a2 = (3*r - s*s) % p
    a3 = (2*t) % p
    a4 = (A + 3*r*r - 2*s*t) % p
    a6 = (A*r + B + r**3 - t*t) % p
    return (a1, a2, a3, a4, a6), (r, s, t)

def point_to_general(P, r, s, t, p):
    # inverse of x=X+r, y=Y+sX+t  ->  X=x-r, Y=y - s*X - t
    x, y = P
    X = (x - r) % p
    Yy = (y - s*X - t) % p
    return (X, Yy)


# ========================= BUILD =========================
# -- E1 anomalous --
p1, A1, B1, G1 = gen_anomalous()
k1 = random.randrange(2, p1)
P1 = ec_mul(k1, G1, A1, p1)

# mask E1 into general Weierstrass, transform its points accordingly
gen_coeffs1, (r1, s1, t1) = to_general(A1, B1, p1)
G1g = point_to_general(G1, r1, s1, t1, p1)
P1g = point_to_general(P1, r1, s1, t1, p1)

# -- E2 supersingular, seeded by k1 --
seed = int.from_bytes(hashlib.sha256(str(k1).encode()).digest(), 'big')
p2, A2, B2, G2 = gen_supersingular(seed)
# order of G2 divides p2+1 (smooth). pick k2 below that order so PH recovers it fully.
ordG2 = p2 + 1
# reduce G2 to a generator of large smooth order; use full group order as bound
k2 = random.randrange(2, ordG2)
P2 = ec_mul(k2, G2, A2, p2)

# encrypt C2 parameters under a key derived from k1 (hard link to layer 1)
c2_blob = json.dumps({
    "p2": p2,
    "a": A2,
    "b": B2,
    "G2": list(G2),
    "P2": list(P2),
}).encode()
key1 = hashlib.sha256(b"C1->C2:" + str(k1).encode()).digest()
iv_c2 = os.urandom(16)
c2_ct = AES.new(key1, AES.MODE_CBC, iv_c2).encrypt(pad(c2_blob, 16))

# -- decoy E3: looks weak (small-ish trace) but Smart's gives garbage --
# build a normal random curve over a random prime; its #E != p so Smart's fails
pd = nextprime((1 << 256) | random.randrange(1 << 200))
Ad, Bd = random.randrange(pd), random.randrange(pd)
while (4*Ad**3 + 27*Bd**2) % pd == 0:
    Ad, Bd = random.randrange(pd), random.randrange(pd)
Gd = find_point(Ad, Bd, pd)
kd = random.randrange(2, pd)
Pd = ec_mul(kd, Gd, Ad, pd)
gen_coeffsd, (rd, sd, td) = to_general(Ad, Bd, pd)
Gdg = point_to_general(Gd, rd, sd, td, pd)
Pdg = point_to_general(Pd, rd, sd, td, pd)

# -- final AES --
key = hashlib.sha256(f"{k1}:{k2}".encode()).digest()
iv = os.urandom(16)
ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(FLAG, 16))


# ========================= WRITE =========================
with open("challenge.txt", "w") as fo:
    fo.write("# Curve Ball\n")
    fo.write("# Everything below lives over its own prime field.\n")
    fo.write("# Curves are given in general Weierstrass form:\n")
    fo.write("#     y^2 + a1*x*y + a3*y = x^3 + a2*x^2 + a4*x + a6\n\n")

    fo.write("# ===== curve C1 =====\n")
    fo.write(f"p1  = {p1}\n")
    fo.write(f"a1  = {gen_coeffs1[0]}\n")
    fo.write(f"a2  = {gen_coeffs1[1]}\n")
    fo.write(f"a3  = {gen_coeffs1[2]}\n")
    fo.write(f"a4  = {gen_coeffs1[3]}\n")
    fo.write(f"a6  = {gen_coeffs1[4]}\n")
    fo.write(f"G1  = {G1g}\n")
    fo.write(f"P1  = {P1g}\n\n")

    fo.write("# ===== curve C3 =====\n")
    fo.write(f"p3  = {pd}\n")
    fo.write(f"c1  = {gen_coeffsd[0]}\n")
    fo.write(f"c2  = {gen_coeffsd[1]}\n")
    fo.write(f"c3  = {gen_coeffsd[2]}\n")
    fo.write(f"c4  = {gen_coeffsd[3]}\n")
    fo.write(f"c6  = {gen_coeffsd[4]}\n")
    fo.write(f"G3  = {Gdg}\n")
    fo.write(f"P3  = {Pdg}\n\n")

    fo.write("# ===== curve C2 (encrypted; key derived from C1's secret) =====\n")
    fo.write("# Recover C1's secret scalar k1 first, then:\n")
    fo.write("#     key = SHA256(b\"C1->C2:\" + str(k1).encode())\n")
    fo.write("#     plaintext = AES-CBC = JSON {p2, a, b, G2, P2}\n")
    fo.write(f"c2_iv = {iv_c2.hex()}\n")
    fo.write(f"c2_ct = {c2_ct.hex()}\n\n")

    fo.write("# ===== encrypted flag (AES-CBC) =====\n")
    fo.write(f"iv  = {iv.hex()}\n")
    fo.write(f"ct  = {ct.hex()}\n")

with open("gen.log", "w") as fo:
    fo.write(f"k1={k1}\nk2={k2}\n")
    fo.write(f"p1={p1}\nA1_short={A1}\nB1_short={B1}\n")
    fo.write(f"r1,s1,t1={r1},{s1},{t1}\n")
    fo.write(f"p2={p2}\nseed_from_k1={seed}\n")
    fo.write(f"aes_key={key.hex()}\n")
    fo.write(f"FLAG={FLAG.decode()}\n")
    fo.write(f"[decoy] pd={pd} Ad={Ad} Bd={Bd} kd={kd}\n")

print(f"[+] C1 anomalous  p1={p1.bit_length()}b")
print(f"[+] C2 supersingular p2={p2.bit_length()}b (seed from k1)")
print(f"[+] C3 decoy      p3={pd.bit_length()}b")

# self-check: k2 must be below order(G2) so the cofactor search in the
# solver recovers it fully (otherwise the challenge would be unsolvable)
ordG2 = p2 + 1
_o = ordG2
for _pr in set(__import__("sympy").factorint(ordG2)):
    while _o % _pr == 0 and ec_mul(_o // _pr, G2, A2, p2) is None:
        _o //= _pr
assert k2 < ordG2, "k2 >= order(G2): regenerate (unsolvable)"
assert ec_mul(k2, G2, A2, p2) == P2, "k2*G2 != P2 sanity failed"
print(f"[+] solvability self-check passed (k2 < order G2)")
print("[+] challenge.txt + gen.log written")
