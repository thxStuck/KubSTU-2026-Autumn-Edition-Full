# What do you know about Perelman

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

给你三个文件：
- `cascade.py` — `F_p` 上椭圆曲线模空间上的“离散 Ricci 流”代码。它固定 `p = 4003`、`N = 30`、`η = 1`。
- `curve.png` — 最终曲线 `E_N` 各点的 4003×4003 散点图，被噪声、两条**诱饵曲线**和白色“空洞”所污染。
- `encrypted.txt` — AES-CBC 加密 flag 的 `iv`、`ct`，**以及明确给出的密钥派生方案**（带参数的 scrypt）。

**文件：** [gen.py](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/gen.py), [solve.py](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/solve.py), [gen.log](../../../assets/Crypto/What%20do%20you%20know%20about%20Perelman/gen.log)

## 🏁 解答

### 观察
`cascade.py` 里的 docstring 堆砌了一大堆关于 Ricci flow / Perelman / surgery 的数学术语——这都是**幌子**。就代码而言，`ricci_step` 不过是模 `p` 的一对多项式更新，由一个共享的“曲率” `K = 4a³ + 27b²`（判别式）联系起来。唯一能当作密钥的 secret 是 `(a₀, b₀)`；级联 `(a₀,b₀) → (a_N,b_N)` 是确定性的。

### 第 1 步 — 从 PNG 中提取点
`F_p` 上的每个点 `E_N: y² = x³ + a·x + b` 都是一个变暗的 3×3 标记。标记的中心 = 8 个邻居全为暗色的像素（3×3 腐蚀 erosion）。

```python
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
img = np.array(Image.open("curve.png"))
centers = binary_erosion(img < 128, structure=np.ones((3, 3)))
ys, xs = np.where(centers)
points = list(zip(xs.tolist(), ys.tolist()))
```

### 第 2 步 — 由点还原 `(a_N, b_N)`（RANSAC）
由两个点可唯一解出 `(a, b)`：

```
a = ((y₁² - y₂²) - (x₁³ - x₂³)) · (x₁ - x₂)⁻¹  (mod p)
b = y₁² - x₁³ - a·x₁                              (mod p)
```

我们尝试许多随机点对，取内点（inliers）最多的那条曲线。**诱饵曲线**画得很稀疏（约 35 % 的点），所以真正的 `E_N` 内点明显更多（参考实现中为 3562，而诱饵约 1400），RANSAC 能可靠地选中它。噪声（约 2500 个点）和 55 个“空洞”降低了内点比例，所以需要更多点对（几千次试验）。

### 第 3 步 — 对原像做前向搜索
级联是不可分离的（`a` 的更新依赖 `b`，反之亦然），因此不能按坐标分别求解——必须枚举点对。点对总数 `p² = 16 032 009`，每对迭代 `N = 30` 次；用 numpy 大约 30 秒：

```python
a = np.arange(p, dtype=np.int64)[:, None].repeat(p, axis=1)
b = np.arange(p, dtype=np.int64)[None, :].repeat(p, axis=0)
for _ in range(N):
    Kv = (4 * ((a*a) % p) * a + 27 * ((b*b) % p)) % p
    a, b = (a - 12*((a*a) % p)*Kv) % p, (b - 54*b*Kv) % p
cand = list(zip(*np.where((a == aN) & (b == bN))))   # ~10-30 прообразов
```

### 第 4 步 — 解密（慢速 KDF）
密钥来自一个**慢速、内存困难（memory-hard）的 KDF**，方案已在 `encrypted.txt` 中公布：

```
key = scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
             salt=b'perelman/ricci/v2', n=65536, r=8, p=1, dklen=32)
```

scrypt **只对少数几个原像**（参考实现中 20 个）施加——每个约 0.2 秒，总共几秒：

```python
for a0, b0 in cand:
    key = hashlib.scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
                         salt=SALT, n=65536, r=8, p=1, maxmem=256*1024*1024, dklen=32)
    try:
        pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
        if pt.startswith(b"KubSTU{"): print(pt.decode()); break
    except ValueError: pass
```

**Flag：** `KubSTU{45_a_m4773r_0f_f4c7_h3_b3c4m3_7he_f1r57_p3rs0n_to_s01v3_0n3_0f_th3_m1ll3nn1um_pr1z3_pr0bl3m5}`
