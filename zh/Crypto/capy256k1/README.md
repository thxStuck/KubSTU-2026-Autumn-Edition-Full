# capy256k1

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

实验室没有采用标准的 secp256k1，而是在 `capy256k1.py` 中提供了自己的 256 位曲线，并配有 `output.json`，其中含若干诊断点，以及每个点对应的结果点 `R = secret · point`。还原出 secret 并解密 flag。

**文件：** [generate.py](../../../assets/Crypto/capy256k1/generate.py), [solve.py](../../../assets/Crypto/capy256k1/solve.py), [SECRETS.txt](../../../assets/Crypto/capy256k1/SECRETS.txt)

## 🏁 解答

### 要点
`capy256k1.py` 里自制的运算**从不检查点是否在曲线上**。这是经典的 **invalid curve attack（无效曲线攻击）**。

实验室提供的不是标准 secp256k1，而是自己的 256 位曲线（`a = 0`，自带一个特殊形式 `2²⁵⁵ + c` 的素数 `p`）。关键区别在于：**该素数并非 twist-secure**。对于 j-不变量为 0 的曲线，其六次扭曲 `y² = x³ + b` 的阶是六种之一，由 CM 表示 `4p = L² + 27M²` 决定。对于这个 `p`，有几条扭曲携带一个**素数阶 `q` 位于 2³⁴…2³⁹ 范围内**的子群。

`output.json` 中有若干诊断点，每个点对应结果点 `R = secret · point`。这些点并不在基曲线上，而在这些弱扭曲上。

这里子群被刻意抬到 2³⁴…2³⁹ 范围。线性扫描（`q` 次运算）意味着数十亿次点加法，在纯 Python 中要耗时数小时到数天——也就是说**暴力枚举行不通**。需要一整套真正的工具链：

1. **识别无效曲线**——没有 on-curve 检查。
2. 对每个点**读出 `b = y² − x³ (mod p)`**（`a = 0`）。
3. **不用 Sage 计算扭曲的阶**——CM 方法 `4p = L² + 27M²`（cornacchia 给出 `(L, M)`，由此得到六个候选阶）；选出能湮灭该点的那个。
4. **提取 `q`**——对阶做因式分解（试除 + Pollard rho / ECM），找出满足 `q·point = O` 的素因子。
5. **在子群 ⟨point⟩ 中求 ECDLP**——baby-step/giant-step（或 Pollard rho / kangaroo），`O(√q) ≈ 2¹⁷…2²⁰`，从 `R = secret·point` 得出 `secret mod q`。
6. 对四个余数做 **CRT**。

secret 为 128 位；四个 `q` 的乘积给出一个 **142 位**的 CRT 模数 `> 2¹²⁸`，故取值唯一。随后执行 `decrypt_flag(secret, ciphertext)`。

Sage 可以加速第 3–5 步，但**并非必需**：整条路径都能用纯 Python 走通（cornacchia + rho + BSGS + CRT）。

### 解答

```
    point 0: b=2, q=11799928573 (~2^34), secret mod q = 3679953973
    point 1: b=3, q=90287601949 (~2^37), secret mod q = 26161617092
    point 2: b=4, q=354690454903 (~2^39), secret mod q = 223611984189
    point 3: b=5, q=11472381409 (~2^34), secret mod q = 8003312562
[+] secret recovered (~40s): 206229994785984600850531915192031064515
[+] flag: KubSTU{1t_l00k3d_str41ght_1n_d3v}
```

**Flag：** `KubSTU{1t_l00k3d_str41ght_1n_d3v}`
