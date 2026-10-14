# BRO, SORRY

> **类别：** Hardware / Stego · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

工厂的噪声已经平息，但有些东西仍在以自己的频率运转。找出隐藏的 flag。

Flag 格式：`KubSTU{...}`。

**文件：** [bro_stego_with_hint.png](../../../assets/STEGO/BRO,%20SORRY/bro_stego_with_hint.png)

## 🏁 解答

首先应使用标准的隐写工具检查题目文件。特别是，查看 PNG 的元数据很有用：

```bash
exiftool bro_stego_with_hint.png
```

元数据中有一条提示：

```text
stego_hint: key-bro
comment: Look into 8x8 frequency blocks
```

由提示可知，密钥是 `bro`，并且需要在被切分成 8×8 块的图像的频域表示中查找数据。

### DCT 隐写

对图像的每个块计算**离散余弦变换**（DCT）。它将像素的亮度值转换为一组频率系数。

题目使用图像的亮度通道。一个隐藏比特由比较两个中频系数来确定。如果这一对中的第一个系数大于或等于第二个，则读出 `1`；否则读出 `0`。

使用的系数对：

| 对 | 第一个系数 | 第二个系数 |
|---:|---:|---:|
| 1 | `(2, 3)` | `(3, 2)` |
| 2 | `(1, 4)` | `(4, 1)` |
| 3 | `(2, 4)` | `(4, 2)` |
| 4 | `(3, 3)` | `(4, 3)` |

索引从零开始。块和系数对的选择按照由密钥 `bro` 生成的伪随机顺序进行。

### 数据恢复

得到的比特被组合成字节。正确的数据流以签名开头：

```text
KSTU-DCT1
```

签名之后依次是消息长度、flag 本身以及 CRC32 校验和。CRC 用于验证密钥是否正确以及数据的完整性。

要自动提取，可以使用附带的脚本：

```bash
python3 stego_dct.py decode bro_stego_with_hint.png --key bro
```

结果：

```text
KubSTU{dct_clouds_hide_more_than_weather}
```

**Flag：** `KubSTU{dct_clouds_hide_more_than_weather}`
