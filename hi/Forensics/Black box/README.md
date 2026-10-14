# Black box

> **श्रेणी:** Forensics · **इवेंट:** KubSTU CTF 2026 Autumn · **कठिनाई:** hard

## 📌 कार्य

कार्य की सभी फ़ाइलें [यहाँ](https://drive.google.com/drive/folders/1wnsoE0BqrU3iZm8F9DOz7U3h58ox9q1N?usp=sharing) मिल सकती हैं।

## 🏁 समाधान

### TL;DR — शृंखला

| # | क्या | मुख्य आर्टिफ़ैक्ट | परिणाम |
|---|---|---|---|
| 1 | ट्रायाज | 5 रिपोर्ट / 5 tlog, पर कार्ड पर 4 लॉग, `LASTLOG.TXT=104` | लॉग 105 हटा दिया गया |
| 2 | 105 का कार्विंग | `A3 95` से भरे FAT में मुक्त क्लस्टर, FMT 101 से (100 से नहीं!) | `00000105.BIN` |
| 3 | FS टाइमलाइन | mtime 102–104 + `LASTLOG` = 16.09 22:14–22:17 | क्रैश के बाद शाम को संपादित, 101 साफ़ |
| 4 | ट्रैक जालसाज़ी | पवन त्रिकोण: GPS बनाम `ARSP`+`ATT`+`XKF2` | दिन 2–5 जाली, अवशेष ~50 m/s |
| 5 | असली PoI | `ORGN`+`XKF1` (दिन 2,4,5), वायु डेड रेकनिंग (दिन 3) | geohash6 `ubh030` |
| 6 | कुंजी | `FW_NAV.LUA` में रेसिपी, `CMD` `CId=18` `Prm4` में बाइट्स | पासवर्ड → AES-256-CBC → फ़्लैग |

रास्ते में: क्रैश का कारण बैटरी का ख़त्म होना है (`ERR 6/1 → 6/2 → RTL → ERR 12`), न कि
«इंजन की विफलता»।

---

### वातावरण

```bash
sudo apt install -y sleuthkit mtools openssl
pip install --user pymavlink numpy
```

### 1. ट्रायाज

```bash
sha256sum -c evidence/sd_card.dd.sha256
mdir -i evidence/sd_card.dd -/ ::/APM            # без root; или mount -o ro,loop
mcopy -i evidence/sd_card.dd -s ::/APM/LOGS ::/APM/SCRIPTS .
cat LOGS/LASTLOG.TXT                             # 104
cp LOGS/0000010?.BIN .
for f in 0000010?.BIN; do echo -n "$f  "; mavlogdump.py --types MSG $f 2>/dev/null | grep -m1 -o 'ArduPlane V[0-9.]*'; done
```

* रिपोर्ट और tlog — 5-5, लॉग — 4 (`100`…`104`), `LASTLOG.TXT = 104`. पाँचवीं उड़ान
  हटा दी गई।
* `00000100.BIN` — **ArduPlane 4.4.4** पर एक ग्राउंड रन, 101–104 — **4.5.7** पर।
  FMT स्थानांतरित करते समय यह एक जाल के रूप में काम आएगा।
* `SCRIPTS/NOTES.TXT` में `KubSTU{n0t_th3_r34l_…}` है — एक नकली फ़्लैग। इसी तरह की
  भ्रामक स्ट्रिंग्स पूरे इमेज में `strings` से मिलती हैं।

### 2. `00000105.BIN` की पुनर्प्राप्ति

```bash
fls -f fat32 -rd evidence/sd_card.dd
# r/r * 4405767:  APM/SCRIPTS/_AV_CACH      <- удалённый .nav_cache, понадобится в шаге 6
```

`-f fat32` अनिवार्य है: वॉल्यूम में 65,470 क्लस्टर हैं, जो स्पेक के अनुसार FAT32 की
सीमा (65,525) से कम है, और TSK का स्वतः-पहचान `Cannot determine file system type`
देता है। Linux का vfat ड्राइवर और mtools BPB को देखते हैं और वॉल्यूम को बिना समस्या के
माउंट कर देते हैं।

इस सूची में `00000105.BIN` **नहीं** है। TSK किसी हटाई गई एंट्री को छोड़ देता है यदि
उसका आकार शून्येतर हो पर आरंभिक क्लस्टर शून्य हो। इसलिए हम `LOGS` डायरेक्टरी को कच्चे
(raw) डंप से देखते हैं:

```bash
istat -f fat32 evidence/sd_card.dd $(ifind -f fat32 -n /APM/LOGS evidence/sd_card.dd) | grep -A1 Sectors
# 276400 276401 ...
blkcat -f fat32 evidence/sd_card.dd 276400 1 | hexdump -C | sed -n '17,18p'
# 00000100  e5 30 30 30 30 31 30 35  42 49 4e 20 00 64 6d 45  |.0000105BIN .dmE|
# 00000110  30 5d 31 5d 00 00 6d 45  30 5d 00 00 4f aa 18 02  |0]1]..mE0]..O...|
```

स्लॉट 8: बनाया गया `0x5d30/0x456d` = 16.09.2026 08:43:26, आरंभिक क्लस्टर
hi/lo = `0000/0000`, आकार `0x0218AA4F` = 35,170,895 बाइट्स। FAT शृंखला से कुछ भी
पुनर्प्राप्त करने को नहीं है: क्लस्टर मुक्त कर दिए गए हैं, फ़ाइल खंडित है।

वॉल्यूम ज्यामिति (BPB): सेक्टर 512 बाइट्स, प्रति क्लस्टर 16 सेक्टर (8 KiB), 512 सेक्टर
वाले 2 FAT, डेटा सेक्टर 1056 से। लॉग का मुख्य भाग — क्लस्टर **12864–15009** और
**15018–17164**। उनके बीच 8 **व्याप्त (occupied)** JPEG क्लस्टर हैं (`IMG_0844.JPG`),
इसलिए `foremost`/`photorec` तस्वीर को लॉग के अंदर जोड़ देंगे। पहला क्लस्टर नए
`LASTLOG.TXT` से अधिलेखित हो गया है, और उसके साथ `FMT` ब्लॉक (टाइप 128, प्रति रिकॉर्ड
89 बाइट्स) भी गायब हो गया। पूँछ संदेश के बीच में कट गई है और शून्यों से भरी गई है।

पुनर्प्राप्ति का तरीका: वे क्लस्टर लें जो FAT में **मुक्त** हैं और `A3 95` सिंक-मार्कर
से घनी तरह भरे हैं। «FAT में मुक्त» मानदंड स्वयं JPEG को छाँट देता है। शुरुआत में हम
**उसी फ़र्मवेयर** के डोनर से FMT ब्लॉक जोड़ देते हैं, यानी 101 से। डोनर 100 (4.4.4)
भिन्न टाइप नंबर देता है, और फ़ील्ड चुपचाप खिसक जाते हैं।

```python
#!/usr/bin/env python3
# carve105.py <sd_card.dd> <fmt_donor.BIN> <out.BIN>
# Free-in-FAT clusters dense with A3 95 -> body; FMT block grafted from donor.
import struct, sys
img, donor, out = open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read(), sys.argv[3]

bps, spc, res, nfat = *struct.unpack_from('<HBH', img, 11), img[16]
tot, fatsz = struct.unpack_from('<II', img, 32)
ds = (res + nfat * fatsz + spc - 1) // spc * spc
ncl, cb = (tot - ds) // spc, spc * bps
fat = struct.unpack_from(f'<{ncl + 2}I', img, res * bps)
off = lambda c: (ds + (c - 2) * spc) * bps
clu = lambda c: img[off(c):off(c) + cb]

body = b''.join(clu(c) for c in range(2, ncl + 2)
                if not fat[c] & 0x0FFFFFFF and clu(c).count(b'\xa3\x95') >= 20)

i = 0                                   # FMT prefix of donor (type 128, len 89)
while donor[i:i + 2] == b'\xa3\x95' and donor[i + 2] == 128:
    i += 89
k = next(j for j in range(len(body)) if body[j:j + 2] == b'\xa3\x95'
         and body.count(b'\xa3\x95', j, j + 4096) >= 20)
data = (donor[:i] + body[k:]).rstrip(b'\0')
open(out, 'wb').write(data)
print(f'{out}: {len(data)} bytes (FMT block {i} bytes from donor)')
```

```bash
python3 carve105.py evidence/sd_card.dd 00000101.BIN 00000105.BIN
# 00000105.BIN: 35165526 bytes (FMT block 2848 bytes from donor)
mavlogdump.py --types MSG 00000105.BIN 2>/dev/null | grep -i nav
# ... MSG {..., Message : NAV: link timeout, cache active}
```

### 3. FS टाइमलाइन

```bash
fls -f fat32 -z UTC -lr evidence/sd_card.dd | grep -E 'BIN|LASTLOG'
# или таймлайн:
fls -f fat32 -z UTC -r -m / evidence/sd_card.dd > body.txt
mactime -b body.txt -z UTC | grep -E 'BIN|LASTLOG'
```

FAT समय को टाइम ज़ोन के बिना संग्रहीत करता है, और TSK डिफ़ॉल्ट रूप से इसे **होस्ट** का
स्थानीय समय मानता है। ऑटोपायलट UTC लिखता है: `00000101.BIN` का crtime 08:41 लॉग में
08:40 UTC पर बूट से मेल खाता है। इसलिए `-z UTC` केवल `mactime` में नहीं, बल्कि `fls`
में भी चाहिए। अन्यथा MSK वाली मशीन पर सब कुछ 3 घंटे खिसक जाएगा। `mount` के लिए इसका
समतुल्य `-o tz=UTC` है।

| फ़ाइल | crtime | **mtime** |
|---|---|---|
| `00000101.BIN` | 12.09 08:41 | 12.09 10:29 |
| `00000102.BIN` | 13.09 08:38 | **16.09 22:14** |
| `00000103.BIN` | 14.09 08:44 | **16.09 22:14** |
| `00000104.BIN` | 15.09 08:40 | **16.09 22:15** |
| `LASTLOG.TXT`  | 12.09 | **16.09 22:17** |

तीन अलग-अलग दिनों के लॉग क्रैश के बाद शाम को तीन मिनट के भीतर संशोधित किए गए। यह PC पर
एक बैच संपादन है। लॉग 101 अछूता है, इसलिए यह विधि की जाँच के लिए संदर्भ (reference) का
काम करता है।

### 4–5. ट्रैक की जालसाज़ी और असली रुचि-बिंदु

ऑपरेटर ने `GPS`, `POS`, `CAM` और `CMD` निर्देशांक फिर से लिखे, और दिन 3 में `XKF1` भी।
अछूते हैं `ARSP` (IAS), `ATT.Yaw`, `XKF2.VWN/VWE` (EKF अनुमान से पवन) और `ORGN`।

* **डिटेक्टर।** विमान के लिए, भू-गति (ground speed) शीर्ष (heading) के साथ वायु-गति
  (airspeed) जमा पवन के बराबर होती है। GPS से व्युत्पन्न पवन
  (`Spd`,`GCrs` − TAS·[cos ψ, sin ψ]) को `XKF2` से मेल खाना चाहिए। ईमानदार उड़ान पर
  अवशेष 1 m/s से कम होता है। जालसाज़ी वाली खिड़की में यह लगभग 50 m/s है, हालाँकि
  `evidence/weather/` में METAR/ERA5 के अनुसार पवन 3–13 m/s थी।
* **पुनर्निर्माण।** जालसाज़ी की खिड़की ±4 मिनट है। यदि `XKF1.PN/PE` GPS से अलग है
  (फिर से नहीं लिखा गया), तो हम ट्रैक उसी से लेते हैं। यदि मेल खाता है (फिर से लिखा गया),
  तो हम ट्रैक को वायु-गति से डेड-रेकन करते हैं: खिड़की में प्रवेश-बिंदु से
  ∫(TAS·[cos ψ, sin ψ] + W_xkf2)dt।
* **लॉइटर केंद्र।** प्रत्येक बिंदु वेग सदिश के अभिलंब (normal) के साथ केंद्र से
  R = V/ω दूरी पर होता है। «वोटों» का माध्यिका (median) भिन्न त्रिज्या वाले वृत्तों के
  ढेर के प्रति दृढ़ (robust) रहता है।

```python
#!/usr/bin/env python3
# poi.py 00000101.BIN ... 00000105.BIN
# Per log: wind-triangle residual (GPS vs ARSP+ATT+XKF2) and, where the track is
# forged, the true loiter centre (XKF1 if intact, else air dead-reckoning).
import sys
import numpy as np
from pymavlink import mavutil
np.seterr(all='ignore')

B32 = '0123456789bcdefghjkmnpqrstuvwxyz'
def geohash(lat, lon, p=6):
    lat, lon = float(lat), float(lon)
    r, out, v, n, ev = [[-90., 90.], [-180., 180.]], '', 0, 0, 1
    while len(out) < p:
        x = lon if ev else lat
        mid = sum(r[ev]) / 2
        v = v * 2 + (x > mid); r[ev][x <= mid] = mid; ev ^= 1; n += 1
        if n == 5: out += B32[v]; v = n = 0
    return out

def load(path):
    m, d = mavutil.mavlink_connection(path), {}
    want = ['GPS', 'ATT', 'ARSP', 'XKF1', 'XKF2', 'ORGN', 'BARO']
    while (x := m.recv_match(type=want)) is not None:
        d.setdefault(x.get_type(), []).append(x.to_dict())
    return {k: {c: np.array([r[c] for r in v]) for c in v[0]} for k, v in d.items()}

I = lambda s, f, t: np.interp(t, s['TimeUS'] / 1e6, s[f])
yaw_at = lambda L, t: np.radians(np.interp(t, L['ATT']['TimeUS'] / 1e6,
                                           np.degrees(np.unwrap(np.radians(L['ATT']['Yaw'])))))
tas_at = lambda L, t, alt: I(L['ARSP'], 'Airspeed', t) / (1 - 2.25577e-5 * alt) ** 2.12794

def smooth(a, w):
    w |= 1; e = np.pad(a, w // 2, mode='edge')
    return np.convolve(e, np.ones(w) / w, 'valid')

def centre(t, n, e, vn, ve):
    w = max(3, int(3 / np.median(np.diff(t))))
    om = smooth(np.gradient(np.unwrap(np.arctan2(smooth(ve, w), smooth(vn, w))), t), w)
    v = np.hypot(vn, ve); r = v / np.where(om == 0, np.nan, om)
    ok = (abs(om) > .02) & (abs(r) > 150) & (abs(r) < 700)
    return np.median((n - r * ve / v)[ok]), np.median((e + r * vn / v)[ok])

res = []
for path in sys.argv[1:]:
    L = load(path); g = L['GPS']; t = g['TimeUS'] / 1e6
    yaw, tas, crs = yaw_at(L, t), tas_at(L, t, g['Alt']), np.radians(g['GCrs'])
    wn = g['Spd'] * np.cos(crs) - tas * np.cos(yaw) - I(L['XKF2'], 'VWN', t)
    we = g['Spd'] * np.sin(crs) - tas * np.sin(yaw) - I(L['XKF2'], 'VWE', t)
    resid = np.hypot(wn, we)
    line = f'{path}: wind residual max {resid.max():5.1f} m/s'
    bad = np.where(np.convolve(resid, np.ones(25) / 25, 'same') > 8)[0]
    if len(bad):
        w0, w1 = t[bad[0]] - 240, t[bad[-1]] + 240
        lat0, lon0, h0 = (float(L['ORGN'][f][0]) for f in ('Lat', 'Lng', 'Alt'))
        ml, mo = 111132., 111320. * np.cos(np.radians(lat0))
        gn, ge = (g['Lat'] - lat0) * ml, (g['Lng'] - lon0) * mo
        k1 = L['XKF1']; tk = k1['TimeUS'] / 1e6
        if abs(k1['PN'] - np.interp(tk, t, gn)).max() > 500:        # XKF1 intact
            m = (tk >= w0) & (tk <= w1)
            c = centre(tk[m], k1['PN'][m], k1['PE'][m], k1['VN'][m], k1['VE'][m]); src = 'XKF1'
        else:                                                         # XKF1 forged too
            ta = L['ATT']['TimeUS'] / 1e6; tt = ta[(ta >= w0) & (ta <= w1)]
            y, v = yaw_at(L, tt), tas_at(L, tt, I(L['BARO'], 'Alt', tt) + h0)
            vn = v * np.cos(y) + I(L['XKF2'], 'VWN', tt); ve = v * np.sin(y) + I(L['XKF2'], 'VWE', tt)
            dt = np.diff(tt, prepend=tt[0])
            n = np.cumsum(vn * dt) + np.interp(w0, t, gn); e = np.cumsum(ve * dt) + np.interp(w0, t, ge)
            c = centre(tt, n, e, vn, ve); src = 'air DR'
        lat, lon = lat0 + c[0] / ml, lon0 + c[1] / mo
        res.append((lat, lon))
        line += f'  FORGED  centre {lat:.5f},{lon:.5f} [{src}] {geohash(lat, lon)}'
    print(line)
if res:
    lat, lon = np.mean(res, axis=0)
    print(f'\nPoI {lat:.5f},{lon:.5f}  geohash6={geohash(lat, lon)}')
```

```bash
python3 poi.py 0000010[1-5].BIN 2>/dev/null
```

```
00000101.BIN: wind residual max   0.6 m/s
00000102.BIN: wind residual max  50.5 m/s  FORGED  centre 45.04671,39.42442 [XKF1] ubh030
00000103.BIN: wind residual max  52.3 m/s  FORGED  centre 45.04564,39.42333 [air DR] ubh030
00000104.BIN: wind residual max  50.2 m/s  FORGED  centre 45.04671,39.42445 [XKF1] ubh030
00000105.BIN: wind residual max  54.4 m/s  FORGED  centre 45.04672,39.42446 [XKF1] ubh030

PoI 45.04644,39.42416  geohash6=ubh030
```

दिन 3 डेड रेकनिंग से लगभग 100 m की त्रुटि देता है, पर चारों दिन एक ही geohash-6
सेल (~1.2 × 0.6 km) में आते हैं।

**क्रैश का कारण** (रास्ते में):

```bash
mavlogdump.py --types ERR,MODE,BAT 00000105.BIN 2>/dev/null | grep -E 'ERR|MODE' | tail -4
```

`ERR 6/1` (बैटरी, कम चार्ज) 09:51 पर, 6 मिनट बाद `ERR 6/2` (गंभीर) और `MODE 11`
(RTL, `Rsn 6` = failsafe)। वापसी के रास्ते में 12–13 m/s की सामने से हवा, और 10:10
पर `ERR 12/2` — क्रैश। `RCOU` पर गिरावट डिस्चार्ज के कारण है, न कि इंजन की विफलता के।

### 6. कुंजी और कंटेनर

`SCRIPTS/FW_NAV.LUA` (मॉड्यूल `fw_nav_assist`) में एक रेसिपी एक टिप्पणी में और एक
base64 कंटेनर चर `C` में लिखा है:

```
marks = { floor(item.p4*255) for each NAV_LOITER_TURNS, ordered by p3 }
cell  = geohash(loiter_centre_lat, loiter_centre_lon, 6)
pass  = base64( marks[i] ~ sha256(cell)[i] ),  i = 1..24
plain = aes-256-cbc -pbkdf2 -d
```

* लॉग में `NAV_LOITER_TURNS` एक `CMD` है जिसमें `CId = 18` है। छाया (shadow) कमांड
  अपने शून्येतर `Prm4` और भिन्नात्मक (fractional) `Prm1` से खुद को उजागर कर देते हैं।
  दिन 2–5 में से प्रत्येक में 6, कुल 24 बाइट्स। **इनमें से छह केवल पुनर्प्राप्त 105 में
  मौजूद हैं।**
* इन कमांड के `Lat/Lng` भी गलियारे (corridor) में फिर से लिखे गए हैं। सेल कमांड से
  नहीं, बल्कि चरण 5 से लें। अन्यथा पासवर्ड वैध base64 के रूप में निकलेगा पर ग़लत होगा।

```python
#!/usr/bin/env python3
# passgen.py <geohash6> 00000102.BIN ... 00000105.BIN   -- recipe from FW_NAV.LUA
import sys, hashlib, base64
from pymavlink import mavutil

marks = []
for path in sys.argv[2:]:
    m, cmds = mavutil.mavlink_connection(path), []
    while (x := m.recv_match(type='CMD')) is not None:
        if int(x.CId) == 18:                          # MAV_CMD_NAV_LOITER_TURNS
            cmds.append((x.Prm3, int(x.Prm4 * 255 + 1e-6)))
    marks += [b for _, b in sorted(cmds)]
mask = hashlib.sha256(sys.argv[1].encode()).digest()[:24]
print(base64.b64encode(bytes(a ^ b for a, b in zip(marks, mask))).decode())
```

```bash
PASS=$(python3 passgen.py ubh030 0000010[2-5].BIN 2>/dev/null); echo $PASS
# W+IHlDGtxh96SNBjniW4EUz3gj1pygXh
```

कंटेनर तीन तरीकों से प्राप्त किया जा सकता है, परिणाम बाइट-दर-बाइट समान है (672 बाइट्स):

```bash
# (а) удалённый .nav_cache по записи каталога (сектор 206800 = кластер 12861)
icat -f fat32 -r evidence/sd_card.dd 4405767 > nav_cache.bin

# (б) из Lua-скрипта (переменная C)
grep '^\.\."' SCRIPTS/FW_NAV.LUA | cut -d'"' -f2 | tr -d '\n' | base64 -d > nav_cache.bin

# (в) сигнатурой по сырому образу
grep -abo 'Salted__' evidence/sd_card.dd
# 105881600  копия A = тот же .nav_cache
# 105889792  копия B, повреждена: расшифровывается в мусор без флага
# 141469635  слово «Salted__» в комментарии FW_NAV.LUA
dd if=evidence/sd_card.dd of=nav_cache.bin bs=672 count=1 skip=105881600 iflag=skip_bytes status=none

openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -pass pass:$PASS -in nav_cache.bin
```

```json
{
  "tasking_id": "GRANIT-4",
  "operator_cover": "GeoLink pipeline survey C-62",
  "poi": [ { "name": "Granit-4 relay node", "lat": 45.04669, "lon": 39.42444, ... }, ... ],
  "flag": "KubSTU{f0ur_qu13t_d4ys_th3n_0n3_l0ud_cr4sh_th3_w1nd_tr14ngl3_n3v3r_l13s}"
}
```

डिक्रिप्ट किए गए टास्किंग में पहला लक्ष्य गणना किए गए केंद्र से ~40 m और `XKF1`
अनुमानों से कुछ मीटर के भीतर है। यह चरण 5 की स्वतंत्र पुष्टि है।

---

### समाधान आमतौर पर कहाँ टूटता है

| त्रुटि | लक्षण |
|---|---|
| `fls` बिना `-f fat32` के | `Cannot determine file system type` |
| 105 की खोज केवल `fls -d` से | एंट्री आउटपुट में नहीं है (TSK उसे छोड़ देता है), कच्चा डायरेक्टरी डंप चाहिए |
| FMT `00000100.BIN` (4.4.4) से लिया | लॉग 105 «पार्स» होता है, पर मान निरर्थक हैं (ऊँचाई फ़ील्ड में अक्षांश) |
| सिग्नेचर कार्विंग (`foremost`/`photorec`) | JPEG (क्लस्टर 15010–15017) लॉग के अंदर या पहले खंड पर टूटना |
| पूँछ के शून्य नहीं काटे गए | pymavlink में `bad header 0x0000` की बाढ़ |
| सेल `GPS`/`CAM`/`CMD` से | गलियारे का ट्रैक → ग़लत geohash → `bad decrypt` |
| केंद्र केवल एक दिन से (खासकर दिन 3) | सेल चूकने की संभावना; सभी दिनों में संगति चाहिए |
| लॉग 105 की अनदेखी | पासवर्ड के 24 में से 6 बाइट्स कम पड़ते हैं |
| `mount` बिना `tz=UTC` / `fls` बिना `-z UTC` के | समय ±3 घं «खिसक» जाते हैं, पर **सापेक्ष** तस्वीर वही रहती है |
| `strings` / `NOTES.TXT` से `KubSTU{…}` | नकली फ़्लैग |

अन्य «शोर» निष्कर्ष समाधान से संबंधित नहीं हैं: किसी एक लॉग में `ERR 11` (GPS glitch),
`/IMAGES` की संख्या में अंतराल (कुछ फ़्रेम ठीक लॉइटर खिड़कियों में हटाए गए), दिन 3 की
रिपोर्ट में 6 मिनट का अंतर (UTC बनाम UTC+3)।

**ATT&CK for ICS:** T0856 Spoof Reporting Message, T0872 Indicator Removal on Host.

**फ़्लैग:** `KubSTU{f0ur_qu13t_d4ys_th3n_0n3_l0ud_cr4sh_th3_w1nd_tr14ngl3_n3v3r_l13s}`
