# Shiffted

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

`cipher.txt` 中只有一行：`RbiZAB{j43z4y_d0bsk_i3_wy0bk}`

还原出 flag。

**文件：** [gen.py](../../../assets/Crypto/Shiffted/gen.py), [solve.py](../../../assets/Crypto/Shiffted/solve.py)

## 🏁 解答

### 思路
这是凯撒密码（位移）：每个字母在字母表中被固定地移动了若干位。数字、花括号和下划线保持不变。

提示一眼可见：flag 以 `KubSTU{` 开头，而密文以 `RbiZAB{` 开头。所以 `R→K`、`b→u`、……——位移处处相同。`R`(17) → `K`(10)：向后位移 7。

### 解答
把每个字母向后移 7 位。或者干脆遍历全部 26 种位移，取出能得到 `KubSTU{` 的那个：

```python
def caesar(t, s):
    r = ""
    for c in t:
        if c.isupper(): r += chr((ord(c)-65+s)%26+65)
        elif c.islower(): r += chr((ord(c)-97+s)%26+97)
        else: r += c
    return r

enc = open("cipher.txt").read().strip()
for s in range(26):
    g = caesar(enc, -s)
    if g.startswith("KubSTU{"):
        print(g); break
```

**Flag：** `KubSTU{c43s4r_w0uld_b3_pr0ud}`
