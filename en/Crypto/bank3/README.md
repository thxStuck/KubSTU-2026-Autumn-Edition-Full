# bank3

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

A Telegram "bank" bot. It can:

- `/register <name>` — open an account and receive a "certificate" (`.cert`);
- the **"Certificates"** button — issue as many certificates as you like, including **many for one account** (a built-in hint: "you need many signatures" ⇒ crypto, not web);
- `/login` — send a `.cert`; logging in under the **`admin`** account **= the flag**;
- you **cannot** register `admin` directly.

Certificate format:

```
-----BEGIN KUBSTU BANK CERTIFICATE-----
account:   KB-319D02F03C
issued:    1791579938
signature: base64( r || s )     # по 32 байта
-----END KUBSTU BANK CERTIFICATE-----
```

The `signature` is an **ECDSA signature (secp256k1)** over the account name (`e = sha256(name) mod n`), `account_id = base64(r‖s)`.

Win condition: present a valid signature for `admin` (which cannot be registered) ⇒ you must **recover the server's private key** and sign `admin` yourself.

**Files:** [solve_blackbox.py](../../../assets/Crypto/bank3/solve_blackbox.py)

## 🏁 Solution

### Vulnerability
The server's key `d` is constant. The weakness is in the **nonce**: it is not fully random, but assembled from three parts:

```
k = prefix·2^253  +  core·2^3  +  postfix
     └ 3 бита ┘       └ 250 бит ┘   └ 3 бита ┘
```

- `prefix` (the top 3 bits) and `postfix` (the bottom 3 bits) are deterministic from the account name (`sha256("prefix:"+name)%8`, `sha256("postfix:"+name)%8`);
- only the middle **250 bits** are random (`core`, a fresh CSPRNG for each signature).

That gives **6 structured (non-random) bits in the nonce** ⇒ a classic **Hidden Number Problem (HNP)** on a biased ECDSA nonce. The 250 random bits cannot be brute-forced, but the 6 "leaked" bits are enough to recover `d` with a lattice.

For **all** signatures of one account, `prefix` and `postfix` are **identical** (the name is the same) — so the attack can be carried out by collecting signatures **from a single account** (which the bot allows).

### Reduction to HNP
For a signature: `s·k = e + r·d (mod n)`. Substituting `k = prefix·2^253 + core·8 + postfix` and denoting the known part `Aabs = prefix·2^253 + postfix`:

```
core = (s^-1·e − Aabs)·8^-1  +  (s^-1·r·8^-1)·d      (mod n),   0 ≤ core < 2^250
     =          B_i          +         A_i · d
```

This is HNP: we look for `d` such that all `core_i = A_i·d + B_i (mod n)` are small (`< 2^250`). We build a Boneh–Venkatesan lattice, reduce it, and read `d` from a short vector.

**Custom twist (anti-slop):** both the high and the low bits are known, but the middle is unknown — because of the low bits a factor of `8^-1` appears in `A_i, B_i`. A stock MSB-only HNP solver from the internet sets the lattice up incorrectly; the linearization has to be derived by hand. The public key is **not needed** — `d` is verified structurally (all `core_i < 2^250`).

### The player's path (no source, black box)
There is no source, `prefix/postfix` are unknown, the nonce itself is not visible. But:

1. Recognize `signature` = `r‖s` ⇒ ECDSA/secp256k1, the name is signed (`e = sha256(name)`).
2. Collect **many signatures from one account** (≥ ~70, 120+ with margin).
3. Check for repeated `r` — there is none ⇒ not nonce reuse, but a **biased nonce**.
4. Key insight: the nonce has a **fixed but unknown** part in the high/low bits, identical across the whole set (one account). There are few such bits ⇒ they can be **brute-forced**, and the hypothesis verified **structurally** (all `core_i` must come out `< 2^250`) — without even contacting the bot.
5. Sweep over small `(a, c)` (how many fixed high/low bits) and over all `2^(a+c)` values of the offset `Aabs`; on the correct hypothesis the lattice yields `d`.
6. Sign `admin` with the key `d`, assemble the `.cert`, send `/login` → the flag.

### Reference and numbers (verified)
**If the structure is known** (internal check, `admin/solve.py`): a balanced/recentered basis, **plain LLL is enough** (BKZ not required, only a fallback):
- threshold: ~70 signatures with pure LLL (8/8 in tests), ~50 with a BKZ fallback;
- time: **~2.5 s** on 120 signatures; recovery of `d` → forging `admin`.

**Black box** (as for the player): a brute-force of `2^(3+3)=64` offsets inside the lattice, accepted by the structural bound on `core`:
- time: **~60 s**, recovers the same `d`.

**Verified on the live TG bot:** 151 certificates from one account (`KB-319D02F03C`) → key recovered (black box) → the forged `admin.cert` accepted by the bot → the flag. So the task is solvable exactly in the form the players receive it.

```python
# ядро решётки (сбалансированный базис; plain LLL)
M = IntegerMatrix(m+2, m+2); F = 1<<7; Kh = (1<<250)>>1
for i in range(m): M[i,i] = N*F
for j in range(m):
    M[m,j]   = A[j]*F
    M[m+1,j] = ((B[j]-Kh) % N)*F
M[m,m] = 1; M[m+1,m+1] = Kh*F
LLL.reduction(M)                      # BKZ только если LLL не дал d
# d читается из строки с |last| == Kh*F; валидация: все (A_i d + B_i) % N < 2^250
```
