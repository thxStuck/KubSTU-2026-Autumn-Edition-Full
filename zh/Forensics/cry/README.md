# cry

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

我们拿到一个网络抓包 `artifacts/incident.pcap`。需要分析流量并恢复出 flag。

**文件：** [solve.py](../../../assets/Forensics/cry/solve.py)

## 🏁 解答

### 1. 寻找 Heartbleed
在 Wireshark 中应用 `tls.record.content_type == 24`。可疑的 heartbeat 请求从 `10.23.7.44` 发往 `10.23.7.10:443`；heartbeat body 中声明的长度为 `0x4000`、`0x2000`，而实际数据却很少。响应中含有 heap bytes。

CLI 方式：
```bash
tshark -r artifacts/incident.pcap -Y 'tcp.port==443' -T fields -e tcp.stream -e tcp.srcport -e tcp.len
strings -a artifacts/incident.pcap | grep -a -n 'LEAK'
```

### 2. 从 Heartbleed 泄漏中恢复密钥
单独的 `memory_*.bin` 是噪声页，不包含 PEM 密钥。密钥只存在于 heartbeat 响应的主体中。提取类型为 `2` 的响应的 payload，查找格式为 `LEAK + uint16(index) + uint16(length) + data` 的记录，应用重复 XOR 密钥 `heartbeat-heap-2014`，按 index 排序并重建相互重叠的 PEM 片段。
```bash
python3 solve.py .
openssl rsa -in server_recovered.key -check -noout
openssl x509 -in artifacts/server.crt -noout -modulus | openssl sha256
openssl rsa -in server_recovered.key -noout -modulus | openssl sha256
```

### 3. 解密 TLS
对于 TLS 1.2 RSA 密钥交换，在 Wireshark 中添加 RSA 密钥：`10.23.7.10`、`443`、`http`、`server.key`。然后应用 `http` 或 `tls && tcp.stream==0`。在解密后的响应中可以看到一个链接：

```text
\\u003ca href="smb://10.23.7.19/IR$\\u005carchive\\u005cdropbox_payload.zip"\\u003eincident bundle\\u003c/a\\u003e
```

解码 HTML 转义后，地址为：

```text
smb://10.23.7.19/IR$/archive/dropbox_payload.zip
```

### 4. 在没有 SMB 服务器的情况下提取 SMB 流
PCAP 中已经存在 TCP 流 `10.23.7.19:445 -> 10.23.7.44:51500`。这是一个自包含的、类 SMB 的证据流。

在 Wireshark 中通过 `tcp.port == 445` 选中该流，然后 **Follow → TCP Stream → Raw → Save As**。找到 `COUNT` 头，然后是格式为 `CHNK + uint16(index) + uint16(length) + encoded_data` 的记录。按 index 对记录排序，并用重复 XOR 密钥 `Northstar-IR-2026` 解密每个 chunk：
```bash
python3 - <<'PY'
from pathlib import Path
b=Path('smb_stream.raw').read_bytes()
key=b'Northstar-IR-2026'
pos=b.index(b'COUNT')+7
count=int.from_bytes(b[pos-2:pos], 'big')
chunks={}
for _ in range(count):
    pos=b.index(b'CHNK', pos)
    i=int.from_bytes(b[pos+4:pos+6], 'big')
    n=int.from_bytes(b[pos+6:pos+8], 'big')
    enc=b[pos+8:pos+8+n]
    chunks[i]=bytes(x ^ key[j % len(key)] for j,x in enumerate(enc))
    pos += 8+n
Path('dropbox_payload.zip').write_bytes(b''.join(chunks[i] for i in range(count)))
PY
unzip -p dropbox_payload.zip flag.txt
```

### 5. Flag
`KubSTU{heartbleed_reassembled_the_private_key_and_tls_fell}`

**Flag：** `KubSTU{heartbleed_reassembled_the_private_key_and_tls_fell}`
