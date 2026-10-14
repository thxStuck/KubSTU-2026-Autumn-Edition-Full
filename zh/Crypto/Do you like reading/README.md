# Do you like reading

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

`reading.txt` 是一个巨大的文本文件。flag 以字节簇的形式藏在其中，这些字节簇在普通的 `[a-z\n]` 文本中显得格格不入——每个真实的簇都是 flag 的一个片段，用各自的凯撒位移加密，但大多数簇都是假的。还原出 flag。

**文件：** [gen.py](../../../assets/Crypto/Do%20you%20like%20reading/gen.py), [solve.py](../../../assets/Crypto/Do%20you%20like%20reading/solve.py), [gen.log](../../../assets/Crypto/Do%20you%20like%20reading/gen.log)

## 🏁 解答

### 观察
- 文件太大，文本编辑器 / `less` 打不开。
- `tr -d 'a-z\n' < reading.txt | xxd | less` 会显示 `[a-z\n]` 之外的字节——大写字母、数字、标点、控制字节。
- 异常很多（约 90 个簇），长度不一（7 到 20 字节）。
- 其中大多数是**假的**。真正的 flag 片段只有 10 个。

### 思路
每个真实的簇都是 flag 的一部分，用各自的逐字节凯撒位移加密。假簇被构造成：**任何**位移都无法产生落在 flag 字符范围内的输出——这就破坏了朴素的“遍历所有簇”的做法。

真实片段在文件中的顺序 = 它们在 flag 中的顺序。

### 解答
需要理解三点：
1. 文件巨大 → 需要流式处理（mmap 最理想）。
2. 簇很多（假簇比真簇多出数倍）→ 需要锚点：第一段以 `KubSTU{` 开头，最后一段以 `}` 结尾。
3. 对于中间的片段——用狭窄的字符集 `[a-z0-9_]` 过滤；当有歧义时，选取下划线数量最多的位移（真实 flag 里下划线频繁，随机位移里罕见）。

```python
import mmap, re

CORE  = set(b"abcdefghijklmnopqrstuvwxyz0123456789_")
CLOSE = CORE | {ord("}")}
HEAD, TAIL = b"KubSTU{", b"}"

def dec(blob, s): return bytes((b - s) % 256 for b in blob)

# 1. Поиск кластеров: mmap + regex по всему файлу.
#    Ядро само подгрузит нужные страницы, ничего не держим в RAM целиком.
clusters = []
with open("reading.txt", "rb") as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        for match in re.finditer(rb"[^a-z\n\r ]+", m):
            clusters.append((match.start(), match.group()))

# 2. HEAD: первый кластер, декодящийся во что-то с префиксом KubSTU{
head_i, head_dec = None, None
for i, (_, blob) in enumerate(clusters):
    for s in range(256):
        d = dec(blob, s)
        if d.startswith(HEAD):
            head_i, head_dec = i, d; break
    if head_i is not None: break

# 3. TAIL: последний кластер, декодящийся во что-то с суффиксом }
tail_i, tail_dec = None, None
for i in range(len(clusters) - 1, -1, -1):
    _, blob = clusters[i]
    for s in range(256):
        d = dec(blob, s)
        if d.endswith(TAIL) and all(c in CLOSE for c in d):
            tail_i, tail_dec = i, d; break
    if tail_i is not None: break

# 4. MIDDLE: между head и tail оставляем только кластеры с валидным
# CORE-декодом. Фейки естественно отфильтруются (нет валидного сдвига).
# Среди валидных сдвигов выбираем с максимумом подчёркиваний.
middle = []
for i in range(head_i + 1, tail_i):
    _, blob = clusters[i]
    best = None
    for s in range(1, 256):
        d = dec(blob, s)
        if all(c in CORE for c in d):
            score = d.count(b"_")
            if best is None or score > best[0]:
                best = (score, d)
    if best: middle.append(best[1])

print((head_dec + b"".join(middle) + tail_dec).decode())
```

**Flag：** `KubSTU{r34d1n6_r3411y_d0e5_m4k3_my_br4in_w0rk_be77er_but_th1s_t45k_1sn7_0ne_0f_7h0s3_c4535}`
