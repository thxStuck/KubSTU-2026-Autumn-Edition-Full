# Echoes of the PLC

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

本题考查的不是查找明文字符串，而是**三种协议的关联**。在一个庞大的混合抓包中，MQTT 发布一个清单（manifest），Modbus/TCP 传输加密块，而 ICMP Echo Reply 则携带每个块的掩码。

**文件：** [validate_and_solve.py](../../../assets/Forensics/Echoes%20of%20the%20PLC/validate_and_solve.py)

## 🏁 解答

### 步骤 1. 找到 MQTT 清单

先用这个过滤器：

```wireshark
tcp.port == 1883
```

在 MQTT 交互中，找到主题为 `facility/maintenance/calibration-manifest` 的发布。一个方便的附加过滤器：

```wireshark
tcp contains "calibration-manifest"
```

选中该流中的一个数据包，打开 **Follow → TCP Stream**。JSON 清单描述了算法：

```json
{
  "source": "Modbus/TCP unit=7 function=0x04",
  "order": "transaction_id ascending",
  "mask": "ICMP Echo Reply id=3199; sequence = transaction_id - 0x4000",
  "final": "zlib"
}
```

这条提示使解题链条变得唯一：无需猜测密码算法、密钥来源或结果格式。

### 步骤 2. 筛选 Modbus 块

应用过滤器：

```wireshark
tcp.port == 502 && ip.addr == 10.20.7.7
```

在服务器 `10.20.7.7` 的响应中，找到 **Unit Identifier = 7** 且 **Function Code = 0x04** 的帧。共有九个。每个响应都有一个 Modbus transaction ID 和读取到的二进制数据。保存如下形式的配对：

```text
transaction_id -> data
```

按 `transaction_id` 升序对这些块排序。

### 步骤 3. 筛选 ICMP 掩码

应用过滤器：

```wireshark
icmp.type == 0 && icmp.ident == 3199
```

这些是带目标 identifier 的 ICMP Echo Reply。对于 Modbus transaction ID `0x4000 + N`，取 sequence 为 `N` 的 ICMP 包。它的 data payload 与对应的 Modbus 块长度相同，即为 XOR 掩码。

### 步骤 4. 还原容器

对每个 Modbus 块与对应的 ICMP payload 逐字节 XOR。按 transaction ID 拼接还原出的块。结果是一个有效的 zlib 流，需要将其解压。

完整的参考解析在 `validate_and_solve.py` 中。关键的变换片段如下：

```python
restored = bytearray()
for transaction_id, encrypted_block in sorted(modbus_blocks.items()):
    sequence = transaction_id - 0x4000
    mask = icmp_masks[sequence]
    restored.extend(
        byte ^ mask[index]
        for index, byte in enumerate(encrypted_block)
    )

print(zlib.decompress(bytes(restored)).decode())
```

解压后会输出校准日志和 flag。

**Flag：** `KubSTU{modbus_echoes_keep_the_secret}`
