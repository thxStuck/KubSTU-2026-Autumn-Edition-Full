# cry

> **श्रेणी:** Forensics · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

हमें एक नेटवर्क डंप `artifacts/incident.pcap` दिया गया है। ट्रैफ़िक का विश्लेषण करके फ़्लैग को पुनर्प्राप्त करना है।

**फ़ाइलें:** [solve.py](../../../assets/Forensics/cry/solve.py)

## 🏁 समाधान

### 1. Heartbleed की खोज
Wireshark में `tls.record.content_type == 24` लागू करें। संदिग्ध heartbeat अनुरोध `10.23.7.44` से `10.23.7.10:443` की ओर जाते हैं; heartbeat body में लंबाई `0x4000`, `0x2000` घोषित की गई है, हालाँकि वास्तविक डेटा बहुत कम है। प्रतिक्रियाओं में heap bytes होते हैं।

CLI विकल्प:
```bash
tshark -r artifacts/incident.pcap -Y 'tcp.port==443' -T fields -e tcp.stream -e tcp.srcport -e tcp.len
strings -a artifacts/incident.pcap | grep -a -n 'LEAK'
```

### 2. Heartbleed leak से कुंजी की पुनर्प्राप्ति
अलग-अलग `memory_*.bin` शोर वाले पृष्ठ (pages) हैं और उनमें PEM-कुंजी नहीं है। कुंजी केवल heartbeat प्रतिक्रियाओं के मुख्य भाग (bodies) में उपलब्ध है। टाइप `2` की प्रतिक्रियाओं का payload निकालें, `LEAK + uint16(index) + uint16(length) + data` प्रारूप के रिकॉर्ड ढूँढें, पुनरावृत्त (repeating) XOR-कुंजी `heartbeat-heap-2014` लागू करें, index के अनुसार क्रमबद्ध करें और अतिव्यापी (overlapping) PEM-खंडों को पुनर्स्थापित करें।
```bash
python3 solve.py .
openssl rsa -in server_recovered.key -check -noout
openssl x509 -in artifacts/server.crt -noout -modulus | openssl sha256
openssl rsa -in server_recovered.key -noout -modulus | openssl sha256
```

### 3. TLS की डिक्रिप्शन
TLS 1.2 RSA key exchange के लिए Wireshark में RSA key जोड़ें: `10.23.7.10`, `443`, `http`, `server.key`। इसके बाद `http` या `tls && tcp.stream==0` लागू करें। डिक्रिप्ट की गई प्रतिक्रिया में एक लिंक दिखाई देता है:

```text
\\u003ca href="smb://10.23.7.19/IR$\\u005carchive\\u005cdropbox_payload.zip"\\u003eincident bundle\\u003c/a\\u003e
```

HTML escapes को डिकोड करने के बाद, पता यह है:

```text
smb://10.23.7.19/IR$/archive/dropbox_payload.zip
```

### 4. SMB-सर्वर के बिना SMB-स्ट्रीम निकालना
PCAP में पहले से ही TCP-स्ट्रीम `10.23.7.19:445 -> 10.23.7.44:51500` मौजूद है। यह एक स्व-निहित (self-contained) SMB-जैसी साक्ष्य-स्ट्रीम है।

Wireshark में `tcp.port == 445` के माध्यम से स्ट्रीम चुनें, फिर **Follow → TCP Stream → Raw → Save As**। `COUNT` हेडर ढूँढें, फिर `CHNK + uint16(index) + uint16(length) + encoded_data` प्रारूप के रिकॉर्ड। रिकॉर्ड को index के अनुसार क्रमबद्ध करें और प्रत्येक chunk को पुनरावृत्त XOR-कुंजी `Northstar-IR-2026` से डिक्रिप्ट करें:
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

### 5. फ़्लैग
`KubSTU{heartbleed_reassembled_the_private_key_and_tls_fell}`

**फ़्लैग:** `KubSTU{heartbleed_reassembled_the_private_key_and_tls_fell}`
