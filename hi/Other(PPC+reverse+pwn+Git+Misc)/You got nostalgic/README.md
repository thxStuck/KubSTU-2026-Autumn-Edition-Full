# You got nostalgic

> **श्रेणी:** Misc / Stego · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

> What a wonderful place, but how did I get here?
> कितनी शानदार जगह है, पर मैं यहाँ पहुँचा कैसे?

![The image](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/the-image.png)

## 🏁 समाधान

### प्रारंभिक विश्लेषण

हमें एक PNG इमेज दी गई है। इसे सामान्य स्टेग्नोग्राफ़ी और मेटाडेटा टूल्स से जाँचते हैं। मैं [Aperi'Solve](https://github.com/Zeecka/AperiSolve) और [ExifTool](https://exiftool.org/) का इस्तेमाल कर रहा हूँ:

![AperiSolve](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/aperisolve.png)

फ़िल्टर, LSB और अल्फ़ा चैनल कुछ भी उपयोगी नहीं दिखाते, इसलिए मेटाडेटा और पढ़ने योग्य स्ट्रिंग्स पर गौर करना ठीक रहेगा। अधिकांश मेटाडेटा सामान्य लगता है (तारीखें, KubSTU और व्हाइट हाउस के GPS निर्देशांक), लेकिन उनके बीच कुछ अजीब फ़ील्ड हैं जिनका कंटेंट देखने में बेमतलब लगता है और किसी एक स्ट्रिंग के हिस्सों जैसा दिखता है। हर टुकड़ा एक अंक से शुरू होता है — यह उसका क्रम संख्या है:

```
1 FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G
2 (SKe^*=*0EMpMdpGijJd81A
3 @HkdoY?I9D=6ii,'#f
4 ]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

अंक हटाकर टुकड़ों को क्रम से जोड़ते हैं:

```
FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G(SKe^*=*0EMpMdpGijJd81A@HkdoY?I9D=6ii,'#f]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

### स्ट्रिंग को डिकोड करना

यह स्ट्रिंग किसी एन्कोडिंग के आउटपुट जैसी दिखती है। CyberChef में अलग-अलग विकल्प आज़माते हैं: ROT13, Base32, Base64 इत्यादि। Base92 पर हमें अर्थपूर्ण टेक्स्ट मिलता है — एक Google Drive लिंक:

![CyberChef](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cyberchef.png)

```
https://drive.google.com/file/d/1s2sqWhknYnbWEhgggjvBzkrP90OU4x-j/view?usp=sharing
```

### Minecraft इंस्टेंस

लिंक पर `CL0S3.zip` नाम का एक आर्काइव है। इसे डाउनलोड करके अनपैक करने पर हमें एक Minecraft इंस्टेंस की फ़ोल्डर संरचना दिखती है — `mods`, `coremods`, `resourcepacks`, `saves` इत्यादि:

![CL0S3 folder](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cl0s3-folder.png)

हमें गेम का वर्ज़न पता नहीं है, इसलिए एक बार फिर इमेज के मेटाडेटा पर लौटते हैं — `Comment` फ़ील्ड में `version 1.12.2` मिलता है:

![Hidden version](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/hidden-version.png)

किसी भी लॉन्चर में वर्ज़न 1.12.2 चलाएँ, और अनपैक किए गए फ़ोल्डर को गेम डायरेक्टरी के रूप में सेट करें (अगर `mods` में मोड हैं, तो 1.12.2 के लिए Forge चाहिए होगा)। सिंगलप्लेयर मेनू में हमें कई सेव दिखते हैं:

![Saves](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/saves.png)

दुनिया `here?` (फ़ोल्डर `4lm0st_th3r3`) ही एकमात्र है जिसका नाम और प्रीव्यू अलग है। इसमें शामिल होते हैं:

![Uncompleted flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/uncompleted-flag.png)

हमारा स्वागत आइटम फ़्रेम की एक 10×5 ग्रिड करती है, जिनमें से दो में पहले से मैप लगे हैं, और एक किताब जिसमें कुछ टेक्स्ट है:

![Book](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/book.png)

```
hello whoever got to
this point.
I hope you enjoy this
challenge.
Finish this grid if you
want a flag.
```

### ग्रिड को भरना

यह समझने के लिए कि ग्रिड को किससे भरना है, हम भरे हुए फ़्रेमों में से एक की सामग्री निकालते हैं — यह एक मैप है। इस पर मूल इमेज का एक टुकड़ा दिखता है, यानी टास्क की तस्वीर को मैपों में काटा गया है।

पहले यह पता लगाते हैं कि Minecraft में कस्टम इमेज मैपों पर आती कैसे हैं:

![Google search](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/google-search.png)

*(सर्च क्वेरी: "how to put your own photo on Minecraft maps"। AI ओवरव्यू बताता है कि कस्टम इमेजों को मैप डेटा फ़ाइलों में बदला जाता है और दुनिया के `data` फ़ोल्डर में रखा जाता है, फिर गेम में `/give` कमांड से उन्हें पाया जाता है।)*

इससे हमें दो संकेत मिलते हैं:

1. मैप डेटा `.minecraft/saves/<World_name>/data` में `map_<number>.dat` नाम की फ़ाइलों में रखा जाता है। हमारे मामले में यह `saves/4lm0st_th3r3/data` है।
2. किसी भी मैप को उसके नंबर से इस कमांड के ज़रिए खुद को दिया जा सकता है:

```
/give @p filled_map 1 <map_number>
```

यह सिंटैक्स ख़ास तौर पर 1.12.2 में काम करता है (मैप नंबर data value के रूप में पास होता है)। 1.13 से कमांड अलग दिखती है: `/give @p filled_map{map:<number>}` — एक और वजह कि सही वर्ज़न ढूँढना क्यों मायने रखता था।

`data` फ़ोल्डर में 65 मैप हैं (`map_0.dat` … `map_64.dat`), जबकि ग्रिड में केवल 50 फ़्रेम हैं। यानी कुछ मैप भटकाने वाले हैं। उदाहरण के लिए, उनमें से एक KubSTU का लोगो है:

![KubSTU logo](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/kubstu-logo.png)

यहाँ से आगे बढ़ने के दो तरीके हैं।

**विकल्प 1 (लेखक का इरादा)।** एक-एक करके मैप खुद को दें और फ़्रेमों में लगाएँ। इमेज 0–49 नंबर वाले मैपों से बनती है।

**विकल्प 2 (बिना हाथ से लगाए)।** हर `map_N.dat` एक gzip-कंप्रेस्ड NBT फ़ाइल है, जिसके `data.colors` फ़ील्ड में 128×128 बाइट का एक ऐरे होता है — Minecraft मैप कलर पैलेट के इंडेक्स। आप इन फ़ाइलों को किसी स्क्रिप्ट (जैसे Python + `nbtlib`) से पढ़ सकते हैं, 1.12 पैलेट से इंडेक्स को RGB में बदल सकते हैं, और मैपों को गेम के बाहर एक ही इमेज में जोड़ सकते हैं।

## फ़्लैग

जब मैप 0–49 को फ़्रेमों में सही से लगा दिया जाता है, तो तस्वीर में फ़्लैग उभर आता है:

![Flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/flag.png)

**फ़्लैग:** `KubSTU{n0st4lg14_1s_h3r3}`
