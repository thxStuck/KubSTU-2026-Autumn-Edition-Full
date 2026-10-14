# Not to give, not to take

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

在 archive.zip 中保留了本地 ZIP 记录，但缺少中央目录（Central Directory, CD）和存档结束记录（EOCD）。需要在不依赖对 PK\x03\x04 签名的朴素搜索的前提下恢复文件，并校验所提取数据的完整性。

**文件：** [recover.py](../../../assets/Forensics/Not%20to%20give,%20not%20to%20take/recover.py)

## 🏁 解答

该存档包含六条真实记录。其中有意保留了以下特征：

- secret.txt 使用 Deflate 和通用标志位（general-purpose）bit 3（0x0008）：本地头中的 CRC 和大小均为零，压缩流之后放置了一个 Data Descriptor。
- café.txt 以旧的 CP437 编码写入：文件名中的字节 0x82 表示 é；未设置 UTF-8 标志位。
- evidence_03.bin 的 CRC 不匹配，必须在提取时明确标注为损坏。
- calibration.dat 使用 Deflate 方法，但其压缩流中含有一个伪造的 PK\x03\x04 签名字节序列。
- 使用了 Store（0）和 Deflate（8）两种方法。
- flag 存储在压缩后的 secret.txt 中。

ZIP 工具通常把中央目录作为记录的索引。这里存档以正确的本地头开头，但索引已被删除。因此标准工具可能报告存档已损坏，或不显示文件列表。

例如，可以这样检查结尾结构是否缺失：

```bash
xxd -g 1 archive.zip | tail
# CD 以 PK 01 02 开头；EOCD 以 PK 05 06 开头。
# 本文件中这两个签名都不存在。
```

搜索 PK\x03\x04 同样不是充分的解法：该签名在 calibration.dat 的压缩数据内部出现过一次。如果把它当作又一条记录来解析，就会得到错误的字段和错误的存档边界。

ZIP 中所有多字节数值都以 little-endian 存储。压缩数据的起始位置这样计算：

```text
data_start = header_offset + 30 + filename_length + extra_length
```

对于 Store，压缩数据就是文件本身的字节。对于 Deflate，ZIP 使用 raw DEFLATE stream：在 Python 中通过 zlib.decompress(data, -15) 解压，即不带 zlib 包装。

在这种情况下，可靠的策略是从一个已知边界走到另一个已知边界。

1. 检查当前 offset 处的签名。
2. 读取本地头、文件名和 extra 字段。
3. 若 bit 3 被清零，则从本地头取压缩数据长度，并跳过这些数据。
4. 若 bit 3 被置位，不要使用头中的零大小。对于 Deflate，用解码器确定流的结尾，然后读取 Data Descriptor。
5. 解压文件，计算 CRC-32 并与期望值比较。
6. 只按计算出的边界查找下一条记录，而不是逐字节扫描 PK\x03\x04。

本题的 Data Descriptor 中存在一个 PK\x07\x08 签名，其后依次是 CRC-32、compressed size 和 uncompressed size——各 4 字节。descriptor 总共占 16 字节。

对于 Deflate，流的结尾可以通过 zlib.decompressobj(-15) 获得：DEFLATE 流结束后，解码器会设置 eof，而流之后的所有内容（本例中即 descriptor）会返回在 unused_data 中。这样就能正确地确定边界，而不会把流内部的伪造签名当作新记录。

secret.txt 设置了标志位 0x0008。因此本地的 CRC 和大小字段为零，不描述实际数据。在 raw Deflate 流之后，解码器找到 Data Descriptor：

- CRC-32：88097019
- compressed size：54 字节
- uncompressed size：53 字节

descriptor 签名位于 offset 227（0xe3）。读取 16 字节的 descriptor 后，下一条本地记录正好从 offset 243 开始。

总之，需要顺序解析各记录、处理描述符、解码文件名并校验 CRC。

**Flag：** `KubSTU{local_headers_lie_central_directory_does_not}`
