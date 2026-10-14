# Black box

> **类别：** Forensics · **赛事：** KubSTU CTF 2026 Autumn · **难度：** hard

## 📌 题目

本题的所有文件可以在[这里](https://drive.google.com/drive/folders/1wnsoE0BqrU3iZm8F9DOz7U3h58ox9q1N?usp=sharing)找到。

## 🏁 解答

### TL;DR — 链条

| # | 内容 | 关键痕迹 | 结果 |
|---|---|---|---|
| 1 | 初步分流 | 5 份报告 / 5 个 tlog，但卡上只有 4 个日志，`LASTLOG.TXT=104` | 日志 105 被删除 |
| 2 | 雕刻 105 | FAT 中空闲且密集含 `A3 95` 的簇，FMT 取自 101（不是 100！） | `00000105.BIN` |
| 3 | 文件系统时间线 | mtime 102–104 + `LASTLOG` = 16.09 22:14–22:17 | 坠毁后当晚被编辑，101 干净 |
| 4 | 航迹伪造 | 风三角：GPS 对比 `ARSP`+`ATT`+`XKF2` | 第 2–5 天被伪造，残差 ~50 m/s |
| 5 | 真实 PoI | `ORGN`+`XKF1`（第 2、4、5 天），空速航位推算（第 3 天） | geohash6 `ubh030` |
| 6 | 密钥 | `FW_NAV.LUA` 中的配方，`CMD` `CId=18` `Prm4` 中的字节 | 口令 → AES-256-CBC → flag |

顺带：坠毁原因是电池耗尽（`ERR 6/1 → 6/2 → RTL → ERR 12`），而非“发动机故障”。

---

### 环境

```bash
sudo apt install -y sleuthkit mtools openssl
pip install --user pymavlink numpy
```

### 1. 初步分流

```bash
sha256sum -c evidence/sd_card.dd.sha256
mdir -i evidence/sd_card.dd -/ ::/APM            # без root; или mount -o ro,loop
mcopy -i evidence/sd_card.dd -s ::/APM/LOGS ::/APM/SCRIPTS .
cat LOGS/LASTLOG.TXT                             # 104
cp LOGS/0000010?.BIN .
for f in 0000010?.BIN; do echo -n "$f  "; mavlogdump.py --types MSG $f 2>/dev/null | grep -m1 -o 'ArduPlane V[0-9.]*'; done
```

* 报告和 tlog 各 5 份，日志只有 4 个（`100`…`104`），`LASTLOG.TXT = 104`。第五次飞行
  被删除。
* `00000100.BIN` 是在 **ArduPlane 4.4.4** 上的一次地面运行，101–104 则在 **4.5.7**
  上。这在搬运 FMT 时会成为一个陷阱。
* `SCRIPTS/NOTES.TXT` 含有 `KubSTU{n0t_th3_r34l_…}`——一个假 flag。`strings` 在整个
  镜像中都能找到同类的诱饵字符串。

### 2. 恢复 `00000105.BIN`

```bash
fls -f fat32 -rd evidence/sd_card.dd
# r/r * 4405767:  APM/SCRIPTS/_AV_CACH      <- удалённый .nav_cache, понадобится в шаге 6
```

`-f fat32` 是必需的：该卷有 65,470 个簇，低于规范规定的 FAT32 阈值（65,525），TSK 的
自动识别会返回 `Cannot determine file system type`。Linux 的 vfat 驱动和 mtools 会
查看 BPB，从而毫无问题地挂载该卷。

此列表中**没有** `00000105.BIN`。如果一个已删除条目的大小非零而起始簇为零，TSK 会将其
丢弃。因此我们用原始转储查看 `LOGS` 目录：

```bash
istat -f fat32 evidence/sd_card.dd $(ifind -f fat32 -n /APM/LOGS evidence/sd_card.dd) | grep -A1 Sectors
# 276400 276401 ...
blkcat -f fat32 evidence/sd_card.dd 276400 1 | hexdump -C | sed -n '17,18p'
# 00000100  e5 30 30 30 30 31 30 35  42 49 4e 20 00 64 6d 45  |.0000105BIN .dmE|
# 00000110  30 5d 31 5d 00 00 6d 45  30 5d 00 00 4f aa 18 02  |0]1]..mE0]..O...|
```

槽位 8：创建于 `0x5d30/0x456d` = 16.09.2026 08:43:26，起始簇 hi/lo = `0000/0000`，
大小 `0x0218AA4F` = 35,170,895 字节。沿 FAT 链无从恢复：簇已被释放，文件已碎片化。

卷几何（BPB）：扇区 512 字节，每簇 16 个扇区（8 KiB），2 个各 512 扇区的 FAT，数据从
扇区 1056 开始。日志主体为簇 **12864–15009** 和 **15018–17164**。它们之间有 8 个
**被占用**的 JPEG 簇（`IMG_0844.JPG`），因此 `foremost`/`photorec` 会把图片拼进日志
里。第一个簇被新的 `LASTLOG.TXT` 覆盖，随之丢失的还有 `FMT` 块（类型 128，每条记录
89 字节）。尾部在一条消息中间被截断，并用零填充。

恢复方法：取那些在 FAT 中**空闲**且密集填充 `A3 95` 同步标记的簇。“FAT 中空闲”这一
判据本身就把 JPEG 过滤掉了。在开头我们拼上一个**同一固件**的捐赠者（donor）的 FMT 块，
即取自 101。捐赠者 100（4.4.4）给出的类型编号不同，字段会悄悄错位。

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

### 3. 文件系统时间线

```bash
fls -f fat32 -z UTC -lr evidence/sd_card.dd | grep -E 'BIN|LASTLOG'
# или таймлайн:
fls -f fat32 -z UTC -r -m / evidence/sd_card.dd > body.txt
mactime -b body.txt -z UTC | grep -E 'BIN|LASTLOG'
```

FAT 存储时间时不带时区，TSK 默认将其视为**主机**的本地时间。自动驾驶仪写入的是 UTC：
`00000101.BIN` 的 crtime 08:41 与日志中 08:40 UTC 的启动相符。因此 `-z UTC` 要加在
`fls` 里，而不仅仅在 `mactime` 里。否则在 MSK 的机器上一切都会偏移 3 小时。对于
`mount`，对应的是 `-o tz=UTC`。

| 文件 | crtime | **mtime** |
|---|---|---|
| `00000101.BIN` | 12.09 08:41 | 12.09 10:29 |
| `00000102.BIN` | 13.09 08:38 | **16.09 22:14** |
| `00000103.BIN` | 14.09 08:44 | **16.09 22:14** |
| `00000104.BIN` | 15.09 08:40 | **16.09 22:15** |
| `LASTLOG.TXT`  | 12.09 | **16.09 22:17** |

三个不同日期的日志在坠毁后当晚三分钟内被修改。这是在 PC 上的批量编辑。日志 101 未被
触碰，因此可作为校验方法的基准。

### 4–5. 航迹伪造与真实的兴趣点

操作者改写了 `GPS`、`POS`、`CAM` 以及 `CMD` 的坐标，并在第 3 天还改写了 `XKF1`。未被
触碰的是 `ARSP`（IAS）、`ATT.Yaw`、`XKF2.VWN/VWE`（来自 EKF 估计的风）以及 `ORGN`。

* **检测器。** 对于飞机，地速等于沿航向的空速加上风。由 GPS 导出的风
  （`Spd`、`GCrs` − TAS·[cos ψ, sin ψ]）必须与 `XKF2` 相符。在诚实的飞行中残差小于
  1 m/s。在伪造窗口内它约为 50 m/s，而根据 `evidence/weather/` 中的 METAR/ERA5，风为
  3–13 m/s。
* **重建。** 伪造窗口为 ±4 分钟。若 `XKF1.PN/PE` 与 GPS 不一致（未被改写），则从中取
  航迹。若一致（被改写），则由空速航位推算航迹：从进入窗口的那一点起
  ∫(TAS·[cos ψ, sin ψ] + W_xkf2)dt。
* **盘旋中心。** 每个点都沿速度矢量的法线方向偏离中心 R = V/ω。这些“投票”的中位数对
  不同半径圆堆叠具有稳健性。

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

第 3 天按航位推算会产生约 100 m 的误差，但四天都落在同一个 geohash-6 单元
（~1.2 × 0.6 km）内。

**坠毁原因**（顺带）：

```bash
mavlogdump.py --types ERR,MODE,BAT 00000105.BIN 2>/dev/null | grep -E 'ERR|MODE' | tail -4
```

`ERR 6/1`（电池，电量低）发生在 09:51，6 分钟后 `ERR 6/2`（严重）和 `MODE 11`
（RTL，`Rsn 6` = failsafe）。返航途中有 12–13 m/s 的逆风，10:10 时 `ERR 12/2`——坠毁。
`RCOU` 上的下陷是由放电引起的，而非发动机故障。

### 6. 密钥与容器

在 `SCRIPTS/FW_NAV.LUA`（模块 `fw_nav_assist`）中，一个配方写在注释里，一个 base64
容器写在变量 `C` 中：

```
marks = { floor(item.p4*255) for each NAV_LOITER_TURNS, ordered by p3 }
cell  = geohash(loiter_centre_lat, loiter_centre_lon, 6)
pass  = base64( marks[i] ~ sha256(cell)[i] ),  i = 1..24
plain = aes-256-cbc -pbkdf2 -d
```

* 日志中的 `NAV_LOITER_TURNS` 是 `CId = 18` 的 `CMD`。影子命令通过非零的 `Prm4` 和
  带小数的 `Prm1` 暴露自己。第 2–5 天每天 6 个，共 24 字节。**其中六个只存在于恢复出来
  的 105 中。**
* 这些命令的 `Lat/Lng` 也被改写到走廊里。单元要取自第 5 步，而不是取自命令。否则口令
  会是有效的 base64 却是错误的。

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

容器可通过三种途径获得，结果逐字节相同（672 字节）：

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

解密后的任务书中的第一个目标距计算出的中心约 ~40 m，距 `XKF1` 估计值仅几米。这是对
第 5 步的独立确认。

---

### 解题通常在哪里出错

| 错误 | 症状 |
|---|---|
| `fls` 不加 `-f fat32` | `Cannot determine file system type` |
| 只通过 `fls -d` 查找 105 | 输出中没有该条目（TSK 丢弃了它），需要原始目录转储 |
| FMT 取自 `00000100.BIN`（4.4.4） | 日志 105 能“解析”，但数值无意义（纬度出现在高度字段里） |
| 基于签名的雕刻（`foremost`/`photorec`） | JPEG（簇 15010–15017）出现在日志内部，或在第一个片段处中断 |
| 未去除尾部的零 | pymavlink 中涌现大量 `bad header 0x0000` |
| 单元取自 `GPS`/`CAM`/`CMD` | 走廊航迹 → 错误的 geohash → `bad decrypt` |
| 仅凭单日求中心（尤其第 3 天） | 可能错选单元；需要所有日期保持一致 |
| 忽略日志 105 | 口令 24 字节中缺少 6 字节 |
| `mount` 不加 `tz=UTC` / `fls` 不加 `-z UTC` | 时间“偏移”±3 小时，但**相对**图景不变 |
| 来自 `strings` / `NOTES.TXT` 的 `KubSTU{…}` | 假 flag |

其他“噪声”发现与解题无关：某个日志中的 `ERR 11`（GPS glitch），`/IMAGES` 编号中的
缺口（部分帧恰好在盘旋窗口内被删除），第 3 天报告中 6 分钟的出入（UTC 对 UTC+3）。

**ATT&CK for ICS:** T0856 Spoof Reporting Message, T0872 Indicator Removal on Host.

**Flag：** `KubSTU{f0ur_qu13t_d4ys_th3n_0n3_l0ud_cr4sh_th3_w1nd_tr14ngl3_n3v3r_l13s}`
