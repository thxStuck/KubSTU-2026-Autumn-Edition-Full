# It really isn't enough

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

`challenge.txt` 给了你两个 RSA 公钥（A 和 B）、一个用 RSA-OAEP 加密的密钥，以及两段 AES-GCM 密文。共三层，每层都需要不同的攻击，外加若干诱饵。题名正是对第 1 层的直接提示：普通的 Wiener **it really isn't enough**（确实不够）。还原出真正的 flag。

**文件：** [solve.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/solve.sage), [bd_core.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/bd_core.sage), [source_reference.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/source_reference.py), [gen.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.py), [gen.log](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.log)

## 🏁 解答

### 题目结构
三层，每层都需要不同的攻击，外加四条错误路径。

| 层 / 陷阱 | 机制 | 发生了什么 |
|---|---|---|
| 第 1 层 (RSA A) | `d ≈ N^0.26` | Wiener 不够 → 需要 Boneh-Durfee |
| 陷阱：密钥 B | `d ≈ N^0.24` | Wiener 一秒就破 → `blob` = 一句嘲讽 |
| 第 2a 层 (ct1) | AES-GCM，有效 tag | 假 flag `k3ep_1o0k1ng` |
| 第 2b 层 (ct2) | AES-GCM，tag 被破坏 | 朴素的 `decrypt_and_verify` 会失败 |
| 陷阱：source 里的 `d` | 假常量 | 哈希得出错误的密钥 |

题名正是对第 1 层的直接提示：普通的 Wiener **it really isn't enough**。

### 第 1 层 — Boneh-Durfee
密钥 A 的私有指数 `d ≈ N^0.26`：
- Wiener 只在 `d < N^0.25` 时有效 → **拿不下**；
- Boneh-Durfee 在 `d < N^0.292` 时有效 → **拿得下**。

密钥 B 是诱饵，`d ≈ N^0.24`：经典 Wiener 瞬间攻破，但它下面的 `blob` 解密出来是一句嘲讽字符串。这就筛掉了那些条件反射般扑向第一个熟悉套路的人（尤其是 LLM）。

**攻击要义。** 由 `e·d ≡ 1 (mod φ)` 和 `φ = N + 1 − (p+q)`，得到一个具有小根的方程：

```
f(x, y) = 1 + x·(A + y) ≡ 0  (mod e),   A = (N+1)/2,  y ≈ -(p+q)/2
```

`|x| ~ N^delta`，`|y| ~ N^0.5`。我们用 x-shift 和 y-shift 多项式（Herrmann–May）构造格，用 LLL 约化，取两个短向量的结式，求出根 → 还原 `d`，然后由 `(e, d)` 分解 `N`。

解密 `enc_key`（RSA-OAEP）和 `src_ct`（AES-GCM），得到 `source.py`。

### 第 2 层 — nonce 重用 + 被破坏的 tag
`source.py` 显示：
- `key = SHA256(str(d))` — 用的是**真正的** `d`。旁边有一个常量 `d = 0x...`，注释写着 "private exponent" — 这是**假的**（陷阱）；必须使用从 Boneh-Durfee 得到的 `d`。
- 两段使用**同一 nonce** 的 GCM 密文。

**ct1** — tag 有效 → 解密出假 flag `k3ep_1o0k1ng`。乱做的人把它交上去，得到“错误”。

**ct2** — 同一 nonce，但 tag 被故意破坏。`decrypt_and_verify` 会抛出 `ValueError`。关键认识：**GCM = CTR + GMAC**。被破坏的只是完整性，而非机密性——可以绕过 tag 进行解密：

```python
real = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(ct2[:-16])  # без verify
```

→ 真正的 flag。

```
sage: cd /path/to/folder        # тут challenge.txt, bd_core.sage, solve.sage
sage: load("solve.sage")
```

流水线：Boneh-Durfee → `d` → 分解 → RSA-OAEP → AES-GCM(source) → 解析 nonce/ct → `SHA256(str(d))` → 对 ct2 不做 verify 的 `decrypt`。

诱饵 flag (ct1)：`KubSTU{7h15_15_n07_7h3_r34l_0n3_k3ep_1o0k1ng}`

**Flag：** `KubSTU{50met1me5_7h3_m057_c0mp13x_7h1ng5_turn_0ut_70_b3_51mpl3_y0u_ju57_n33d_t0_74k3_4_cl053r_lo0k}`
