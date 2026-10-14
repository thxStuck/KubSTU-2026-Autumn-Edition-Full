# bank3

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

一个 Telegram “银行”机器人。它可以：

- `/register <名字>` — 开户，领取一张“证书”（`.cert`）；
- **“Certificates”** 按钮 — 想签发多少证书就签发多少，包括**对同一个账户签发多张**（一个内置提示：“你需要很多签名” ⇒ 密码学，而非 Web）；
- `/login` — 提交一张 `.cert`；以 **`admin`** 账户登录 **= flag**；
- **无法**直接注册 `admin`。

证书格式：

```
-----BEGIN KUBSTU BANK CERTIFICATE-----
account:   KB-319D02F03C
issued:    1791579938
signature: base64( r || s )     # по 32 байта
-----END KUBSTU BANK CERTIFICATE-----
```

`signature` 是对账户名的一个 **ECDSA 签名（secp256k1）**（`e = sha256(name) mod n`），`account_id = base64(r‖s)`。

获胜条件：为 `admin`（无法注册）出示一个有效签名 ⇒ 你必须**还原出服务器的私钥**，自己给 `admin` 签名。

**文件：** [solve_blackbox.py](../../../assets/Crypto/bank3/solve_blackbox.py)

## 🏁 解答

### 漏洞
服务器的密钥 `d` 是固定的。弱点在于 **nonce**：它并非完全随机，而是由三部分拼成：

```
k = prefix·2^253  +  core·2^3  +  postfix
     └ 3 бита ┘       └ 250 бит ┘   └ 3 бита ┘
```

- `prefix`（高 3 位）和 `postfix`（低 3 位）由账户名确定（`sha256("prefix:"+name)%8`、`sha256("postfix:"+name)%8`）；
- 只有中间的 **250 位**是随机的（`core`，每次签名用一次全新的 CSPRNG）。

于是 nonce 中有 **6 个结构化（非随机）比特** ⇒ 一个经典的、针对有偏 ECDSA nonce 的 **Hidden Number Problem (HNP)**。250 个随机比特无法暴力枚举，但这 6 个“泄露”比特已足以用格还原 `d`。

对于同一账户的**所有**签名，`prefix` 和 `postfix` 都**相同**（名字一样）——所以可以通过**从单个账户**收集签名来实施攻击（而机器人正好允许这样做）。

### 归约到 HNP
对一个签名：`s·k = e + r·d (mod n)`。代入 `k = prefix·2^253 + core·8 + postfix`，并把已知部分记为 `Aabs = prefix·2^253 + postfix`：

```
core = (s^-1·e − Aabs)·8^-1  +  (s^-1·r·8^-1)·d      (mod n),   0 ≤ core < 2^250
     =          B_i          +         A_i · d
```

这就是 HNP：我们寻找使所有 `core_i = A_i·d + B_i (mod n)` 都很小（`< 2^250`）的 `d`。构造一个 Boneh–Venkatesan 格，约化，从一个短向量中读出 `d`。

**自定义变体（反套路）：** 高位和低位都已知，中间未知——由于低位，`A_i, B_i` 中出现了一个 `8^-1` 因子。网上常见的仅处理 MSB 的 HNP solver 会把格建错；线性化必须自己推导。公钥**不需要**——`d` 以结构方式验证（所有 `core_i < 2^250`）。

### 玩家的路径（无源码，黑盒）
没有源码，`prefix/postfix` 未知，nonce 本身也看不见。但是：

1. 认出 `signature` = `r‖s` ⇒ ECDSA/secp256k1，签的是名字（`e = sha256(name)`）。
2. **从一个账户**收集**大量签名**（≥ ~70，留余量 120+）。
3. 检查 `r` 是否重复——没有 ⇒ 不是 nonce 重用，而是**有偏 nonce**。
4. 关键洞见：nonce 的高/低位有一个**固定但未知**的部分，在整组数据中保持一致（同一账户）。这类比特很少 ⇒ 可以**暴力枚举**，并用**结构方式**验证假设（所有 `core_i` 都应得出 `< 2^250`）——甚至无需联系机器人。
5. 在较小的 `(a, c)`（固定了多少高/低位）以及偏移 `Aabs` 的所有 `2^(a+c)` 个取值上扫描；在正确假设下，格会给出 `d`。
6. 用密钥 `d` 给 `admin` 签名，拼出 `.cert`，发送 `/login` → flag。

### 基准与数据（已验证）
**若结构已知**（内部检查，`admin/solve.py`）：平衡 / 重新居中的基，**纯 LLL 就够了**（不必 BKZ，仅作回退）：
- 阈值：纯 LLL 约需 ~70 个签名（测试中 8/8），带 BKZ 回退约 ~50 个；
- 耗时：120 个签名上 **~2.5 秒**；还原 `d` → 伪造 `admin`。

**黑盒**（和玩家一样）：在格内部暴力枚举 `2^(3+3)=64` 个偏移，用 `core` 的结构上界来接受：
- 耗时：**~60 秒**，还原出同一个 `d`。

**在真实 TG 机器人上验证：** 从一个账户（`KB-319D02F03C`）取 151 张证书 → 还原密钥（黑盒）→ 伪造的 `admin.cert` 被机器人接受 → flag。也就是说，这道题在玩家拿到它的形态下确实可解。

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
