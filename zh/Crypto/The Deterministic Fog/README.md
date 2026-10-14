# The Deterministic Fog

> **类别：** Crypto (LWE + LCG) · **赛事：** KubSTU CTF 2026 Autumn
> 由 mpei_larpers 团队撰写的详细 writeup（[CTFtime](https://ctftime.org/writeup/41123)）

## 📌 题目

`output.json` 包含矩阵 `A`、`R`，向量 `b`、`ciphertext`，以及参数与校准数据。LWE 参数：40 元的 secret、200 个公开方程、`q=257`、噪声范围 `[-100,100]`。LCG 的状态为 48 位。还原出 flag。

**文件：** [generate.py](../../../assets/Crypto/The%20Deterministic%20Fog/generate.py), [solution_fog.py](../../../assets/Crypto/The%20Deterministic%20Fog/solution_fog.py), [SECRETS.txt](../../../assets/Crypto/The%20Deterministic%20Fog/SECRETS.txt), [截图](../../../assets/Crypto/The%20Deterministic%20Fog/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20234600.png)

## 🏁 解答

### 要点
表面上是老实的 LWE（`n=40, m=200, q=257`，带噪声的系统）。实际上并不需要求解 LWE：噪声是**确定性的**。它的来源是一个公开的**截断 LCG**

```
x_{i+1} = (mult · x_i + inc) mod 2^48      (mult, inc, mod_bits — в output.json)
```

其秘密的 48 位种子为 `x_0`。设备公布了一段简短的**校准轨迹** `calibration`——前 24 个状态的高 8 位（`x_i >> 40`）。由这段轨迹可以**用格**还原出种子（经典的截断 LCG 重构，FHKLLS）。

### 为什么不能“硬碰硬”
- **噪声界 `bound = 100 > q/4 = 64`。** 噪声无法被“舍入掉”，也就是说这**不是**普通的 small-noise LWE——对 LWE 的通用 BDD 攻击不奏效，必须重现确切的噪声流。
- **种子为 48 位** → 暴力 `2⁴⁸` 无望。
- **校准隐藏了每个输出的低 40 位**（只给出高 8 位）→ 暴力低位 `2⁴⁰` 同样无望。只剩下格这一条路。
- 因此通向 flag 的唯一路径必经格，绕不开。

### 分析
**第 1 步。用格还原种子。** 状态关于 `x_0` 是线性的：`x_i = α_i·x_0 + β_i (mod M)`，而 `x_0 = (calib[0]·2⁴⁰) + l_0`，其中 `l_0` 是隐藏的 40 位。由 `x_i = (calib[i]·2⁴⁰) + l_i`、`0 ≤ l_i < 2⁴⁰`，我们在未知量 `(l_0, …)` 上构造格并寻找短向量（LLL）。24 个样本绰绰有余；通过把 LCG 向前跑一遍并比对高位来验证输出。

**第 2 步。重现噪声流。** 从 `x_0` 跑 LCG：校准取状态 `x_0…x_{23}`，工作噪声流从 `x_{24}` 继续（居中处理：`e = x mod 201 − 100`）。前 `m=200` 个值进入 `b`，接下来的 `len(flag)·8` 个进入密文。

**第 3 步。剥离 LWE（现在是线性方程组）。** 已知噪声 `e`，公开样本给出 `A·s = b − e (mod q)`——这是 `F₂₅₇` 上的普通线性方程组，用高斯消元求解（`m=200 ≫ n=40`，解唯一）。

**第 4 步。解密。** 对密文的每一行 `val = (c_j − e_{m+j} − ⟨R_j, s⟩) mod q`；若 `val` 更靠近 `0` 则比特为 `0`，否则为 `1`（编码为 `bit·⌊q/2⌋`）。把比特拼成 flag。

---

### 详细团队 writeup（mpei_larpers）

**要点：** LWE 噪声由一个确定性的 48 位 LCG 产生。校准揭示了前 24 个状态的高 8 位。我们用格还原 seed，重放噪声流，再把噪声从 LWE 系统中剥离。

#### 1. 原始数据
`output.json` 中有矩阵 `A`、`R`，向量 `b`、`ciphertext`，以及参数和校准数据。LWE 参数：40 元的 secret、200 个公开方程、`q=257`、噪声在 `[-100,100]`。LCG 的状态为 48 位。

公开方程：

```text
b[i] = dot(A[i], secret) + noise[i] mod q
```

噪声生成器：

```text
x[i+1] = (mult * x[i] + inc) mod 2^48
noise[i] = x[i] mod 201 - 100
```

`mult` 和 `inc` 已知。只需还原 `x[0]`。

#### 2. 还原 LCG 的初始状态
校准值为 `y[i]=x[i]>>40`。记 `B=2^40`、`M=2^48`。于是：

```text
x[i] = y[i] * B + z[i]
0 <= z[i] < B
```

`z[i]` 是未知的低 40 位。展开递推：

```text
x[i] = A[i] * x[0] + C[i] mod M
```

系数：

```text
A[0] = 1                 C[0] = 0
A[i+1] = A[i] * mult mod M
C[i+1] = C[i] * mult + inc mod M
```

代入 `x[0]=y[0]*B+z[0]`，对每个校准值得到：

```text
A[i] * z[0] + D[i] = k[i] * M + u[i]
0 <= u[i] < B
```

余数 `u[i]` 小于 `B`，于是把该系统表示为一个格，通过 LLL 和 Babai CVP 寻找近向量。用完整的 LCG 运行验证候选，得到：

```text
seed = 194990846919092
```

##### 还原 seed
安装依赖：

```bash
python3 -m pip install fpylll cysignals
```

脚本从压缩包读取校准数据，构造格，只有当所有值都匹配时才接受候选：

```python
import json
from zipfile import ZipFile

from fpylll import CVP, IntegerMatrix, LLL

ARCHIVE = "The Deterministic Fog.zip"
MEMBER = "The Deterministic Fog/output.json"

with ZipFile(ARCHIVE) as archive:
    data = json.loads(archive.read(MEMBER))

sampler = data["sampler"]
mult = sampler["mult"]
inc = sampler["inc"]
M = 1 << sampler["mod_bits"]
B = 1 << sampler["hide"]
ys = data["calibration"]
n = len(ys)

# Коэффициенты в x[i] = A[i]*x[0] + C[i] (mod M).
A, C = [], []
aa, cc = 1, 0
for _ in ys:
    A.append(aa)
    C.append(cc)
    aa = aa * mult % M
    cc = (cc * mult + inc) % M

# После подстановки x[0] = y[0]*B + z[0] получаем
# общую неизвестную z[0] и ограниченные остатки для каждой строки.
D = [(A[i] * ys[0] * B + C[i] - ys[i] * B) % M
     for i in range(n)]

# Базис порождает координаты A[i]*z + k[i]*M и последнюю координату z.
basis = IntegerMatrix(n + 1, n + 1)
for i in range(n):
    basis[i, i] = M
for i in range(n):
    basis[n, i] = A[i]
basis[n, n] = 1

LLL.reduction(basis)
target = [-value for value in D] + [0]
nearest = CVP.babai(basis, target)
low_part = int(nearest[-1])

def calibration(seed):
    x = seed
    trace = []
    for _ in ys:
        trace.append(x >> sampler["hide"])
        x = (mult * x + inc) % M
    return trace

seed = None
for candidate_low in (low_part, -low_part):
    if 0 <= candidate_low < B:
        candidate = ys[0] * B + candidate_low
        if calibration(candidate) == ys:
            seed = candidate
            break

if seed is None:
    raise ValueError("Кандидат решётки не совпал с калибровочной трассой")

print("Recovered seed:", seed)
```

完整的轨迹校验会剔除错误的最近向量。

#### 3. 重建噪声流
先做 24 次转移到达 `x[24]`。然后为 `b` 的 200 行生成噪声，再为 `ciphertext` 的每个比特各生成一个值。顺序必须与题目代码一致。

```python
mask = M - 1
x = seed
for _ in range(sampler["calib"]):
    x = (mult * x + inc) & mask

count = len(data["b"]) + len(data["ciphertext"])
noise = []
for _ in range(count):
    noise.append(
        x % (2 * data["params"]["bound"] + 1)
        - data["params"]["bound"]
    )
    x = (mult * x + inc) & mask
```

现在整条噪声流都已知。

#### 4. 求模 257 下的 LWE secret
从 `b` 中减去前 200 个噪声值。剩下一个线性方程组：

```text
A * secret = b - noise mod 257
```

在域 `F_257` 上用高斯消元求解。矩阵的秩为 40，所以 secret 被唯一确定。

```python
q = data["params"]["q"]
rows = data["A"]
rhs = [
    (value - error) % q
    for value, error in zip(data["b"], noise)
]
n_secret = data["params"]["n"]
matrix = [
    [value % q for value in row] + [target]
    for row, target in zip(rows, rhs)
]

pivots = []
r = 0
for col in range(n_secret):
    pivot = next(
        (i for i in range(r, len(matrix)) if matrix[i][col] % q),
        None,
    )
    if pivot is None:
        continue

    matrix[r], matrix[pivot] = matrix[pivot], matrix[r]
    inverse = pow(matrix[r][col], -1, q)
    matrix[r] = [(value * inverse) % q for value in matrix[r]]

    for i in range(len(matrix)):
        if i != r and matrix[i][col]:
            factor = matrix[i][col]
            matrix[i] = [
                (a - factor * b) % q
                for a, b in zip(matrix[i], matrix[r])
            ]

    pivots.append(col)
    r += 1
    if r == n_secret:
        break

if r != n_secret:
    raise ValueError(f"Неожиданный ранг матрицы: {r}")

secret = [0] * n_secret
for row_index, col in enumerate(pivots):
    secret[col] = matrix[row_index][-1]

# Проверяем найденный секрет во всех 200 публичных уравнениях.
assert all(
    sum(a * b for a, b in zip(row, secret)) % q == value
    for row, value in zip(rows, rhs)
)
```

这个 `assert` 用全部 200 个方程检验 secret。

#### 5. 剥离加密并拼出 flag
每个 `ciphertext` 值编码明文的一个比特。对于比特 `m`、行 `R` 和噪声 `e`，加密计算为：

```text
c = dot(R, secret) + e + m*(q//2) mod q
```

从 `c` 中减去已知的 `dot(R, secret)` 和噪声 `e`。余数为 `0` 表示比特 0，`128` 表示比特 1。字节按从高位到低位拼接。

```python
bit_errors = noise[len(data["b"]):]
bits = []

for value, row, error in zip(
    data["ciphertext"], data["R"], bit_errors
):
    phase = (
        value
        - sum(a * b for a, b in zip(row, secret))
        - error
    ) % q
    bits.append(1 if q // 4 < phase < 3 * q // 4 else 0)

plaintext = bytes(
    sum(bits[offset + j] << (7 - j) for j in range(8))
    for offset in range(0, len(bits), 8)
)
flag = plaintext.decode("ascii")

assert flag.startswith("KubSTU{") and flag.endswith("}")
print(flag)
```

结果：

```text
KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}
```

#### 结果验证
1. seed 能重现全部 24 个 `calibration` 值。
2. secret 满足 200 个 LWE 方程。
3. 每个清理后的比特都等于 `0` 或 `128`。
4. 字节构成形如 `KubSTU{...}` 的 ASCII flag。

**漏洞成因：** 噪声是确定性的，而校准部分地暴露了 LCG 状态。

**Flag：** `KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}`
