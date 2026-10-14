# cry

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

We are given a network capture `artifacts/incident.pcap`. We need to analyze the traffic and recover the flag.

**Files:** [solve.py](../../../assets/Forensics/cry/solve.py)

## 🏁 Solution

### 1. Looking for Heartbleed
In Wireshark, apply `tls.record.content_type == 24`. Suspicious heartbeat requests go from `10.23.7.44` to `10.23.7.10:443`; the heartbeat body declares lengths `0x4000`, `0x2000`, although there is very little real data. The responses contain heap bytes.

CLI variant:
```bash
tshark -r artifacts/incident.pcap -Y 'tcp.port==443' -T fields -e tcp.stream -e tcp.srcport -e tcp.len
strings -a artifacts/incident.pcap | grep -a -n 'LEAK'
```

### 2. Recovering the key from the Heartbleed leak
The individual `memory_*.bin` files are noise pages and do not contain a PEM key. The key is available only in the bodies of the heartbeat responses. Extract the payload of type `2` responses, find records of the format `LEAK + uint16(index) + uint16(length) + data`, apply the repeating XOR key `heartbeat-heap-2014`, sort by index and reconstruct the overlapping PEM fragments.
```bash
python3 solve.py .
openssl rsa -in server_recovered.key -check -noout
openssl x509 -in artifacts/server.crt -noout -modulus | openssl sha256
openssl rsa -in server_recovered.key -noout -modulus | openssl sha256
```

### 3. Decrypting TLS
For TLS 1.2 RSA key exchange, add the RSA key in Wireshark: `10.23.7.10`, `443`, `http`, `server.key`. Then apply `http` or `tls && tcp.stream==0`. In the decrypted response a link is visible:

```text
\\u003ca href="smb://10.23.7.19/IR$\\u005carchive\\u005cdropbox_payload.zip"\\u003eincident bundle\\u003c/a\\u003e
```

After decoding the HTML escapes, the address is:

```text
smb://10.23.7.19/IR$/archive/dropbox_payload.zip
```

### 4. Extracting the SMB stream without an SMB server
The PCAP already contains the TCP stream `10.23.7.19:445 -> 10.23.7.44:51500`. This is a self-contained SMB-like evidence stream.

In Wireshark, select the stream via `tcp.port == 445`, then **Follow → TCP Stream → Raw → Save As**. Find the header `COUNT`, then records of the format `CHNK + uint16(index) + uint16(length) + encoded_data`. Sort the records by index and decrypt each chunk with the repeating XOR key `Northstar-IR-2026`:
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

**Flag:** `KubSTU{heartbleed_reassembled_the_private_key_and_tls_fell}`
