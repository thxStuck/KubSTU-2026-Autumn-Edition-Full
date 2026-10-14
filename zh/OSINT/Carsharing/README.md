# Carsharing

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

![carsharing_hq.jpg](../../../assets/OSINT/Carsharing/carsharing_hq.jpg)

某天下课后，我和朋友租了一辆共享汽车，在市中心兜了一圈。我们把车停在了某处树荫下，并拍照留念。在找下一辆车的时候，我们完全忘了把这辆停在哪儿了。帮我们回忆一下：车停在哪里了？小数点后 4 位的坐标就够了。

Flag 格式 — `KubSTU{xx.xxxx_yy.yyyy}`

**文件：** [carsharing_hq.jpg](../../../assets/OSINT/Carsharing/carsharing_hq.jpg)

## 🏁 解答

### 第 1 步：元数据

首先检查 EXIF：有时手机会把 GPS 坐标保存进照片，那样题目一分钟就解完了。

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

元数据中没有拍摄坐标。只剩下靠图像本身来定位了。

### 第 2 步：照片里能看到什么

**城市。** 车后窗上贴着 "Citydrive"（Ситидрайв）共享汽车的贴纸。共享汽车在很多城市都有，但比赛来自 Krasnodar，而 Citydrive 在 Krasnodar 有业务。从这里开始搜索是合理的。

**建筑。** 右侧是一栋带装饰砌砖的红砖矮房：壁柱、带线脚的檐口。墙面刷白，灰泥多处剥落，窗户上装着护栏。这是老 Yekaterinodar 的革命前建筑。这类房子在住宅区（FMR、YuMR、KMR、Gidrostroy）几乎见不到，而集中在历史中心。

**街道剖面。** 车停在车行道上。再往前是一条种着高大老树的宽阔土带，其后是一条窄窄的沥青人行道，房子就紧贴人行道后方、立在建筑红线上。中心老街区网格的街道正是这样布置的：窄路、带树的草坪、紧贴人行道的低层房屋。

**周边环境。** 背景里没有高层建筑，四周只有低矮房屋和树木。这再次说明是老中心，而不是新城区。

**结论：** 照片拍摄于 Krasnodar 历史中心，位于 Severnaya 街和 Postovaya 街之间的老城街区。接下来我们在全景图上寻找那栋具体的房子。

### 第 3 步：查看全景图

过了一段时间，我们定位到坐标 **45.025635, 38.981874** 处的全景。这里的房子与我们要找的极为相似，不过 2025 年的全景信息量不大。如果查看其他年份的全景，2021 年的最好。

我们开始对比。

![carsharing_paint.jpg](../../../assets/OSINT/Carsharing/carsharing_paint.jpg)

我们对上了 5 个要素，因此找到了正确的坐标。

现在提交 flag — `KubSTU{45.0256, 38.9818}`

**Flag：** `KubSTU{45.0256, 38.9818}`
