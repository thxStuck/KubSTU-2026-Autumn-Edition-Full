# Timing

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

我们拿到一个用于分析的样本。需要打开它并恢复出 flag。

## 🏁 解答

需要打开该样本进行分析，例如在 autopsy 中。

`draft_notes.tmp` 和 `unused_ledger.tmp` 这两个对象是用来分散注意力的小诱饵记录。在文件系统的根目录中有一个被删除的 `sync_7D3.tmp`；相邻的日志 `Logs/TRANSFER.LOG` 将该对象与最后一次操作 Batch 7D3 关联起来。

尽管扩展名是 `.tmp`，按魔数（magic number）识别将目标文件判定为 **PE32 executable**。在 Autopsy 中应通过右键操作 Extract File(s) 将其保存。正确文件的大小为 **14 848 字节**，其起始字节为 `4D 5A`（`MZ`）。原始文件名可能显示为首字符被还原，或带有删除标记：这是 FAT 记录的正常结果，不影响提取。

在 `fwrite` 调用之前构建缓冲区的那个函数里，有两个短字节数组。它们先被拼接起来，然后对索引为 `i` 的每个字节执行如下操作：

```text
shuffled[i] = encoded[i] XOR ((0x51 + 0x23 × i) mod 256)
```

接着，前两个 16 字节的块互换，其余部分原样复制：

```text
plain[0:16]   = shuffled[16:32]
plain[16:32]  = shuffled[0:16]
plain[32:]    = shuffled[32:]
```

完成这些操作后得到：

```text
KubSTU{aU70p5y_D3l373d_P3_4nd_r3v3r53}
```

**Flag：** `KubSTU{aU70p5y_D3l373d_P3_4nd_r3v3r53}`
