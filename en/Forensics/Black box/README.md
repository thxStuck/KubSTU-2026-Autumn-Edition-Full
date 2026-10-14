# Black box

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn · **Difficulty:** hard

## 📌 Task

All files for the task can be found [here](https://drive.google.com/drive/folders/1wnsoE0BqrU3iZm8F9DOz7U3h58ox9q1N?usp=sharing).

## 🏁 Solution

### TL;DR — the chain

| # | What | Key artifact | Result |
|---|---|---|---|
| 1 | Triage | 5 reports / 5 tlogs, but 4 logs on the card, `LASTLOG.TXT=104` | log 105 deleted |
| 2 | Carving 105 | free-in-FAT clusters with `A3 95`, FMT from 101 (not 100!) | `00000105.BIN` |
| 3 | FS timeline | mtime 102–104 + `LASTLOG` = 16.09 22:14–22:17 | edited in the evening after the crash, 101 clean |
| 4 | Track forgery | wind triangle: GPS vs `ARSP`+`ATT`+`XKF2` | days 2–5 forged, residual ~50 m/s |
| 5 | True PoI | `ORGN`+`XKF1` (days 2,4,5), air dead reckoning (day 3) | geohash6 `ubh030` |
| 6 | Key | recipe in `FW_NAV.LUA`, bytes in `CMD` `CId=18` `Prm4` | password → AES-256-CBC → flag |

Along the way: the cause of the crash is battery depletion (`ERR 6/1 → 6/2 → RTL → ERR 12`),
not "engine failure".

---

### Environment

```bash
sudo apt install -y sleuthkit mtools openssl
pip install --user pymavlink numpy
```

### 1. Triage

```bash
sha256sum -c evidence/sd_card.dd.sha256
mdir -i evidence/sd_card.dd -/ ::/APM            # без root; или mount -o ro,loop
mcopy -i evidence/sd_card.dd -s ::/APM/LOGS ::/APM/SCRIPTS .
cat LOGS/LASTLOG.TXT                             # 104
cp LOGS/0000010?.BIN .
for f in 0000010?.BIN; do echo -n "$f  "; mavlogdump.py --types MSG $f 2>/dev/null | grep -m1 -o 'ArduPlane V[0-9.]*'; done
```

* Reports and tlogs — 5 each, logs — 4 (`100`…`104`), `LASTLOG.TXT = 104`. The fifth
  flight was deleted.
* `00000100.BIN` — a ground run on **ArduPlane 4.4.4**, 101–104 — on **4.5.7**.
  This will be useful as a trap when transferring the FMT.
* `SCRIPTS/NOTES.TXT` contains `KubSTU{n0t_th3_r34l_…}` — a fake flag. The same kind of
  decoy strings are found by `strings` across the whole image.

### 2. Recovery of `00000105.BIN`

```bash
fls -f fat32 -rd evidence/sd_card.dd
# r/r * 4405767:  APM/SCRIPTS/_AV_CACH      <- удалённый .nav_cache, понадобится в шаге 6
```

`-f fat32` is mandatory: the volume has 65,470 clusters, which is below the FAT32
threshold per spec (65,525), and TSK autodetection returns
`Cannot determine file system type`. The Linux vfat driver and mtools look at the
BPB and mount the volume without problems.

This list does **not** contain `00000105.BIN`. TSK discards a deleted entry if it
has a nonzero size with a zero start cluster. So we look at the `LOGS` directory
with a raw dump:

```bash
istat -f fat32 evidence/sd_card.dd $(ifind -f fat32 -n /APM/LOGS evidence/sd_card.dd) | grep -A1 Sectors
# 276400 276401 ...
blkcat -f fat32 evidence/sd_card.dd 276400 1 | hexdump -C | sed -n '17,18p'
# 00000100  e5 30 30 30 30 31 30 35  42 49 4e 20 00 64 6d 45  |.0000105BIN .dmE|
# 00000110  30 5d 31 5d 00 00 6d 45  30 5d 00 00 4f aa 18 02  |0]1]..mE0]..O...|
```

Slot 8: created `0x5d30/0x456d` = 16.09.2026 08:43:26, start cluster
hi/lo = `0000/0000`, size `0x0218AA4F` = 35,170,895 bytes. There is nothing to
recover via the FAT chain: the clusters are freed, the file is fragmented.

Volume geometry (BPB): sector 512 bytes, 16 sectors per cluster (8 KiB), 2 FATs of
512 sectors each, data from sector 1056. The log body — clusters **12864–15009** and
**15018–17164**. Between them are 8 **occupied** JPEG clusters (`IMG_0844.JPG`),
so `foremost`/`photorec` will splice the picture inside the log. The first cluster
is overwritten by a new `LASTLOG.TXT`, and with it the `FMT` block (type 128,
89 bytes per record) is gone. The tail is cut off mid-message and padded with zeros.

Recovery method: take the clusters that are **free** in the FAT and densely packed
with the `A3 95` sync marker. The "free-in-FAT" criterion itself filters out the
JPEG. At the start we graft the FMT block from a donor **of the same firmware**, i.e.
from 101. Donor 100 (4.4.4) gives different type numbers, and fields silently shift.

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

### 3. FS timeline

```bash
fls -f fat32 -z UTC -lr evidence/sd_card.dd | grep -E 'BIN|LASTLOG'
# или таймлайн:
fls -f fat32 -z UTC -r -m / evidence/sd_card.dd > body.txt
mactime -b body.txt -z UTC | grep -E 'BIN|LASTLOG'
```

FAT stores time without a time zone, and TSK by default treats it as the **host's**
local time. The autopilot writes UTC: the crtime of `00000101.BIN` 08:41 matches the
boot in the log at 08:40 UTC. So `-z UTC` is needed in `fls`, not just in `mactime`.
Otherwise on an MSK machine everything shifts by 3 hours. For `mount` the analog is
`-o tz=UTC`.

| file | crtime | **mtime** |
|---|---|---|
| `00000101.BIN` | 12.09 08:41 | 12.09 10:29 |
| `00000102.BIN` | 13.09 08:38 | **16.09 22:14** |
| `00000103.BIN` | 14.09 08:44 | **16.09 22:14** |
| `00000104.BIN` | 15.09 08:40 | **16.09 22:15** |
| `LASTLOG.TXT`  | 12.09 | **16.09 22:17** |

Logs from three different days were modified within three minutes in the evening
after the crash. This is a batch edit on a PC. Log 101 is untouched, so it serves as
a reference for checking the method.

### 4–5. Track forgery and the true point of interest

The operator rewrote `GPS`, `POS`, `CAM` and the `CMD` coordinates, and on day 3 also
`XKF1`. Untouched are `ARSP` (IAS), `ATT.Yaw`, `XKF2.VWN/VWE` (wind from the EKF
estimate) and `ORGN`.

* **Detector.** For an airplane, ground speed equals airspeed along the heading plus
  wind. The wind derived from GPS (`Spd`,`GCrs` − TAS·[cos ψ, sin ψ]) must match
  `XKF2`. On an honest flight the residual is under 1 m/s. In the forgery window it is
  about 50 m/s, although per METAR/ERA5 in `evidence/weather/` the wind was 3–13 m/s.
* **Reconstruction.** The forgery window is ±4 min. If `XKF1.PN/PE` diverges from GPS
  (not rewritten), we take the track from it. If it matches (rewritten), we dead-reckon
  the track from airspeed: ∫(TAS·[cos ψ, sin ψ] + W_xkf2)dt from the point of entry
  into the window.
* **Loiter center.** Each point is offset from the center by R = V/ω along the normal
  to the velocity vector. The median of the "votes" is robust to a stack of circles of
  different radius.

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

Day 3 by dead reckoning gives an error of about 100 m, but all four days fall into the
same geohash-6 cell (~1.2 × 0.6 km).

**Cause of the crash** (along the way):

```bash
mavlogdump.py --types ERR,MODE,BAT 00000105.BIN 2>/dev/null | grep -E 'ERR|MODE' | tail -4
```

`ERR 6/1` (battery, low charge) at 09:51, 6 minutes later `ERR 6/2` (critical) and
`MODE 11` (RTL, `Rsn 6` = failsafe). On the way back a headwind of 12–13 m/s, and at
10:10 `ERR 12/2` — the crash. The dip on `RCOU` is caused by the discharge, not an
engine failure.

### 6. Key and container

In `SCRIPTS/FW_NAV.LUA` (module `fw_nav_assist`) a recipe is written in a comment and a
base64 container in the variable `C`:

```
marks = { floor(item.p4*255) for each NAV_LOITER_TURNS, ordered by p3 }
cell  = geohash(loiter_centre_lat, loiter_centre_lon, 6)
pass  = base64( marks[i] ~ sha256(cell)[i] ),  i = 1..24
plain = aes-256-cbc -pbkdf2 -d
```

* `NAV_LOITER_TURNS` in the log is a `CMD` with `CId = 18`. Shadow commands give
  themselves away by a nonzero `Prm4` and a fractional `Prm1`. 6 of them in each of days
  2–5, 24 bytes in total. **Six of them exist only in the recovered 105.**
* The `Lat/Lng` of these commands are also rewritten to the corridor. Take the cell from
  step 5, not from the commands. Otherwise the password comes out as valid base64 but
  wrong.

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

The container can be obtained in three ways, the result is byte-for-byte identical (672 bytes):

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

The first target in the decrypted tasking is ~40 m from the computed center, and within
a few meters of the `XKF1` estimates. This is independent confirmation of step 5.

---

### Where the solution usually breaks

| Error | Symptom |
|---|---|
| `fls` without `-f fat32` | `Cannot determine file system type` |
| searching for 105 only via `fls -d` | the entry is not in the output (TSK discards it), a raw directory dump is needed |
| FMT taken from `00000100.BIN` (4.4.4) | log 105 "parses", but the values are meaningless (latitude in the altitude field) |
| signature carving (`foremost`/`photorec`) | JPEG (clusters 15010–15017) inside the log or a break at the first fragment |
| tail zeros not trimmed | an avalanche of `bad header 0x0000` in pymavlink |
| cell from `GPS`/`CAM`/`CMD` | corridor track → wrong geohash → `bad decrypt` |
| center from a single day (especially day 3) | a cell miss is possible; consistency across all days is needed |
| log 105 ignored | 6 of the 24 password bytes are missing |
| `mount` without `tz=UTC` / `fls` without `-z UTC` | times "shift" by ±3 h, but the **relative** picture is the same |
| `KubSTU{…}` from `strings` / `NOTES.TXT` | fake flags |

Other "noise" findings are not relevant to the solution: `ERR 11` (GPS glitch) in one of
the logs, gaps in the `/IMAGES` numbering (some frames were deleted precisely in the
loiter windows), a 6-minute discrepancy in the day-3 report (UTC vs UTC+3).

**ATT&CK for ICS:** T0856 Spoof Reporting Message, T0872 Indicator Removal on Host.

**Flag:** `KubSTU{f0ur_qu13t_d4ys_th3n_0n3_l0ud_cr4sh_th3_w1nd_tr14ngl3_n3v3r_l13s}`
