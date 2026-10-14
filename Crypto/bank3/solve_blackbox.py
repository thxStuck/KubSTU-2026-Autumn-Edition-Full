#!/usr/bin/env python3
"""
KubSTU Bank (bank3) — reference player-side solver (BLACK BOX, no source).

Input : a folder of .cert files collected from the bot (ideally many from ONE
        account; ~70+, 120 recommended).
Output: the recovered server private key d, and a forged .cert for `admin`.

Idea  : account_id = base64(r||s) is an ECDSA/secp256k1 signature over the
        account name (e = sha256(name) mod n). The nonce is biased — a few
        high and low bits are FIXED (and equal across all signatures of one
        account) while the middle ~250 bits are random. That is a Hidden
        Number Problem. We don't know the fixed bits, but there are only a
        handful, so we brute the fixed offset and validate each guess purely
        by the structural bound (every recovered core must be < 2^250).

Deps  : pip install fpylll cysignals
Usage : python3 solve_blackbox.py <certs_dir> [admin_name]
"""
import sys, os, re, glob, base64, hashlib, time
from fpylll import IntegerMatrix, LLL, BKZ

# ---- secp256k1 ----
P  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
A_ = 0
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G  = (GX, GY)

def inv(a, m): return pow(a, -1, m)
def add(Pt, Qt):
    if Pt is None: return Qt
    if Qt is None: return Pt
    x1, y1 = Pt; x2, y2 = Qt
    if x1 == x2 and (y1 + y2) % P == 0: return None
    if Pt == Qt: l = (3*x1*x1 + A_) * inv(2*y1, P) % P
    else:        l = (y2 - y1) * inv((x2 - x1) % P, P) % P
    x3 = (l*l - x1 - x2) % P
    return (x3, (l*(x1 - x3) - y1) % P)
def mul(k, Pt):
    R = None
    while k:
        if k & 1: R = add(R, Pt)
        Pt = add(Pt, Pt); k >>= 1
    return R
def H(b): return int.from_bytes(hashlib.sha256(b).digest(), "big") % N

# ---- parse certs ----
def load_certs(folder):
    out = []
    for fp in glob.glob(os.path.join(folder, "**", "*.cert"), recursive=True):
        t = open(fp).read()
        acc = re.search(r"account:\s*(\S+)", t).group(1)
        sig = re.search(r"signature:\s*(\S+)", t).group(1)
        blob = base64.b64decode(sig)
        r = int.from_bytes(blob[:32], "big"); s = int.from_bytes(blob[32:], "big")
        out.append((acc, r, s))
    return out

# ---- HNP with a GUESSED fixed offset (unknown high/low bits), brute all offsets ----
def recover(sigs, e, a_bits, c_bits):
    K = 1 << (256 - a_bits - c_bits)          # core bound (2^250 for 3+3)
    Kh = K >> 1; F = 1 << 7
    PREF_SH = 256 - a_bits; cmul = 1 << c_bits
    for Pbits in range(1 << a_bits):
        for Qbits in range(1 << c_bits):
            Aabs = (Pbits << PREF_SH) + Qbits
            A, B = [], []
            for (r, s) in sigs:
                den = inv(s * cmul % N, N)
                A.append(den * r % N)
                B.append(den * (e - s * Aabs) % N)
            m = len(A)
            M = IntegerMatrix(m + 2, m + 2)
            for i in range(m): M[i, i] = N * F
            for j in range(m):
                M[m, j]   = A[j] * F
                M[m+1, j] = ((B[j] - Kh) % N) * F
            M[m, m] = 1; M[m+1, m+1] = Kh * F
            LLL.reduction(M)                      # plain LLL per offset (fast);
            d = read(M, A, B, K, m)               # 120 sigs => LLL is enough
            if d is not None:
                return d, Pbits, Qbits
    return None

def read(M, A, B, K, m):
    tgt = (K >> 1) * (1 << 7)
    for row in M:
        if abs(row[m+1]) == tgt:
            sgn = 1 if row[m+1] == tgt else -1
            for cand in (sgn*row[m] % N, -sgn*row[m] % N):
                d = cand % N
                if all((A[j]*d + B[j]) % N < K for j in range(m)):
                    return d
    return None

def forge(d, name):
    import secrets
    e = H(name.encode()); k = secrets.randbelow(N - 1) + 1
    R = mul(k, G); r = R[0] % N; s = inv(k, N) * (e + r*d) % N
    return base64.b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).decode()

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "certs"
    admin  = sys.argv[2] if len(sys.argv) > 2 else "admin"
    certs = load_certs(folder)
    accs = set(a for a, _, _ in certs)
    acc = certs[0][0]
    sigs = [(r, s) for (a, r, s) in certs if a == acc][:120]   # one account
    e = H(acc.encode())
    print(f"[*] {len(certs)} certs, {len(accs)} account(s); using {len(sigs)} sigs from '{acc}'")

    t0 = time.time(); found = None
    for (a_bits, c_bits) in [(3, 3), (2, 2), (4, 4), (3, 0), (0, 3)]:   # sweep structures
        print(f"    trying fixed bits: top={a_bits}, bottom={c_bits}  ({1<<(a_bits+c_bits)} offsets)")
        res = recover(sigs, e, a_bits, c_bits)
        if res:
            d, Pb, Qb = res
            print(f"[+] server key recovered in {time.time()-t0:.0f}s  "
                  f"(top={a_bits},bottom={c_bits}, offset P={Pb},Q={Qb})")
            print(f"[+] d = {hex(d)}")
            found = d; break
    if found is None:
        print("[-] not recovered — collect more signatures or widen the sweep"); sys.exit(1)

    token = forge(found, admin)
    print(f"\n[+] forged account_id for '{admin}':\n{token}\n")
    print("Submit this .cert to the bot's /login :\n")
    print("-----BEGIN KUBSTU BANK CERTIFICATE-----")
    print(f"account: {admin}")
    print(f"signature: {token}")
    print("-----END KUBSTU BANK CERTIFICATE-----")
