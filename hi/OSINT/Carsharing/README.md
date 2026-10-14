# Carsharing

> **श्रेणी:** OSINT · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

![carsharing_hq.jpg](../../../assets/OSINT/Carsharing/carsharing_hq.jpg)

एक दिन क्लास के बाद मैंने दोस्तों के साथ एक कारशेयरिंग कार ली और शहर के केंद्र में घूमे। कार को हमने कहीं पेड़ों की छाया में छोड़ दिया और यादगार के तौर पर एक फ़ोटो खींची। अगली कार ढूँढ़ते-ढूँढ़ते हम बिल्कुल भूल ही गए कि इसे कहाँ छोड़ा था। याद दिलाने में मदद करो: हमने इसे कहाँ पार्क किया था? दशमलव के बाद 4 अंकों वाले निर्देशांक काफ़ी होंगे।

फ़्लैग फ़ॉर्मैट — `KubSTU{xx.xxxx_yy.yyyy}`

**फ़ाइलें:** [carsharing_hq.jpg](../../../assets/OSINT/Carsharing/carsharing_hq.jpg)

## 🏁 समाधान

### चरण 1. मेटाडेटा

सबसे पहले हम EXIF जाँचते हैं: कभी-कभी फ़ोन फ़ोटो में GPS निर्देशांक सहेज लेता है, और तब कार्य एक मिनट में हल हो जाता है।

```
exiftool carsharing_hq.jpg

ExifTool Version Number         : 13.45
File Name                       : carsharing_hq.jpg
Directory                       : .
File Size                       : 767 kB
File Modification Date/Time     : 2026:10:06 12:29:44+03:00
File Access Date/Time           : 2026:10:06 16:58:06+03:00
File Creation Date/Time         : 2026:10:06 12:30:09+03:00
File Permissions                : -rw-rw-rw-
File Type                       : JPEG
File Type Extension             : jpg
MIME Type                       : image/jpeg
Exif Byte Order                 : Big-endian (Motorola, MM)
Y Resolution                    : 72
X Resolution                    : 72
Camera Model Name               : SM-A556E
Make                            : samsung
Software                        : A556EXXU7BYDB
Y Cb Cr Positioning             : Centered
Exif Version                    : 0220
Aperture Value                  : 1.8
Scene Type                      : Unknown (?)
Exposure Compensation           : 0
Exposure Program                : Program AE
Color Space                     : sRGB
Max Aperture Value              : 1.7
Brightness Value                : 6.09
Flashpix Version                : 0100
Date/Time Original              : 2026:05:26 14:23:25
Warning                         : [minor] Unrecognized MakerNotes
Sub Sec Time Original           : 0035
White Balance                   : Auto
Interoperability Index          : R98 - DCF basic file (sRGB)
Custom Rendered                 : Normal
Exposure Mode                   : Auto
Exposure Time                   : 1/681
Flash                           : No Flash
Sub Sec Time                    : 127
F Number                        : 1.8
User Comment                    :
Saturation                      : Normal
Components Configuration        : Err (63), Err (63), Err (63), -
ISO                             : 50
Focal Length In 35mm Format     : 23 mm
Sub Sec Time Digitized          : 0035
Contrast                        : Normal
Sharpness                       : Normal
Digital Zoom Ratio              : 0
Create Date                     : 2026:05:26 14:23:25
Shutter Speed Value             : 1/671
Metering Mode                   : Center-weighted average
Focal Length                    : 5.5 mm
Scene Capture Type              : Standard
Light Source                    : Unknown
Orientation                     : Horizontal (normal)
Resolution Unit                 : inches
Modify Date                     : 2026:05:26 14:23:25
JFIF Version                    : 1.01
Profile CMM Type                :
Profile Version                 : 4.3.0
Profile Class                   : Display Device Profile
Color Space Data                : RGB
Profile Connection Space        : XYZ
Profile Date Time               : 2016:01:01 00:00:00
Profile File Signature          : acsp
Primary Platform                : Unknown ()
CMM Flags                       : Not Embedded, Independent
Device Manufacturer             :
Device Model                    :
Device Attributes               : Reflective, Glossy, Positive, Color
Rendering Intent                : Media-Relative Colorimetric
Connection Space Illuminant     : 0.9642 1 0.82491
Profile Creator                 :
Profile ID                      : 0
Profile Description             : sRGB
Red Matrix Column               : 0.43607 0.22249 0.01392
Green Matrix Column             : 0.38515 0.71687 0.09708
Blue Matrix Column              : 0.14307 0.06061 0.7141
Media White Point               : 0.9642 1 0.82491
Red Tone Reproduction Curve     : (Binary data 40 bytes, use -b option to extract)
Green Tone Reproduction Curve   : (Binary data 40 bytes, use -b option to extract)
Blue Tone Reproduction Curve    : (Binary data 40 bytes, use -b option to extract)
Profile Copyright               : Google Inc. 2016
Image Width                     : 1920
Image Height                    : 886
Encoding Process                : Baseline DCT, Huffman coding
Bits Per Sample                 : 8
Color Components                : 3
Y Cb Cr Sub Sampling            : YCbCr4:2:0 (2 2)
Aperture                        : 1.8
Image Size                      : 1920x886
Megapixels                      : 1.7
Scale Factor To 35 mm Equivalent: 4.2
Shutter Speed                   : 1/681
Create Date                     : 2026:05:26 14:23:25.0035
Date/Time Original              : 2026:05:26 14:23:25.0035
Modify Date                     : 2026:05:26 14:23:25.127
Circle Of Confusion             : 0.007 mm
Field Of View                   : 76.1 deg
Focal Length                    : 5.5 mm (35 mm equivalent: 23.0 mm)
Hyperfocal Distance             : 2.36 m
Light Value                     : 12.1
```

