# Curve Ball

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

一条由两条紧密耦合的椭圆曲线组成的链（外加一条诱饵曲线 C3），以及一个 AES 加密的 flag。每一层都是一个独立且非平凡的攻击，整条链只能严格按顺序求解。还原出 flag。

**文件：** [gen.py](../../../assets/Crypto/Curve%20Ball/gen.py), [solve.sage](../../../assets/Crypto/Curve%20Ball/solve.sage), [gen.log](../../../assets/Crypto/Curve%20Ball/gen.log), [截图](../../../assets/Crypto/Curve%20Ball/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-02%20022018.png)

## 🏁 解答

### 概览
两条紧密耦合的椭圆曲线组成的链。每一层都是独立、非平凡的攻击。只能顺序求解才能完整解出。

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

诱饵：C3 是一条普通曲线，玩家可能会尝试攻击它，但它并不通向 flag（任何一种攻击在它上面都得不到有用的结果）。

---

### 第 0 层 — 识别
C1 以**完整的 Weierstrass 形式**给出：`y² + a1·xy + a3·y = x³ + a2·x² + a4·x + a6`。玩家把它化为短形式 `y² = x³ + Ax + B`（标准 b/c-不变量），并计算其阶（Sage 中的 `E.order()`）。

关键观察：**#E1 = p1**。这是一条异常（anomalous）曲线，对它而言 ECDLP 可通过 Smart's attack 在线性时间内解出。若不计算阶，这条曲线看上去就像一个普通的、无法 lift 的 256 位 ECDLP——这正是第 0 层的陷阱。

---

### 第 1 层 — Smart's attack (SSSA)
对于异常曲线（`#E = p`），通过 lift 到 p-adic 域 `Q_p` 并使用形式对数，存在到加法群 `F_p` 的同构。

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

结果是 `k1`，即 C1 的秘密标量。

---

### 各层之间的衔接
C2 的参数以 AES-CBC 加密，密钥由 `k1` 派生：

```python
key1 = SHA256(b"C1->C2:" + str(k1).encode())
plaintext = JSON {p2, a, b, G2, P2}
```

没有对 C1 的 Smart's attack，就拿不到 C2 的参数——暴力枚举 k1（258 位）是不可能的。这使整条链严格顺序化。

---

### 第 2 层 — MOV attack
解密后，C2 原来是 supersingular 的：在 `p2 ≡ 3 (mod 4)` 上的 `y² = x³ + x`，`#E2 = p2 + 1`，embedding degree 2。其阶是 **smooth（光滑）** 的（刻意构造），所以转移之后 DLP 可解。

MOV 通过 Weil 配对把 ECDLP 转移到 `GF(p2²)*`。它不随机搜索辅助点，而是使用一个 **distortion map** `φ(x,y) = (−x, i·y)`（其中 `i² = −1`），从而保证配对非退化：

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

结果是 `k2`。

**微妙之处（对稳定性至关重要）：** 对 supersingular 曲线，Weil 配对 `e(G, φ(G))` 的阶可能是 `ord_alpha < n`，从而丢失了 2 的幂的一部分（`p2+1` 含有 `2^k`）。因此 `discrete_log` 只能还原 `k2 mod ord_alpha`，当碰到不走运的 `k2` 时无法直接得到完整的 secret。一次简短的余因子搜索补齐缺失的比特。没有这一步，solver 会在一部分随机密钥上失败。

---

### 第 3 层 — flag

```python
key = SHA256(f"{k1}:{k2}")
flag = AES-CBC-decrypt(iv, ct, key)
```

**Flag：** `KubSTU{45_f0r_311ip71c_curv3_g30m37ry_4nd_cryp70gr4phy_1n_g3ner41_1_63l13v3_y0u_w3re_46l3_70_501ve_i7}`
