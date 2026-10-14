# Last chance

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

我们拿到一个可疑的 PDF 文件。目标是分析它并恢复出隐藏的 flag。

**文件：** [solve.py](../../../assets/Forensics/Last%20chance/solve.py)

## 🏁 解答

分析可疑 PDF 时，首先应检查其属性和元数据。可以用 `exiftool`、`pdfid`，或者直接用文本编辑器打开文件并搜索字典对象来完成。

### 步骤 1：元数据分析
在元数据字段 **Author**（作者）和 **Subject**（主题）中，发现了 Base64 格式的奇怪字符串：
- **Author**：`QR_PART1:<base64_data>`
- **Subject**：`QR_PART2:<base64_data>`

### 步骤 2：重建二维码
提取这两个字符串，将它们从 Base64 解码为 PNG 格式。我们得到一张图像的两半。将它们竖直拼接（上半部分在上，下半部分在下），就得到一个完整的二维码。

扫描二维码得到 AES 的盐值（salt）：
```text
salt=7f3c92a1b4e5
```

### 步骤 3：在 PDF 结构中查找隐藏对象
PDF 文件可以存储不可见显示的对象。我们使用 `pdf-parser` 或搜索字符串 `obj`。我们发现在文件末尾添加了三个可疑对象：

1.  **对象 100（`/JBIG2Decode`）**：在数据流（stream）内部隐藏着一个初始化向量（**IV**）。数据以 hex 字符串形式表示。
    *   **IV**：`a1b2c3d4e5f67890`（在字节表示中偏移 11 处提取）。

2.  **对象 101（`/Sig`）**：一个数字签名对象，其 `/Contents` 字段中包含 ASN.1 DER 结构。在该结构内部，非标准标签 `0x80` 之下隐藏着 flag 的第一部分。
    *   **Part 1**：`part1_f4k3_s1g`

3.  **对象 102（`/Crypt`）**：包含一段 hex 格式的加密数据流——即我们最终的 flag。

### 步骤 4：解密 flag
现在我们拥有所有组成部分：
- **盐值（来自二维码）**：`7f3c92a1b4e5`
- **IV（来自对象 100）**：`a1b2c3d4e5f67890`
- **密文**：来自对象 102
- **flag 的第一部分（来自对象 101）**：`part1_f4k3_s1g`

AES-256 的密钥计算为盐值与 IV 拼接后的 SHA-256 哈希：
$$\text{Key} = \text{SHA256}(\text{Salt} + \text{IV})[:32]$$

使用得到的密钥和 IV，以 AES-256-CBC 算法解密对象 102 中的数据。

**Flag：** `KubSTU{part1_f4k3_s1g_metadata_stitching_is_fun_abe8776b}`
