# capy256k1

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

Instead of standard secp256k1, the lab shipped its own 256-bit curve in `capy256k1.py`, together with `output.json` containing several diagnostic points and, for each, a result point `R = secret · point`. Recover the secret and decrypt the flag.

**Files:** [generate.py](../../../assets/Crypto/capy256k1/generate.py), [solve.py](../../../assets/Crypto/capy256k1/solve.py), [SECRETS.txt](../../../assets/Crypto/capy256k1/SECRETS.txt)

## 🏁 Solution

### The gist
The home-grown arithmetic in `capy256k1.py` **never checks that a point lies on the curve**. This is a classic **invalid curve attack**.

The lab shipped not the standard secp256k1 but its own 256-bit curve (`a = 0`, with its own prime `p` of the special form `2²⁵⁵ + c`). The key difference: **the prime is NOT chosen twist-secure**. For curves with j-invariant 0, the sextic twists `y² = x³ + b` have one of six orders, determined by the CM representation `4p = L² + 27M²`. For this `p`, several twists carry a subgroup of **prime order `q` in the range 2³⁴…2³⁹**.

`output.json` contains several diagnostic points, and for each — the result point `R = secret · point`. The points lie not on the base curve but on these weak twists.

Here the subgroups are deliberately raised into the 2³⁴…2³⁹ range. A linear sweep (`q` operations) means billions of point additions, which in pure Python takes hours to days — i.e. **brute force does not work**. A real toolchain is needed:

1. **Recognize the invalid curve** — there is no on-curve check.
2. **Read `b = y² − x³ (mod p)`** for each point (`a = 0`).
3. **Compute the twist order without Sage** — the CM method `4p = L² + 27M²` (cornacchia gives `(L, M)`, hence six candidate orders); pick the one that annihilates the point.
4. **Extract `q`** — factor the order (trial division + Pollard rho / ECM), find the prime factor with `q·point = O`.
5. **ECDLP in the subgroup ⟨point⟩** — baby-step/giant-step (or Pollard rho / kangaroo), `O(√q) ≈ 2¹⁷…2²⁰`, recover `secret mod q` from `R = secret·point`.
6. **CRT** over the four residues.

The secret is 128-bit; the product of the four `q` gives a **142-bit** CRT modulus `> 2¹²⁸`, so the value is unique. Then `decrypt_flag(secret, ciphertext)`.

Sage speeds up steps 3–5 but is **not required**: the whole path can be walked in pure Python (cornacchia + rho + BSGS + CRT).

### Solution

```
    point 0: b=2, q=11799928573 (~2^34), secret mod q = 3679953973
    point 1: b=3, q=90287601949 (~2^37), secret mod q = 26161617092
    point 2: b=4, q=354690454903 (~2^39), secret mod q = 223611984189
    point 3: b=5, q=11472381409 (~2^34), secret mod q = 8003312562
[+] secret recovered (~40s): 206229994785984600850531915192031064515
[+] flag: KubSTU{1t_l00k3d_str41ght_1n_d3v}
```

**Flag:** `KubSTU{1t_l00k3d_str41ght_1n_d3v}`
