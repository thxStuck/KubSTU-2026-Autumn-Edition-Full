# It really isn't enough

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

`challenge.txt` hands you two RSA public keys (A and B), an RSA-OAEP-encrypted key, and two AES-GCM ciphertexts. Three layers, each requiring a separate attack, plus several decoys. The name is a direct hint to layer 1: ordinary Wiener **it really isn't enough**. Recover the real flag.

**Files:** [solve.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/solve.sage), [bd_core.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/bd_core.sage), [source_reference.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/source_reference.py), [gen.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.py), [gen.log](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.log)

## 🏁 Solution

### Task structure
Three layers, each requiring a separate attack, plus four false paths.

| Layer / trap | Mechanism | What happens |
|---|---|---|
| Layer 1 (RSA A) | `d ≈ N^0.26` | Wiener is not enough → Boneh-Durfee needed |
| Trap: key B | `d ≈ N^0.24` | Wiener breaks it in a second → `blob` = a taunt |
| Layer 2a (ct1) | AES-GCM, valid tag | fake flag `k3ep_1o0k1ng` |
| Layer 2b (ct2) | AES-GCM, broken tag | naive `decrypt_and_verify` fails |
| Trap: `d` in source | fake constant | the hash yields the wrong key |

The name is a direct hint to layer 1: ordinary Wiener **it really isn't enough**.

### Layer 1 — Boneh-Durfee
Key A has the private exponent `d ≈ N^0.26`:
- Wiener works only for `d < N^0.25` → **does not catch it**;
- Boneh-Durfee works for `d < N^0.292` → **catches it**.

Key B is a decoy with `d ≈ N^0.24`: classic Wiener breaks it instantly, but the `blob` under it decrypts to a taunting string. This cuts off those who reflexively jump on the first familiar pattern (especially LLMs).

**The essence of the attack.** From `e·d ≡ 1 (mod φ)` and `φ = N + 1 − (p+q)` we get an equation with small roots:

```
f(x, y) = 1 + x·(A + y) ≡ 0  (mod e),   A = (N+1)/2,  y ≈ -(p+q)/2
```

`|x| ~ N^delta`, `|y| ~ N^0.5`. We build a lattice from x- and y-shift polynomials (Herrmann–May), reduce with LLL, take the resolvent of two short vectors, find the root → recover `d`, then factor `N` from `(e, d)`.

Decrypting `enc_key` (RSA-OAEP) and `src_ct` (AES-GCM), we obtain `source.py`.

### Layer 2 — nonce reuse + broken tag
`source.py` reveals:
- `key = SHA256(str(d))` — from the **real** `d`. Nearby there is a constant `d = 0x...` with the comment "private exponent" — this is a **fake** (a trap); you must use the `d` obtained from Boneh-Durfee.
- Two GCM ciphertexts with **the same nonce**.

**ct1** — valid tag → decrypts to the fake flag `k3ep_1o0k1ng`. The slopper submits it and gets "wrong".

**ct2** — the same nonce, but the tag is deliberately corrupted. `decrypt_and_verify` throws a `ValueError`. The key insight: **GCM = CTR + GMAC**. Only integrity is broken, not confidentiality — it can be decrypted bypassing the tag:

```python
real = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(ct2[:-16])  # без verify
```

→ the real flag.

```
sage: cd /path/to/folder        # тут challenge.txt, bd_core.sage, solve.sage
sage: load("solve.sage")
```

Pipeline: Boneh-Durfee → `d` → factorization → RSA-OAEP → AES-GCM(source) → parse nonce/ct → `SHA256(str(d))` → `decrypt` without verify on ct2.

Decoy flag (ct1): `KubSTU{7h15_15_n07_7h3_r34l_0n3_k3ep_1o0k1ng}`

**Flag:** `KubSTU{50met1me5_7h3_m057_c0mp13x_7h1ng5_turn_0ut_70_b3_51mpl3_y0u_ju57_n33d_t0_74k3_4_cl053r_lo0k}`
