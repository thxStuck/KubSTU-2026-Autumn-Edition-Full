
## 1. Поиск Heartbleed
В Wireshark применить `tls.record.content_type == 24`. Подозрительные heartbeat-запросы идут от `10.23.7.44` к `10.23.7.10:443`; в heartbeat body заявлены длины `0x4000`, `0x2000`, хотя реальных данных очень мало. Ответы содержат heap bytes.

CLI-вариант:
```bash
tshark -r artifacts/incident.pcap -Y 'tcp.port==443' -T fields -e tcp.stream -e tcp.srcport -e tcp.len
strings -a artifacts/incident.pcap | grep -a -n 'LEAK'
```

## 2. Восстановление ключа из Heartbleed leak
Отдельные `memory_*.bin` являются шумовыми страницами и не содержат PEM-ключа. Ключ доступен только в телах heartbeat-ответов. Извлеките payload ответов типа `2`, найдите записи формата `LEAK + uint16(index) + uint16(length) + data`, примените повторяющийся XOR-ключ `heartbeat-heap-2014`, отсортируйте по index и восстановите перекрывающиеся PEM-фрагменты.
```bash
python3 solve.py .
openssl rsa -in server_recovered.key -check -noout
openssl x509 -in artifacts/server.crt -noout -modulus | openssl sha256
openssl rsa -in server_recovered.key -noout -modulus | openssl sha256
```


## 3. Расшифровка TLS
Для TLS 1.2 RSA key exchange добавить RSA key в Wireshark: `10.23.7.10`, `443`, `http`, `server.key`. После этого применить `http` или `tls && tcp.stream==0`. В расшифрованном ответе видна ссылка:
`\\u003ca href="smb://10.23.7.19/IR$\\u005carchive\\u005cdropbox_payload.zip"\\u003eincident bundle\\u003c/a\\u003e`

После декодирования HTML escapes адрес равен:
`smb://10.23.7.19/IR$/archive/dropbox_payload.zip`

## 4. Извлечение SMB-потока без SMB-сервера
В PCAP уже присутствует TCP-поток `10.23.7.19:445 -> 10.23.7.44:51500`. Это self-contained SMB-like evidence stream

В Wireshark выбрать поток через `tcp.port == 445`, затем **Follow → TCP Stream → Raw → Save As**. Найдите заголовок `COUNT`, затем записи формата `CHNK + uint16(index) + uint16(length) + encoded_data`. Отсортируйте записи по index и расшифруйте каждый chunk повторяющимся XOR-ключом `Northstar-IR-2026`:
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

## 5. Флаг
`KubSTU{heartbleed_reassembled_the_private_key_and_tls_fell}`