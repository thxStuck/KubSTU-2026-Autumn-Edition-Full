#!/usr/bin/env python3
"""Organizer-only generator.  Do NOT ship this file to players."""

import json
import secrets

from fog import SEED_BITS, build_session

FLAG = b"KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}"

# q-prime LWE with a LARGE noise bound (bound > q/4): the noise cannot be
# rounded off, so the instance is NOT solvable as generic small-noise LWE --
# the exact noise stream must be reproduced from the generator seed.
#
# The noise generator is a truncated LCG; its 48-bit seed is recoverable only
# by a lattice (FHKLLS) from the published calibration trace: hiding 40 low
# bits per output kills a low-bit brute (2^40), while 24 calibration samples
# give the lattice plenty to reconstruct the state.
CONFIG = {
    "params": {"n": 40, "m": 200, "q": 257, "bound": 100},
    "sampler": {
        "mult": 0x5DEECE66D | 1,   # odd multiplier (public)
        "inc": 0xB,                # increment (public)
        "mod_bits": 48,            # state modulus 2^48
        "hide": 40,                # low bits hidden in the calibration trace
        "calib": 24,               # number of published calibration outputs
    },
}


def main():
    n = CONFIG["params"]["n"]
    m = CONFIG["params"]["m"]
    q = CONFIG["params"]["q"]

    rng = secrets.SystemRandom()

    seed = rng.randrange(1 << (SEED_BITS - 1), 1 << SEED_BITS)   # full 48-bit
    secret = [rng.randrange(q) for _ in range(n)]
    A = [[rng.randrange(q) for _ in range(n)] for _ in range(m)]
    rows = [[rng.randrange(q) for _ in range(n)] for _ in range(len(FLAG) * 8)]

    data = build_session(FLAG, A, rows, secret, CONFIG, seed)

    with open("output.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh)

    with open("SECRETS.txt", "w", encoding="utf-8") as fh:
        fh.write(f"seed = {seed}\n")
        fh.write(f"secret = {secret}\n")
        fh.write(f"flag = {FLAG.decode()}\n")

    print(f"seed={seed}  ({seed.bit_length()} bits)")


if __name__ == "__main__":
    main()
