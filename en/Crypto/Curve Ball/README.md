# Curve Ball

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

A chain of two tightly-coupled elliptic curves (plus a decoy curve C3) and an AES-encrypted flag. Each layer is a separate, non-trivial attack and the chain can only be solved strictly in order. Recover the flag.

**Files:** [gen.py](../../../assets/Crypto/Curve%20Ball/gen.py), [solve.sage](../../../assets/Crypto/Curve%20Ball/solve.sage), [gen.log](../../../assets/Crypto/Curve%20Ball/gen.log), [screenshot](../../../assets/Crypto/Curve%20Ball/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-02%20022018.png)

## 🏁 Solution

### Overview
A chain of two elliptic curves, tightly coupled. Each layer is a separate, non-trivial attack. It can only be fully solved sequentially.

```
C1 (general Weierstrass)
   -> привести к короткой форме
   -> посчитать #E1, обнаружить #E1 = p1  (АНОМАЛЬНАЯ)
   -> Smart's attack -> k1
k1 -> SHA256 -> ключ AES -> расшифровать параметры C2
C2 (supersingular, embedding degree 2)
   -> MOV attack (distortion map + Weil pairing)
   -> smooth DLP в GF(p2^2)* (Pohlig-Hellman) -> k2
AES(key = SHA256("k1:k2")) -> флаг
```

Decoy: C3 is an ordinary curve that the player may try to attack, but it does not lead to the flag (none of the attacks yields a useful result on it).

---

### Layer 0 — recognition
C1 is given in **full Weierstrass form** `y² + a1·xy + a3·y = x³ + a2·x² + a4·x + a6`. The player reduces it to the short form `y² = x³ + Ax + B` (standard b/c-invariants) and computes the order (`E.order()` in Sage).

The key observation: **#E1 = p1**. This is an anomalous curve, and for it ECDLP is solved in linear time via Smart's attack. Without computing the order, the curve looks like an ordinary unliftable 256-bit ECDLP — that is the trap of layer 0.

---

### Layer 1 — Smart's attack (SSSA)
For an anomalous curve (`#E = p`) there is an isomorphism onto the additive group `F_p` via a lift into the p-adic field `Q_p` and the formal logarithm.

```python
def smart_attack(G, P, p):
    E = G.curve()
    Eqp = EllipticCurve(Qp(p, 2), [ZZ(t) for t in E.a_invariants()])
    Gl = Eqp.lift_x(ZZ(G.xy()[0]))
    if (ZZ(Gl.xy()[1]) % p) != (ZZ(G.xy()[1]) % p): Gl = -Gl
    Pl = Eqp.lift_x(ZZ(P.xy()[0]))
    if (ZZ(Pl.xy()[1]) % p) != (ZZ(P.xy()[1]) % p): Pl = -Pl
    pG, pP = p*Gl, p*Pl                    # push into the formal group
    tG = -(pG.xy()[0]) / (pG.xy()[1])      # p-adic elliptic log
    tP = -(pP.xy()[0]) / (pP.xy()[1])
    return Integer((tP / tG) % p)
```

The result is `k1`, the secret scalar of C1.

---

### Linking the layers
The parameters of C2 are AES-CBC encrypted, the key being derived from `k1`:

```python
key1 = SHA256(b"C1->C2:" + str(k1).encode())
plaintext = JSON {p2, a, b, G2, P2}
```

Without Smart's attack on C1 the parameters of C2 are unreachable — brute-forcing k1 (258 bits) is impossible. This makes the chain strictly sequential.

---

### Layer 2 — MOV attack
After decryption, C2 turns out to be supersingular: `y² = x³ + x` over `p2 ≡ 3 (mod 4)`, `#E2 = p2 + 1`, embedding degree 2. The order is **smooth** (deliberately constructed), so the DLP is solvable after the transfer.

MOV transfers the ECDLP into `GF(p2²)*` via the Weil pairing. Instead of randomly searching for an auxiliary point, a **distortion map** `φ(x,y) = (−x, i·y)` (where `i² = −1`) is used, which guarantees a non-degenerate pairing:

```python
F2e = GF(p2**2, 'i', modulus=x**2 + 1); i = F2e.gen()
E2e = EllipticCurve(F2e, [a, b])
def distort(P):
    x, y = P.xy(); return E2e(-x, i*y)
alpha = G2e.weil_pairing(distort(G2e), n)
beta  = P2e.weil_pairing(distort(G2e), n)

# beta = alpha^k2 в GF(p2^2)* ; порядок гладкий -> Pohlig-Hellman
ord_alpha = alpha.multiplicative_order()
k2_partial = discrete_log(beta, alpha, ord=ord_alpha, operation='*')

# Weil pairing может потерять часть 2-компоненты порядка, так что
# discrete_log даёт k2 только по модулю ord_alpha. Недостающий кофактор
# n/ord_alpha крошечный (делитель 2-части) — добираем полный k2
# коротким перебором (максимум ~16 итераций):
cof = n // ord_alpha
for j in range(cof):
    cand = k2_partial + j * ord_alpha
    if cand * G2 == P2:
        k2 = cand; break
```

The result is `k2`.

**Subtlety (critical for stability):** the Weil pairing `e(G, φ(G))` for a supersingular curve can have order `ord_alpha < n`, losing part of the power of two (`p2+1` contains `2^k`). Therefore `discrete_log` recovers `k2 mod ord_alpha`, and for an unlucky `k2` the full secret is not obtained directly. A short cofactor search recovers the missing bits. Without this step the solver fails on a fraction of random keys.

---

### Layer 3 — flag

```python
key = SHA256(f"{k1}:{k2}")
flag = AES-CBC-decrypt(iv, ct, key)
```

**Flag:** `KubSTU{45_f0r_311ip71c_curv3_g30m37ry_4nd_cryp70gr4phy_1n_g3ner41_1_63l13v3_y0u_w3re_46l3_70_501ve_i7}`
