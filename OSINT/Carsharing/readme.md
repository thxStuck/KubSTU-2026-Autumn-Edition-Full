![carsharing_hq.jpg](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/main/OSINT/Carsharing/media/carsharing_hq.jpg)

Однажды после пар взяли с друзьями каршеринг и покатались по центру. Машину бросили где-то в тени деревьев и сфоткались на память. Пока искали следующую, начисто забыли, где оставили эту. Помоги вспомнить: где мы её припарковали? Достаточно будет координат с 4-мя знаками после запятой.

Формат флага - `KubSTU{xx.xxxx_yy.yyyy}`

---

### Шаг 1. Метаданные

Первым делом проверяем EXIF: иногда телефон сохраняет в фото GPS-координаты, и тогда таск решается за минуту.

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

Координат съёмки в метаданных нет. Остаётся только геолокация по самому изображению.

### Шаг 2. Что видно на фото

**Город.** На заднем стекле машины наклейка каршеринга «Ситидрайв». Сам по себе каршеринг работает во многих городах, но соревнование краснодарское, а «Ситидрайв» в Краснодаре есть. Логично начать поиск с него.

**Здание.** Справа невысокий дом из красного кирпича с декоративной кладкой: пилястры, профилированный карниз. Стены побелены, штукатурка местами облупилась, на окнах решётки. Это дореволюционная застройка старого Екатеринодара. Такие дома почти не встречаются в спальных районах (ФМР, ЮМР, КМР, Гидрострой) и сосредоточены в историческом центре.

**Профиль улицы.** Машина стоит на проезжей части. Дальше идёт широкая земляная полоса со старыми крупными деревьями, за ней узкий асфальтовый тротуар, а дом стоит сразу за тротуаром, по красной линии. Так устроены улицы старой квартальной сетки центра: узкая дорога, газоны с деревьями, малоэтажные дома вплотную к тротуару.

**Окружение.** На фоне нет многоэтажек, вокруг только низкая застройка и деревья. Это ещё раз указывает на старый центр, а не на новые районы.

**Вывод:** фото сделано в историческом центре Краснодара, в квартале старой застройки между улицей Северной и Постовой. Дальше ищем конкретный дом на панорамах.

### Шаг 3. Рассматриваем панораму

Спустя какое-то время мы приходим к панораме по координатам **45.025635, 38.981874**. Дом здесь выглядит крайне похожим на искомый, однако панорама за 2025 год не сильно информативна. Если проверить панорамы за другие года, то 2021 год будет лучше всех.

Начинаем сравнивать.

![carsharing_paint.jpg](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/main/OSINT/Carsharing/media/carsharing_paint.jpg)

У нас сходится 5 элементов, следовательно мы нашли нужные координаты.

Теперь сдаём флаг - `KubSTU{45.0256, 38.9818}`
