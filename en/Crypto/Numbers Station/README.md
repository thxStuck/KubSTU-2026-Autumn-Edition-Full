# Numbers Station

> **Category:** Crypto · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

`codes.txt` contains a single line of space-separated numbers:
`75 117 98 83 84 85 123 ...`

Decode the message.

**Files:** [gen.py](../../../assets/Crypto/Numbers%20Station/gen.py), [solve.py](../../../assets/Crypto/Numbers%20Station/solve.py)

## 🏁 Solution

### Idea
These are ASCII codes of characters in decimal. Each number is the code of a single letter. Hint: `75` = `K`, `117` = `u`, `98` = `b` → you can already read `Kub…`.

### Solution
Convert each number to a character:

```python
codes = open("codes.txt").read().split()
flag = "".join(chr(int(x)) for x in codes)
print(flag)
```

**Flag:** `KubSTU{d3c1m4l_15_my_l4n6u4g3}`
