# Do you like reading

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

`reading.txt` is a huge text file. The flag is hidden inside it as byte clusters that stand out from the plain `[a-z\n]` text — each real cluster is a Caesar-shifted fragment of the flag, but most clusters are fakes. Recover the flag.

**Files:** [gen.py](../../../assets/Crypto/Do%20you%20like%20reading/gen.py), [solve.py](../../../assets/Crypto/Do%20you%20like%20reading/solve.py), [gen.log](../../../assets/Crypto/Do%20you%20like%20reading/gen.log)

## 🏁 Solution

### Observations
- The file is too large for a text editor / `less`.
- `tr -d 'a-z\n' < reading.txt | xxd | less` shows inclusions of bytes outside `[a-z\n]` — uppercase, digits, punctuation, control bytes.
- There are many anomalies (~90 clusters), of varying length (from 7 to 20 bytes).
- Most of them are **fakes**. There are only 10 real flag parts.

### Idea
Each real cluster is a part of the flag, encrypted with its own per-byte Caesar shift. The fakes are constructed so that **no** shift produces output within the flag's character range — this breaks the naive "try all clusters" approach.

The order of the real parts in the file = the order in the flag.

### Solution
Three things to understand:
1. The file is enormous → stream processing is needed (mmap is ideal).
2. There are many clusters (far more fakes than real ones) → an anchor is needed: the first part starts with `KubSTU{`, the last ends with `}`.
3. For the middle parts — a filter on the narrow charset `[a-z0-9_]`; in case of ambiguity we pick the shift with the maximum number of underscores (in the real flag they are frequent, in a random shift they are rare).

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

**Flag:** `KubSTU{r34d1n6_r3411y_d0e5_m4k3_my_br4in_w0rk_be77er_but_th1s_t45k_1sn7_0ne_0f_7h0s3_c4535}`
