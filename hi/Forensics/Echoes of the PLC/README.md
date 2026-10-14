# Echoes of the PLC

> **श्रेणी:** Forensics · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

यह कार्य किसी खुली (plaintext) स्ट्रिंग की खोज की नहीं, बल्कि **तीन प्रोटोकॉलों के सहसंबंध (correlation)** की परीक्षा लेता है। एक बड़े मिश्रित डंप में MQTT एक मैनिफ़ेस्ट प्रकाशित करता है, Modbus/TCP एन्क्रिप्टेड ब्लॉक भेजता है, और ICMP Echo Reply प्रत्येक ब्लॉक के लिए मास्क रखता है।

**फ़ाइलें:** [validate_and_solve.py](../../../assets/Forensics/Echoes%20of%20the%20PLC/validate_and_solve.py)

## 🏁 समाधान

### चरण 1. MQTT मैनिफ़ेस्ट ढूँढें

इस फ़िल्टर से शुरू करें:

```wireshark
tcp.port == 1883
```

MQTT आदान-प्रदानों में से विषय (topic) `facility/maintenance/calibration-manifest` वाला प्रकाशन ढूँढें। एक सुविधाजनक अतिरिक्त फ़िल्टर:

```wireshark
tcp contains "calibration-manifest"
```

इस स्ट्रीम का एक पैकेट चुनें और **Follow → TCP Stream** खोलें। JSON मैनिफ़ेस्ट एल्गोरिथ्म का वर्णन करता है:

```json
{
  "source": "Modbus/TCP unit=7 function=0x04",
  "order": "transaction_id ascending",
  "mask": "ICMP Echo Reply id=3199; sequence = transaction_id - 0x4000",
  "final": "zlib"
}
```

यह संकेत समाधान की शृंखला को असंदिग्ध बना देता है: सिफर, कुंजी के स्रोत या परिणाम के प्रारूप का अनुमान लगाने की ज़रूरत नहीं।

### चरण 2. Modbus ब्लॉक चुनें

यह फ़िल्टर लागू करें:

```wireshark
tcp.port == 502 && ip.addr == 10.20.7.7
```

सर्वर `10.20.7.7` की प्रतिक्रियाओं में **Unit Identifier = 7** और **Function Code = 0x04** वाले फ़्रेम ढूँढें। इनकी संख्या नौ है। प्रत्येक प्रतिक्रिया में एक Modbus transaction ID और पढ़ा गया बाइनरी डेटा होता है। इस रूप की जोड़ियाँ सहेजें:

```text
transaction_id -> data
```

ब्लॉकों को `transaction_id` के आरोही क्रम (ascending) में क्रमबद्ध करें।

### चरण 3. ICMP मास्क चुनें

यह फ़िल्टर लागू करें:

```wireshark
icmp.type == 0 && icmp.ident == 3199
```

ये लक्षित identifier वाले ICMP Echo Reply हैं। Modbus transaction ID `0x4000 + N` के लिए, sequence `N` वाला ICMP पैकेट लें। इसका data payload संबंधित Modbus ब्लॉक के बराबर लंबाई का है और यही XOR मास्क है।

### चरण 4. कंटेनर को पुनर्स्थापित करें

प्रत्येक Modbus ब्लॉक के लिए संबंधित ICMP payload के साथ बाइट-दर-बाइट XOR करें। पुनर्प्राप्त ब्लॉकों को transaction ID के अनुसार जोड़ें। परिणाम एक मान्य zlib स्ट्रीम है, जिसे विसंपीड़ित (decompress) करना है।

पूर्ण संदर्भ विश्लेषण `validate_and_solve.py` में है। परिवर्तन का मुख्य अंश ऐसा दिखता है:

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

विसंपीड़न के बाद कैलिब्रेशन लॉग और फ़्लैग प्रिंट होता है।

**फ़्लैग:** `KubSTU{modbus_echoes_keep_the_secret}`