मेटाडेटा में शूटिंग के निर्देशांक नहीं हैं। बस छवि के ज़रिये ही जियोलोकेशन करना बाकी है।

### चरण 2. फ़ोटो में क्या दिखता है

**शहर।** कार के पिछले शीशे पर "Citydrive" (Ситидрайв) कारशेयरिंग का स्टिकर है। कारशेयरिंग तो कई शहरों में चलती है, पर प्रतियोगिता Krasnodar की है, और Krasnodar में Citydrive मौजूद है। खोज वहीं से शुरू करना तर्कसंगत है।

**इमारत।** दाईं ओर सजावटी चिनाई वाला लाल ईंट का एक नीचा घर है: पायलस्टर, प्रोफ़ाइल किया हुआ कार्निस। दीवारें सफ़ेदी की हुई हैं, पलस्तर जगह-जगह उखड़ा हुआ है, खिड़कियों पर जाली है। यह पुराने Yekaterinodar की क्रांति-पूर्व इमारतें हैं। ऐसे घर रिहायशी इलाक़ों (FMR, YuMR, KMR, Gidrostroy) में लगभग नहीं मिलते और ऐतिहासिक केंद्र में केंद्रित हैं।

**सड़क का प्रोफ़ाइल।** कार सड़क के हिस्से पर खड़ी है। आगे पुराने बड़े पेड़ों वाली चौड़ी मिट्टी की पट्टी है, उसके पीछे एक सँकरा डामर का फ़ुटपाथ, और घर फ़ुटपाथ के ठीक पीछे, बिल्डिंग-लाइन पर खड़ा है। केंद्र की पुरानी ब्लॉक-ग्रिड वाली सड़कें ऐसे ही बनी होती हैं: सँकरी सड़क, पेड़ों वाले लॉन, फ़ुटपाथ से सटे हुए नीचे घर।

**आस-पास।** पृष्ठभूमि में कोई बहुमंज़िला इमारत नहीं है, चारों ओर केवल नीची इमारतें और पेड़ हैं। यह एक बार फिर नए इलाक़ों की नहीं, बल्कि पुराने केंद्र की ओर इशारा करता है।

**निष्कर्ष:** फ़ोटो Krasnodar के ऐतिहासिक केंद्र में, Severnaya और Postovaya सड़कों के बीच पुरानी इमारतों वाले ब्लॉक में ली गई है। आगे हम पैनोरमा पर ठीक वही घर ढूँढ़ते हैं।

### चरण 3. पैनोरमा का अध्ययन

कुछ समय बाद हम निर्देशांक **45.025635, 38.981874** के पैनोरमा तक पहुँचते हैं। यहाँ का घर खोजे जा रहे घर से बेहद मिलता-जुलता दिखता है, लेकिन 2025 का पैनोरमा बहुत जानकारी नहीं देता। अन्य वर्षों के पैनोरमा जाँचें तो 2021 सबसे बेहतर रहेगा।

हम तुलना करना शुरू करते हैं।

![carsharing_paint.jpg](../../../assets/OSINT/Carsharing/carsharing_paint.jpg)

हमारे 5 तत्व मेल खाते हैं, इसलिए हमें सही निर्देशांक मिल गए।

अब हम फ़्लैग सबमिट करते हैं — `KubSTU{45.0256, 38.9818}`

**फ़्लैग:** `KubSTU{45.0256, 38.9818}`
