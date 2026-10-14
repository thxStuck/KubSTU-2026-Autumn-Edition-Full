# default

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

`output.txt` 中有两个大数——RSA 模数 `n` 和密文 `c`。公钥指数 `e` 未给出。还原出明文。

**文件：** [solve.py](../../../assets/Crypto/default/solve.py)

## 🏁 解答

### 观察
- 两个大数 + 名字 "Default" → 这是无填充的 RSA。
- `e` 未给出 → 很可能它很小（否则何必隐藏）。
- 小指数的经典候选：`3, 5, 7, 11, 13, 17`。

### 漏洞
对单个密文的小指数攻击（无填充的 Håstad 攻击的特例）。

如果消息 `m` 足够短，那么 `m^e < n`，模幂运算实际上不会发生取模回绕：

```
c = m^e mod n = m^e   (因为 m^e < n)
```

因此要还原 `m`，只需对 `c` 取普通的整数 `e` 次方根即可。

量级检查：flag ≈ 480 位，`n` = 4096 位 → 当 `e ∈ {3, 5, 7}` 时 `m^e < n`。

### 解答
遍历较小的 `e`，对每个尝试取整数开方并检查 flag 格式：

```python
from Crypto.Util.number import long_to_bytes
import gmpy2

# from output.txt: n, c
for e in [3, 5, 7, 11, 13, 17, 19, 23]:
    m, exact = gmpy2.iroot(c, e)
    if not exact:
        continue
    try:
        flag = long_to_bytes(int(m)).decode()
    except UnicodeDecodeError:
        continue
    if "KubSTU{" in flag:
        print(f"e = {e}")
        print(flag)
        break
```
