# L. Lawliet - L

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

`params.txt` 给出 `n = 64`、一个含 64 个权重（每个约 84 位）的列表 `w`，以及 `ciphertexts`——7 个数。你需要从数据中还原出加密方案并取回 flag。

**文件：** [gen.py](../../../assets/Crypto/L.%20Lawliet%20-%20L/gen.py), [solve.py](../../../assets/Crypto/L.%20Lawliet%20-%20L/solve.py), [SECRETS.txt](../../../assets/Crypto/L.%20Lawliet%20-%20L/SECRETS.txt), [截图](../../../assets/Crypto/L.%20Lawliet%20-%20L/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20212314.png)

## 🏁 解答

### 要点
方案（需从数据中还原）：消息先填充，再切成 64 位的块（MSB first），每个块用同一个公钥 `w` 加密为

    c = Σ w[i] · bit[i]   (i = 0..63)

这是一个 **低密度子集和（背包，knapsack）**。其密度为 `d = n / log2(max w) ≈ 64/84 ≈ 0.76`。

### 为什么仅靠 LLL 不够
理论上的 CJLOSS 界 `d < 0.9408` 是渐近的，且假设存在完美的 SVP 预言机。实际上**纯 LLL** 只能可靠地解到大约 `d ≈ 0.64` 的背包（Lagarias–Odlyzko 界）。在 `d ≈ 0.76` 时，LLL 只能找到“垃圾”短向量，真正的 `(±1)` 向量始终浮不出来。需要更强的约化——**BKZ**。

### 解答
对每个块构造一个 CJLOSS 格 `(n+1)×(n+1)`：

```
rows i<n:  [ 2·e_i ,  K·w_i ]
row  n  :  [ 1 … 1 ,  K·s   ]
```

（`K` 是一个大乘子，把求和坐标压到零）。短向量 `(±1, …, ±1, 0)` = `2·bit_i − 1` → 该块的各比特。

```python
from fpylll import IntegerMatrix, LLL, BKZ
K = 1 << 64
def rec(s):
    B = IntegerMatrix(n+1, n+1)
    for i in range(n): B[i,i]=2; B[i,n]=w[i]*K
    for j in range(n): B[n,j]=1
    B[n,n]=s*K
    LLL.reduction(B)
    BKZ.reduction(B, BKZ.Param(block_size=30))   # LLL alone НЕ хватает
    for r in range(n+1):
        row=[B[r,j] for j in range(n+1)]
        if row[n]==0 and all(abs(x)==1 for x in row[:n]):
            for sg in (1,-1):
                bits=[(sg*row[j]+1)//2 for j in range(n)]
                if all(b in (0,1) for b in bits) and sum(w[i]*bits[i] for i in range(n))==s:
                    return bits
```

把全部 7 个块的比特收集起来，转成字节，去掉零填充。

**Flag：** `KubSTU{y0u_n33d_70_6e_4_re41_d373ct1ve_7o_5o1v3_7h15}`
