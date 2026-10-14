"""
capy256k1 — reference solution (no Sage).

Invalid-curve attack.  capy256k1.py never checks that a point is on the curve,
so each diagnostic point actually lives on a weak sextic twist y^2 = x^3 + b.
Steps per diagnostic:

  1. read b = y^2 - x^3  (mod p)          (a = 0, so b is immediate)
  2. twist order via CM:  4p = L^2 + 27 M^2  ->  six candidate orders;
     pick the one that annihilates the point
  3. the point has a single large prime order q (2^34..2^39): pull q out of
     the order (trial division + Pollard rho) and confirm q*Point = O
  4. ECDLP in the prime-order subgroup <Point>:  baby-step / giant-step
     recovers  secret mod q  from the published result point secret*Point

Then CRT the four residues (product > 2^128 = secret range -> unique) and
decrypt the flag.

Run:  python3 solve.py
"""
import json, math, random, sys, time
from pathlib import Path

# --- robustly locate capy256k1.py and output.json (same folder, ../player, etc.) ---
HERE = Path(__file__).resolve().parent
def _find(fname):
    for d in (HERE, HERE.parent / "player", HERE / "player", Path.cwd()):
        if (d / fname).exists():
            return d
    return HERE
CAPY_DIR = _find("capy256k1.py")
OUT_DIR = _find("output.json")
sys.path.insert(0, str(CAPY_DIR))

from capy256k1 import P, Point, decrypt_flag
from sympy.solvers.diophantine.diophantine import cornacchia

random.seed(1)


def cm_orders():
    L, M = next(iter(cornacchia(1, 27, 4 * P)))
    tr = {L, -L, (L+9*M)//2, -((L+9*M)//2), (L-9*M)//2, -((L-9*M)//2)}
    return sorted({P + 1 - t for t in tr})


def is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d, r = n-1, 0
    while d % 2 == 0: d //= 2; r += 1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a, d, n)
        if x in (1, n-1): continue
        for _ in range(r-1):
            x = x*x % n
            if x == n-1: break
        else: return False
    return True


def brent(n):
    if n % 2 == 0: return 2
    while True:
        y, c, m = random.randrange(1, n), random.randrange(1, n), 64
        g = r = q = 1; x = ys = y
        while g == 1:
            x = y
            for _ in range(r): y = (y*y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r-k)):
                    y = (y*y + c) % n; q = q * abs(x - y) % n
                g = math.gcd(q, n); k += m
            r *= 2
        if g != n: return g
        while True:
            ys = (ys*ys + c) % n; g = math.gcd(abs(x - ys), n)
            if g > 1: break
        if g != n: return g


def point_order_prime(Pt, order):
    cof = order
    for p in range(2, 1_000_000):
        if cof % p == 0:
            while cof % p == 0: cof //= p
            if (p * Pt).infinity: return p
    seen = set()
    while cof > 1:
        if is_prime(cof):
            return cof if (cof * Pt).infinity else None
        f = brent(cof)
        while not is_prime(f): f = brent(f)
        if f in seen:
            while cof % f == 0: cof //= f
            continue
        seen.add(f)
        if (f * Pt).infinity: return f
        while cof % f == 0: cof //= f
    return None


def bsgs(G, Q, q):
    m = math.isqrt(q) + 1
    table = {}
    cur = Point()
    for j in range(m):
        key = None if cur.infinity else (cur.x, cur.y)
        table.setdefault(key, j)
        cur = cur + G
    neg_mG = -(m * G)
    gamma = Q
    for i in range(m + 1):
        key = None if gamma.infinity else (gamma.x, gamma.y)
        if key in table:
            return i * m + table[key]
        gamma = gamma + neg_mG
    return None


def crt(res, mods):
    x, Mall = 0, 1
    for mm in mods: Mall *= mm
    for a, mm in zip(res, mods):
        Mi = Mall // mm
        x = (x + a * Mi * pow(Mi, -1, mm)) % Mall
    return x, Mall


def main():
    data = json.load(open(OUT_DIR / "output.json"))
    orders = cm_orders()
    res, mods = [], []
    t0 = time.time()
    for i, d in enumerate(data["diagnostics"]):
        Pt, R = Point(d["x"], d["y"]), Point(d["rx"], d["ry"])
        b = (d["y"]**2 - d["x"]**3) % P
        O = next(o for o in orders if (o * Pt).infinity)
        q = point_order_prime(Pt, O)
        k = bsgs(Pt, R, q)
        assert k is not None and (k * Pt) == R
        print(f"    point {i}: b={b}, q={q} (~2^{q.bit_length()}), secret mod q = {k}")
        res.append(k); mods.append(q)
    secret, M = crt(res, mods)
    print(f"[+] secret recovered ({time.time()-t0:.1f}s): {secret}")
    print("[+] flag:", decrypt_flag(secret, bytes.fromhex(data["ciphertext"])))


if __name__ == "__main__":
    main()
