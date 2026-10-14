# Latte Art

> **श्रेणी:** OSINT · **इवेंट:** KubSTU CTF 2026 Autumn

## 📌 कार्य

बास्केटबॉल अरीना के पास एक कॉफ़ी शॉप में घुसा, और बगल की मेज़ पर लैपटॉप के साथ एक आदमी बैठा था — हर अदा से NBA का स्काउट लग रहा था। स्क्रीन किन्हीं प्री-ड्राफ़्ट नोट्स से भरी थी। लगता है लीग में जल्द ही एक और रूसी शामिल होने वाला है। गुज़रते हुए मैंने फ़ोन से उसकी स्क्रीन की फ़ोटो खींच ली — पर फ़ोटो बिल्कुल धुँधली आई, पढ़ना नामुमकिन। OCR से गुज़ारा तो टेढ़ा-मेढ़ा निकला। क्या तुम पता लगा पाओगे कि बात किसकी हो रही है? चाहिए: उपनाम और नाम, पिक नंबर, और वह टीम जिसके लिए वह NBA समर लीग खेलेगा।

**फ़ाइलें:** [scout_note.txt](../../../assets/OSINT/Latte%20Art/scout_note.txt)

फ़्लैग का उदाहरण — `KubSTU{Леброн_Джеймс:01:Cleveland_Cavaliers}`

## 🏁 समाधान

### चरण 1. संकेतों की सूची बनाना

वह सब कुछ लिख लेते हैं जिसे सर्च क्वेरी में बदला जा सके:

| आर्टिफ़ैक्ट से उद्धरण | इससे क्या मिलता है |
| --- | --- |
| «hear his name off that stage», «rights», «2nd-rd» | **NBA ड्राफ़्ट**, दूसरा राउंड |
| «Federation-wise… only the **eleventh** of his kind» | ड्राफ़्ट के इतिहास में देश का 11वाँ प्रतिनिधि |
| «rights are already promised south, **to Texas**. Same night» | ड्राफ़्ट के तुरंत बाद अधिकार एक Texas क्लब को गए |
| «registered club paperwork reads **Krasnodar**» | क्लब संबद्धता |
| «million-plus city **on the Don**», «different river, different town» | गृहनगर ≠ क्लब का शहर (डिस्ट्रैक्टर) |
| «Verify against **Summer** numbers… in **Vegas**» | NBA समर लीग, Las Vegas |
| «G», «6'8"», «jumbo lead guard» | सत्यापन के लिए पोज़िशन और लंबाई |

मुख्य धुरी है यह संयोजन — **eleventh + Federation + Krasnodar**। इसी से पहली क्वेरी बनती है।

---
### चरण 2. खिलाड़ी की पहचान

#### क्वेरी 1

```
11-й россиянин в истории НБА выбранный на драфте
```

**स्रोत:** Championat, «Vsevolod Ishchenko — NBA इतिहास में ड्राफ़्ट होने वाला 11वाँ रूसी» - https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html

सीधा निशाना: लेख में सभी ड्राफ़्ट हुए रूसियों की पूरी सूची दी गई है, जहाँ 2026 के 56वें पिक पर Vsevolod Ishchenko दर्ज है, और बताया गया है कि शुरुआत में यह पिक "Los Angeles Lakers" का था, जिसके बाद क्लब ने इसे "Dallas Mavericks" को ट्रेड कर दिया।

#### क्वेरी 2 (वैकल्पिक रास्ता, अगर पहली न चले)

```
Локомотив-Кубань игрок драфт НБА 2026
```

**स्रोत:** sports.ru - https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html

Vsevolod Ishchenko (198 सेमी, 21 वर्ष), Krasnodar के "Lokomotiv" का खिलाड़ी, 2026 ड्राफ़्ट में 56वें नंबर पर चुना गया; वह Krasnodar क्लब का उत्पाद है और 15 साल की उम्र से "Lokomotiv-Kuban" सिस्टम में है।

#### परिकल्पना का सत्यापन

नोट के संकेतों को मिले प्रोफ़ाइल से मिलाते हैं:

| नोट में संकेत | तथ्य | ✓ |
| --- | --- | --- |
| «G» (गार्ड) | शूटिंग गार्ड | ✓ |
| «6'8"» (~203 सेमी) | 198 सेमी — करीब, स्काउटिंग अनुमान गोल कर देते हैं | ~ |
| «2nd-rd» | दूसरा राउंड | ✓ |
| «Krasnodar» | "Lokomotiv-Kuban" | ✓ |
| «Texas» | "Dallas Mavericks" | ✓ |
| eleventh | 11वाँ रूसी | ✓ |

**फ़्लैग का घटक मिला:** `Всеволод_Ищенко`

---
### चरण 3. पिक नंबर — और स्रोतों में पेच

#### क्वेरी 3

```
Всеволод Ищенко драфт НБА 2026 какой номер пика
```

पिक नंबर — **56** — सभी स्रोतों से एकमत पुष्टि होती है। पर **उसे चुना किसने**, इसे मीडिया अलग-अलग बताता है, और इसे समझना ज़रूरी है:

