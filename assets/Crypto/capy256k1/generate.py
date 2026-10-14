"""
capy256k1 — instance generator (hardened).

The lab's curve uses a custom 256-bit prime (a = 0, j-invariant 0), so every
sextic twist y^2 = x^3 + b has one of six group orders given by the CM
representation 4p = L^2 + 27 M^2.  Unlike the standard secp256k1, this prime
was NOT chosen twist-secure: several twists carry a prime-order subgroup in
the 2^32 .. 2^40 range.  Those subgroups are far too large for a linear walk
but are solvable by baby-step/giant-step (or Pollard rho) — so the intended
invalid-curve attack now needs a real DLP routine plus CRT, not a for-loop.

The secret is 128-bit; the CRT modulus (product of the chosen subgroup primes)
exceeds it, so the recovered value is unique.  No public key is published.

No Sage dependency (cornacchia for the CM step, ECM for the band primes).

Run:  python3 generate.py
"""

import json
import secrets
import sys
from pathlib import Path

from sympy.solvers.diophantine.diophantine import cornacchia

ROOT = Path(__file__).resolve().parent.parent
PLAYER_DIR = ROOT / "player"
OUTPUT_FILE = PLAYER_DIR / "output.json"
SECRETS_FILE = Path(__file__).resolve().parent / "SECRETS.txt"

sys.path.insert(0, str(PLAYER_DIR))
from capy256k1 import P, Point, probe, encrypt_flag  # noqa: E402

FLAG = "KubSTU{1t_l00k3d_str41ght_1n_d3v}"

SECRET_BITS = 128
REAL_B = 7                       # base curve y^2 = x^3 + 7 (reserved)

# Four weak sextic twists of this prime, each carrying a prime-order subgroup
# in the 2^33 .. 2^39 BSGS band.  (b, q, full twist order).  The primes were
# located once with ECM over the six CM twist orders; their product is a
# ~141-bit CRT modulus, comfortably above the 128-bit secret.
CHOSEN = [
    (2, 11799928573,
     57896044618658097711785492504343953979085142477686007990470793051870453243053),
    (3, 90287601949,
     57896044618658097711785492504343953978719001740178540358883402650443963079739),
    (4, 354690454903,
     57896044618658097711785492504343953979517459296605260332042017293687417040061),
    (5, 11472381409,
     57896044618658097711785492504343953979151318559097792700454626892260926876747),
]


def sqrt_mod(a):
    a %= P
    if a == 0:
        return 0
    if pow(a, (P - 1) // 2, P) != 1:
        return None
    return pow(a, (P + 1) // 4, P)        # P % 4 == 3


def random_point(b):
    while True:
        x = secrets.randbelow(P - 1) + 1
        y = sqrt_mod((x * x * x + b) % P)
        if y:
            return Point(x, y)


def twist_orders():
    L, M = next(iter(cornacchia(1, 27, 4 * P)))
    assert L * L + 27 * M * M == 4 * P
    traces = {
        L, -L,
        (L + 9 * M) // 2, -((L + 9 * M) // 2),
        (L - 9 * M) // 2, -((L - 9 * M) // 2),
    }
    return sorted({P + 1 - t for t in traces})


def curve_order(b, candidates):
    point = random_point(b)
    matching = [n for n in candidates if (n * point).infinity]
    if len(matching) != 1:
        return None
    o = matching[0]
    if not (o * random_point(b)).infinity:     # confirm
        return None
    return o


def make_order_q_point(b, q, order):
    cofactor = order // q
    while True:
        point = cofactor * random_point(b)
        if point.infinity:
            continue
        if (q * point).infinity:
            return point


def main():
    print("[+] deriving twist orders (CM, no Sage)")
    candidates = set(twist_orders())

    # integrity: every chosen order is a genuine CM twist order, q | order
    product = 1
    for b, q, order in CHOSEN:
        assert order in candidates, f"order for b={b} is not a CM twist order"
        assert order % q == 0, f"q does not divide order for b={b}"
        product *= q
        print(f"    twist b={b:<3} subgroup prime q={q}  (~2^{q.bit_length()})")
    print(f"[+] CRT modulus {product.bit_length()} bits over {len(CHOSEN)} subgroups")
    if product <= (1 << SECRET_BITS):
        raise RuntimeError("CRT modulus does not cover the secret")

    secret = secrets.randbelow(1 << SECRET_BITS)

    diagnostics = []
    for b, q, order in CHOSEN:
        point = make_order_q_point(b, q, order)
        assert (point.y * point.y - point.x ** 3 - b) % P == 0
        result = probe(secret, point)                 # result = secret * point
        assert not result.infinity
        diagnostics.append({
            "x": point.x, "y": point.y,
            "rx": result.x, "ry": result.y,
        })

    output = {
        "curve": "capy256k1",
        "diagnostics": diagnostics,
        "ciphertext": encrypt_flag(secret, FLAG).hex(),
    }
    with OUTPUT_FILE.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    with SECRETS_FILE.open("w", encoding="utf-8") as fh:
        fh.write(f"secret = {secret}\n")
        fh.write(f"secret_bits = {secret.bit_length()}\n")
        fh.write(f"subgroups (b, q) = {[(b, q) for b, q, _ in CHOSEN]}\n")
        fh.write(f"crt_modulus_bits = {product.bit_length()}\n")
        fh.write(f"flag = {FLAG}\n")

    print(f"[+] secret bits: {secret.bit_length()}")
    print(f"[+] diagnostics: {len(diagnostics)}")
    print(f"[+] written: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
