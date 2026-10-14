# AES Is Secure, Right

> **类别：** Crypto · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

一名实习生用自制密码（`intern_cipher.py`）包裹了 AES-128，并把它的输出留在 `output.txt` 中：密文 `ct` 以及一条透露 PIN 首位数字的提示。AES 密钥由一个 4 位 PIN 派生而来。还原出 flag。

**文件：** [generate.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/generate.py), [solve.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/solve.py), [SECRETS.txt](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/SECRETS.txt)

## 🏁 解答

### 要点
原语本身是老实的——AES-128。弱点在于它周围的一切：密钥由一个 **4 位 PIN**（`sha256(pin)[:16]`）派生，而 `output.txt` 里的提示还告诉了你首位数字。密钥空间坍缩为 1000 种可能——无需攻破 AES，直接按 PIN 暴力枚举即可。

### 分析
`intern_cipher.py` 在加密前做了两件非标准的事：

1. **自定义填充** `prepare()`：把数据填充到 16 的倍数，但填充字节用的是**块数**，而不是填充长度（不是 PKCS#7）。这意味着 `Crypto.Util.Padding.unpad()` 不适用——逆操作我们自己写。
2. **块置换**：先按 `shift = sum(PIN 各位数字) % 块数` 做循环移位，然后把列表翻转。

加密流程：`plaintext → prepare → 分块 → shift → reverse → AES-ECB`。

解法就是对 `2000..2999` 中的每个 PIN 把全部步骤反过来：

```
ciphertext → AES-ECB decrypt → reverse → 逆向 shift → 拼接 → unpad
```

被加密的不是裸 flag，而是一份简短的证书吊销说明（flag 在其中，位于最后一行）——共 9 个块。在 9 个块上 `shift` 确实会取到不同的值，所以必须老老实实地还原这个置换，而不能像只有 2 个块时那样在两种结果里猜一个。

### 解答

```python
from hashlib import sha256
from Crypto.Cipher import AES

def unprepare(d, bs=16):
    tb = len(d)//bs; pb = tb & 0xff; pl = 0
    for b in reversed(d):
        if b != pb: break
        pl += 1
    return None if (pl == 0 or pl > bs) else d[:-pl]

def decrypt(ct, pin):
    c = AES.new(sha256(pin.encode()).digest()[:16], AES.MODE_ECB)
    bl = [c.decrypt(ct[i:i+16]) for i in range(0, len(ct), 16)]
    bl.reverse()
    sh = sum(int(x) for x in pin) % len(bl)
    if sh: bl = bl[-sh:] + bl[:-sh]
    return unprepare(b"".join(bl))

# первая цифра PIN известна из подсказки -> 1000 кандидатов
for rest in range(1000):
    pin = f"2{rest:03d}"
    pt = decrypt(ct, pin)
    if pt and b"KubSTU{" in pt:
        print(pt.decode()); break
```

**Flag：** `KubSTU{c3rt1f1c4t3_r3v0k3d}`