| स्रोत | शब्दावली |
| --- | --- |
| sports.ru 🔗 [लिंक](https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html) | «56वें नंबर पर **«Lakers»** ने चुना» |
| Sportbox 🔗 [लिंक](https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas) | «**Chicago** ने Ishchenko को 56वें नंबर पर चुना… पूर्व समझौते के अनुसार खिलाड़ी को "Los Angeles Lakers" जाना था» |
| Vedomosti 🔗 [लिंक](https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina) | «"Dallas Mavericks" क्लब ने Ishchenko को 56वें नंबर पर चुना… मूलतः 56वें पर "Chicago Bulls" को चुनना था, पर क्लब ने यह एसेट "Los Angeles Lakers" को, और उन्होंने "Dallas" को ट्रेड कर दिया» |

**अधिकारों की असली शृंखला:** Chicago → Lakers → Dallas, सब ड्राफ़्ट की रात को। इसीलिए आर्टिफ़ैक्ट में लिखा है «the club that actually calls him up won't keep him five minutes» और «don't let the on-stage cap fool you» — नोट ठीक इसी गड़बड़ी का वर्णन करता है।

**फ़्लैग का घटक मिला:** `56`

---
### चरण 4. समर लीग में टीम

आर्टिफ़ैक्ट सीधे दिशा बताता है: «Verify against Summer numbers… If the passing shows up in Vegas»।

#### क्वेरी 4

```
Ищенко Летняя лига НБА 2026 статистика
```

**स्रोत:** Championat, अंतिम मैच की रिपोर्ट - https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html

समर लीग में "Dallas" का अंतिम, पाँचवाँ मैच "New York" के ख़िलाफ़ था और 110:88 की जीत के साथ समाप्त हुआ; Ishchenko के आँकड़े — 27 मिनट में 15 अंक, तीन रिबाउंड, सात असिस्ट, एक स्टील और एक ब्लॉक, जो टूर्नामेंट में अंक और असिस्ट के मामले में उसका व्यक्तिगत रिकॉर्ड बना। टूर्नामेंट का औसत: 27.5 मिनट में 9.5 अंक, 4.4 रिबाउंड, 3.0 असिस्ट, 1.2 स्टील और 0.8 ब्लॉक।

#### मैचों की पूरी तस्वीर (सत्यापन हेतु)

| मैच | परिणाम | Ishchenko | स्रोत |
| --- | --- | --- | --- |
| vs "Golden State" (डेब्यू) | हार | 7 अंक | [Championat](https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html) |
| vs "Lakers" | हार | 8 अंक | [metaratings](https://metaratings.ru/news/dallas-obygral-oklakhomu-v-matche-letnei-ligi-nba-ishenko-nabral-12-ochkov-634938/) |
| vs "Memphis" | 96:88 जीत | 6 अंक, 5 रिब, 4 असि, 3 ब्लॉक, 32 मिन | [Championat](https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html) |
| vs "Oklahoma" | 97:87 जीत | 12 अंक, 7 रिब, 3 असि, 2 स्टील, 29 मिन | [Sport-Express](https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/) |
| vs "New York" | 110:88 जीत | **15 अंक, 7 असिस्ट**, 27 मिन | [Championat](https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html) |

पाँचों मैचों में Ishchenko ने **"Dallas Mavericks"** के लिए खेला।

**फ़्लैग का घटक मिला:** `Dallas_Mavericks`

---
### फ़्लैग जोड़ना

```
KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}
```

| घटक | मान | कहाँ से |
| --- | --- | --- |
| उपनाम | Ищенко | 11 रूसियों की सूची |
| नाम | Всеволод | वहीं से |
| पिक नंबर | 56 | 2026 ड्राफ़्ट रिपोर्टें |
| समर लीग टीम | Dallas Mavericks | समर लीग बॉक्स-स्कोर |

---
### स्रोतों की पूरी सूची

1. **Championat** — ड्राफ़्ट इतिहास में 11वाँ रूसी (पूरी सूची) https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html
2. **sports.ru** — 56वें नंबर पर चयन, "Dallas" को ट्रेड https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html
3. **Vedomosti.Sport** — Chicago → Lakers → Dallas शृंखला का विश्लेषण https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina
4. **Sportbox** — «Chicago ने चुना… और "Dallas" को ट्रेड किया» https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas
5. **Championat** — समर लीग का अंतिम मैच, व्यक्तिगत रिकॉर्ड, औसत आँकड़े https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html
6. **Championat** — "Memphis" के साथ मैच, Cameron Boozer की मार्किंग https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html
7. **Sport-Express** — "Oklahoma" के साथ मैच 17.07.2026 https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/
8. **Championat** — "Golden State" के साथ डेब्यू मैच https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html
9. **Kommersant** — लगातार दूसरे साल ड्राफ़्ट में एक रूसी https://www.kommersant.ru/doc/8765152
10. **sports.ru (ब्लॉग)** — सभी ड्राफ़्ट हुए रूसियों का सारांश + बिना ड्राफ़्ट वाले (Mozgov, Shved, Bazarevich) https://www.sports.ru/basketball/blogs/3415820.html

**फ़्लैग:** `KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}`
