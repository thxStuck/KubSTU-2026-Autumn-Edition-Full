#!/usr/bin/env python3
"""
The Deterministic Fog - reference solution.

The LWE noise bound (100) exceeds q/4, so the instance is NOT decodable as
generic small-noise LWE: the exact noise stream must be reproduced.  The noise
is a public truncated LCG whose 48-bit seed is hidden, but a short calibration
trace (high 8 bits of the first 24 states) is published.

  1. Recover the 48-bit seed from the calibration trace with a lattice
     (the classic truncated-LCG / FHKLLS reconstruction).
  2. Reproduce the full noise stream.
  3. The public samples now give a plain linear system  A s = b - e (mod q);
     solve it for s by Gaussian elimination over F_q.
  4. Strip noise + phase from the ciphertext, read the (q/2)-encoded bits.

Run:  python3 solution_fog.py        (needs fpylll)
"""
import json
from pathlib import Path
from fpylll import IntegerMatrix, LLL

HERE = Path(__file__).resolve().parent
def _find(fname):
    for d in (HERE, HERE.parent / "player", HERE / "player", Path.cwd()):
        if (d / fname).exists():
            return d
    return HERE
PLAYER = _find("output.json")


def recover_seed(calib, mult, inc, M, hide):
    """Lattice recovery of x_0 from high bits y_i = x_i >> hide."""
    K = len(calib)
    B = 1 << hide
    # x_i = alpha_i * x0 + beta_i (mod M); x0 = (calib[0]<<hide) + l0
    alpha, beta = [], []
    ai, bi = 1, 0
    for i in range(K):
        alpha.append(ai % M)
        beta.append((ai * (calib[0] << hide) + bi) % M)
        bi = (mult * bi + inc) % M
        ai = (mult * ai) % M

    dim = K + 1
    Mx = IntegerMatrix(dim, dim)
    Mx[0, 0] = 1
    for i in range(1, K):
        Mx[0, i] = alpha[i] % M
    for i in range(1, K):
        Mx[i, i] = M
    for i in range(1, K):
        Mx[dim - 1, i] = (beta[i] - (calib[i] << hide)) % M
    Mx[dim - 1, dim - 1] = B

    LLL.reduction(Mx)
    for r in range(dim):
        if abs(Mx[r, dim - 1]) == B:
            sign = 1 if Mx[r, dim - 1] == B else -1
            l0 = (sign * Mx[r, 0]) % B
            x0 = (calib[0] << hide) + l0
            x = x0; ok = (x >> hide) == calib[0]
            for i in range(1, K):
                x = (mult * x + inc) % M
                ok &= (x >> hide) == calib[i]
            if ok:
                return x0
    raise RuntimeError("seed not recovered")


def noise_stream(seed, mult, inc, M, calib, bound, count):
    x = seed % M
    for _ in range(calib):                 # advance x_0 -> x_{calib}
        x = (mult * x + inc) % M
    out = []
    for _ in range(count):
        out.append(x % (2 * bound + 1) - bound)
        x = (mult * x + inc) % M
    return out


def solve_linear(A, rhs, q):
    """Solve A s = rhs (mod q), A is m x n with m >= n, unique s."""
    m, n = len(A), len(A[0])
    M = [row[:] + [rhs[i] % q] for i, row in enumerate(A)]
    piv = []
    r = 0
    for c in range(n):
        pr = next((i for i in range(r, m) if M[i][c] % q), None)
        if pr is None:
            continue
        M[r], M[pr] = M[pr], M[r]
        invp = pow(M[r][c], -1, q)
        M[r] = [(v * invp) % q for v in M[r]]
        for i in range(m):
            if i != r and M[i][c] % q:
                f = M[i][c]
                M[i] = [(M[i][k] - f * M[r][k]) % q for k in range(n + 1)]
        piv.append(c); r += 1
        if r == n:
            break
    s = [0] * n
    for i, c in enumerate(piv):
        s[c] = M[i][n] % q
    return s


def main():
    data = json.load(open(PLAYER / "output.json"))
    q = data["params"]["q"]; bound = data["params"]["bound"]
    s_cfg = data["sampler"]
    mult, inc, M = s_cfg["mult"], s_cfg["inc"], 1 << s_cfg["mod_bits"]
    hide, calib = s_cfg["hide"], s_cfg["calib"]

    seed = recover_seed(data["calibration"], mult, inc, M, hide)
    print(f"[+] seed recovered: {seed}")

    A, b, R, ct = data["A"], data["b"], data["R"], data["ciphertext"]
    e = noise_stream(seed, mult, inc, M, calib, bound, len(b) + len(ct))

    rhs = [(b[i] - e[i]) % q for i in range(len(b))]
    s = solve_linear(A, rhs, q)
    print(f"[+] secret recovered ({len(s)} elems)")

    bits = []
    for j, row in enumerate(R):
        phase = sum(x * y for x, y in zip(row, s)) % q
        val = (ct[j] - e[len(b) + j] - phase) % q
        bits.append(0 if min(val, q - val) < abs(val - q // 2) else 1)

    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i:i + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    print("[+] plaintext:", out.decode(errors="replace"))


if __name__ == "__main__":
    main()
