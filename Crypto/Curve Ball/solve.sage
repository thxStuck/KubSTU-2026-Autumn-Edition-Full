#!/usr/bin/env sage
# solve.sage  —  "Curve Ball"   (run:  sage solve.sage)
#
# Pipeline:
#   C1 (general Weierstrass) -> short form -> #E1 = p1  => anomalous
#       -> Smart's attack (p-adic elliptic log)         => k1
#   k1 -> SHA256 -> AES-CBC decrypt C2 parameters (p2, G2, P2)
#   C2 supersingular y^2=x^3+x, embedding degree 2
#       -> MOV via distortion map phi(x,y)=(-x, i*y)
#       -> Weil pairing into GF(p2^2)*, smooth DLP (Pohlig-Hellman) => k2
#   AES key = SHA256("k1:k2") -> flag
#
# Requires: pycryptodome  (sage -pip install pycryptodome)

import json, hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ---------- parse challenge.txt (Sage-preparse-safe) ----------
ch = open("challenge.txt").read()

def _find(name):
    for line in ch.splitlines():
        s = line.strip()
        if "=" not in s:
            continue
        lhs, _, rhs = s.partition("=")
        if lhs.strip() == name:
            return rhs.strip()
    return None

def gi(name):
    return Integer(_find(name))
def gh(name):
    return _find(name)
def gpt(name):
    raw = _find(name).strip().strip("()")
    xs, ys = raw.split(",")
    return Integer(xs.strip()), Integer(ys.strip())

p1 = gi("p1")
coeffs1 = [gi("a1"), gi("a2"), gi("a3"), gi("a4"), gi("a6")]
G1x, G1y = gpt("G1")
P1x, P1y = gpt("P1")

# ---------- C1: build, confirm anomalous ----------
E1 = EllipticCurve(GF(p1), coeffs1)
G1 = E1(G1x, G1y)
P1 = E1(P1x, P1y)
assert E1.order() == p1, "C1 is not anomalous"
print(f"[+] C1 anomalous confirmed: #E1 = p1 ({p1.nbits()} bits)")

# ---------- Smart's attack -> k1 ----------
def smart_attack(G, P, p):
    E = G.curve()
    Eqp = EllipticCurve(Qp(p, 2), [ZZ(t) for t in E.a_invariants()])

    Gl = Eqp.lift_x(ZZ(G.xy()[0]))
    if (ZZ(Gl.xy()[1]) % p) != (ZZ(G.xy()[1]) % p):
        Gl = -Gl
    Pl = Eqp.lift_x(ZZ(P.xy()[0]))
    if (ZZ(Pl.xy()[1]) % p) != (ZZ(P.xy()[1]) % p):
        Pl = -Pl

    pG, pP = p * Gl, p * Pl
    tG = -(pG.xy()[0]) / (pG.xy()[1])
    tP = -(pP.xy()[0]) / (pP.xy()[1])
    return Integer((tP / tG) % p)

k1 = smart_attack(G1, P1, p1)
assert k1 * G1 == P1, "Smart's attack failed"
print(f"[+] Smart's attack: k1 recovered")

# ---------- derive key from k1, decrypt C2 ----------
key1 = hashlib.sha256(b"C1->C2:" + str(int(k1)).encode()).digest()
blob = unpad(AES.new(key1, AES.MODE_CBC, bytes.fromhex(gh("c2_iv")))
             .decrypt(bytes.fromhex(gh("c2_ct"))), 16)
c2 = json.loads(blob)
p2 = Integer(c2["p2"])
a2_, b2_ = Integer(c2["a"]), Integer(c2["b"])
G2x, G2y = Integer(c2["G2"][0]), Integer(c2["G2"][1])
P2x, P2y = Integer(c2["P2"][0]), Integer(c2["P2"][1])
print(f"[+] C2 parameters decrypted ({p2.nbits()} bits)")

# ---------- MOV on supersingular C2 -> k2 ----------
E2 = EllipticCurve(GF(p2), [a2_, b2_])
G2 = E2(G2x, G2y)
P2 = E2(P2x, P2y)
n = G2.order()

# GF(p2^2) = GF(p2)[i], i^2 = -1  (p2 = 3 mod 4)
F2e = GF(p2**2, 'i', modulus=var('x')**2 + 1)
i = F2e.gen()
E2e = EllipticCurve(F2e, [a2_, b2_])
G2e, P2e = E2e(G2), E2e(P2)

# distortion map gives a non-degenerate pairing with no random search
def distort(P):
    x, y = P.xy()
    return E2e(-x, i * y)

alpha = G2e.weil_pairing(distort(G2e), n)
beta  = P2e.weil_pairing(distort(G2e), n)

# smooth DLP in GF(p2^2)* via Pohlig-Hellman (explicit order)
ord_alpha = alpha.multiplicative_order()
k2_partial = Integer(discrete_log(beta, alpha, ord=ord_alpha, operation='*'))

# Weil pairing can lose part of the 2-power order, so discrete_log yields
# k2 only modulo ord_alpha. The missing cofactor n/ord_alpha is tiny
# (a divisor of the 2-part), so recover the full k2 by a short search.
cof = n // ord_alpha
k2 = None
for j in range(cof):
    cand = k2_partial + j * ord_alpha
    if cand * G2 == P2:
        k2 = Integer(cand)
        break
assert k2 is not None, "MOV failed (cofactor search exhausted)"
assert k2 * G2 == P2, "MOV failed"
print(f"[+] MOV attack: k2 recovered")

# ---------- final flag ----------
key = hashlib.sha256(f"{int(k1)}:{int(k2)}".encode()).digest()
flag = unpad(AES.new(key, AES.MODE_CBC, bytes.fromhex(gh("iv")))
             .decrypt(bytes.fromhex(gh("ct"))), 16)
print(f"\n[+] FLAG: {flag.decode()}")
