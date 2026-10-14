# Numbers Station

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

`codes.txt` 中有一行用空格分隔的数字：
`75 117 98 83 84 85 123 ...`

请解码出其中的消息。

**文件：** [gen.py](../../../assets/Crypto/Numbers%20Station/gen.py), [solve.py](../../../assets/Crypto/Numbers%20Station/solve.py)

## 🏁 解答

### 思路
这些是十进制表示的字符 ASCII 码。每个数字是一个字母的编码。提示：`75` = `K`，`117` = `u`，`98` = `b` → 已经能看出 `Kub…`。

### 解答
把每个数字转换成字符：

```python
codes = open("codes.txt").read().split()
flag = "".join(chr(int(x)) for x in codes)
print(flag)
```

**Flag：** `KubSTU{d3c1m4l_15_my_l4n6u4g3}`
