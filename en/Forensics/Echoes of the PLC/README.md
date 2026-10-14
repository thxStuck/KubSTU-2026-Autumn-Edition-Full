# Echoes of the PLC

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

The task tests not the search for a plaintext string but the **correlation of three protocols**. In a large mixed dump, MQTT publishes a manifest, Modbus/TCP transmits encrypted blocks, and ICMP Echo Reply contains masks for each block.

**Files:** [validate_and_solve.py](../../../assets/Forensics/Echoes%20of%20the%20PLC/validate_and_solve.py)

## 🏁 Solution

### Step 1. Find the MQTT manifest

Start with a filter:

```wireshark
tcp.port == 1883
```

Among the MQTT exchanges, find the publication with the topic `facility/maintenance/calibration-manifest`. A convenient additional filter:

```wireshark
tcp contains "calibration-manifest"
```

Select a packet from this stream and open **Follow → TCP Stream**. The JSON manifest describes the algorithm:

```json
{
  "source": "Modbus/TCP unit=7 function=0x04",
  "order": "transaction_id ascending",
  "mask": "ICMP Echo Reply id=3199; sequence = transaction_id - 0x4000",
  "final": "zlib"
}
```

This hint makes the solution chain unambiguous: there is no need to guess the cipher, the key source, or the result format.

### Step 2. Select the Modbus blocks

Apply the filter:

```wireshark
tcp.port == 502 && ip.addr == 10.20.7.7
```

In the responses of server `10.20.7.7`, find frames with **Unit Identifier = 7** and **Function Code = 0x04**. There are nine of them. Each response has a Modbus transaction ID and binary read data. Save pairs of the form:

```text
transaction_id -> data
```

Sort the blocks by `transaction_id` in ascending order.

### Step 3. Select the ICMP masks

Apply the filter:

```wireshark
icmp.type == 0 && icmp.ident == 3199
```

These are ICMP Echo Replies with the target identifier. For Modbus transaction ID `0x4000 + N`, take the ICMP packet with sequence `N`. Its data payload has the same length as the corresponding Modbus block and is the XOR mask.

### Step 4. Reconstruct the container

For each Modbus block, perform a byte-wise XOR with the corresponding ICMP payload. Concatenate the recovered blocks by transaction ID. The result is a valid zlib stream, which must be decompressed.

The full reference analysis is in `validate_and_solve.py`. The key transformation fragment looks like this:

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

After decompression, the calibration log and the flag are printed.

**Flag:** `KubSTU{modbus_echoes_keep_the_secret}`
