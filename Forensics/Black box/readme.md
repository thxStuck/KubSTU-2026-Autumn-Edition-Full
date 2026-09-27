# «Чёрный ящик»

**Категория:** Digital Forensics · **Сложность:** hard · **Флаг:** `KubSTU{...}`

## TL;DR — цепочка

| # | Что | Ключевой артефакт | Результат |
|---|---|---|---|
| 1 | Триаж | 5 актов / 5 tlog, но 4 лога на карте, `LASTLOG.TXT=104` | лог 105 удалён |
| 2 | Карвинг 105 | свободные в FAT кластеры с `A3 95`, FMT из 101 (не 100!) | `00000105.BIN` |
| 3 | Таймлайн ФС | mtime 102–104 + `LASTLOG` = 16.09 22:14–22:17 | правка вечером после падения, 101 чист |
| 4 | Подделка трека | ветровой треугольник: GPS vs `ARSP`+`ATT`+`XKF2` | дни 2–5 подделаны, невязка ~50 м/с |
| 5 | Истинная PoI | `ORGN`+`XKF1` (дни 2,4,5), воздушное счисление (день 3) | geohash6 `ubh030` |
| 6 | Ключ | рецепт в `FW_NAV.LUA`, байты в `CMD` `CId=18` `Prm4` | пароль → AES-256-CBC → флаг |

Попутно: причина крушения — разряд АКБ (`ERR 6/1 → 6/2 → RTL → ERR 12`), а не
«отказ двигателя».

---

## Окружение

```bash
sudo apt install -y sleuthkit mtools openssl
pip install --user pymavlink numpy
```

## 1. Триаж

```bash
sha256sum -c evidence/sd_card.dd.sha256
mdir -i evidence/sd_card.dd -/ ::/APM            # без root; или mount -o ro,loop
mcopy -i evidence/sd_card.dd -s ::/APM/LOGS ::/APM/SCRIPTS .
cat LOGS/LASTLOG.TXT                             # 104
cp LOGS/0000010?.BIN .
for f in 0000010?.BIN; do echo -n "$f  "; mavlogdump.py --types MSG $f 2>/dev/null | grep -m1 -o 'ArduPlane V[0-9.]*'; done
```

* Актов и tlog — по 5, логов — 4 (`100`…`104`), `LASTLOG.TXT = 104`. Пятый
  вылет удалён.
* `00000100.BIN` — наземная гонка на **ArduPlane 4.4.4**, 101–104 — на **4.5.7**.
  Это пригодится как ловушка при переносе FMT.
* `SCRIPTS/NOTES.TXT` содержит `KubSTU{n0t_th3_r34l_…}` — ложный флаг. Такие же
  подсадные строки находит `strings` по всему образу.

## 2. Восстановление `00000105.BIN`

```bash
fls -f fat32 -rd evidence/sd_card.dd
# r/r * 4405767:  APM/SCRIPTS/_AV_CACH      <- удалённый .nav_cache, понадобится в шаге 6
```

`-f fat32` обязателен: у тома 65 470 кластеров, это меньше порога FAT32 по
спецификации (65 525), и автоопределение TSK выдаёт
`Cannot determine file system type`. Linux-драйвер vfat и mtools смотрят на
BPB и монтируют том без проблем.

В этом списке **нет** `00000105.BIN`. TSK отбрасывает удалённую запись, если у
неё ненулевой размер при нулевом стартовом кластере. Поэтому смотрим каталог
`LOGS` сырым дампом:

```bash
istat -f fat32 evidence/sd_card.dd $(ifind -f fat32 -n /APM/LOGS evidence/sd_card.dd) | grep -A1 Sectors
# 276400 276401 ...
blkcat -f fat32 evidence/sd_card.dd 276400 1 | hexdump -C | sed -n '17,18p'
# 00000100  e5 30 30 30 30 31 30 35  42 49 4e 20 00 64 6d 45  |.0000105BIN .dmE|
# 00000110  30 5d 31 5d 00 00 6d 45  30 5d 00 00 4f aa 18 02  |0]1]..mE0]..O...|
```

Слот 8: создан `0x5d30/0x456d` = 16.09.2026 08:43:26, стартовый кластер
hi/lo = `0000/0000`, размер `0x0218AA4F` = 35 170 895 байт. По цепочке FAT
восстановить нечего: кластеры освобождены, файл фрагментирован.

Геометрия тома (BPB): сектор 512 байт, 16 секторов в кластере (8 КиБ), 2 FAT по
512 секторов, данные с сектора 1056. Тело лога — кластеры **12864–15009** и
**15018–17164**. Между ними 8 **занятых** кластеров JPEG (`IMG_0844.JPG`),
поэтому `foremost`/`photorec` вклеят картинку внутрь лога. Первый кластер
перезаписан новым `LASTLOG.TXT`, и вместе с ним пропал блок `FMT` (тип 128,
89 байт на запись). Хвост оборван посреди сообщения и добит нулями.

Способ восстановления: берём кластеры, которые в FAT **свободны** и плотно
набиты синхромаркером `A3 95`. Критерий «свободен в FAT» сам отсекает JPEG. В
начало пришиваем блок FMT из донора **той же прошивки**, то есть из 101. Донор
100 (4.4.4) даёт другие номера типов, и поля молча съезжают.

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

## 3. Таймлайн ФС

```bash
fls -f fat32 -z UTC -lr evidence/sd_card.dd | grep -E 'BIN|LASTLOG'
# или таймлайн:
fls -f fat32 -z UTC -r -m / evidence/sd_card.dd > body.txt
mactime -b body.txt -z UTC | grep -E 'BIN|LASTLOG'
```

FAT хранит время без часового пояса, и TSK по умолчанию трактует его как
местное время **хоста**. Автопилот пишет UTC: crtime `00000101.BIN` 08:41
совпадает с загрузкой в логе в 08:40 UTC. Поэтому `-z UTC` нужен в `fls`, а не
только в `mactime`. Иначе на машине с MSK всё сдвинется на 3 часа. Для
`mount` аналог — `-o tz=UTC`.

| файл | crtime | **mtime** |
|---|---|---|
| `00000101.BIN` | 12.09 08:41 | 12.09 10:29 |
| `00000102.BIN` | 13.09 08:38 | **16.09 22:14** |
| `00000103.BIN` | 14.09 08:44 | **16.09 22:14** |
| `00000104.BIN` | 15.09 08:40 | **16.09 22:15** |
| `LASTLOG.TXT`  | 12.09 | **16.09 22:17** |

Логи за три разных дня изменены за три минуты вечером после падения. Это
пакетная правка на ПК. Лог 101 не тронут, поэтому он служит эталоном для
проверки метода.

## 4–5. Подделка трека и истинная точка интереса

Оператор переписал `GPS`, `POS`, `CAM` и координаты `CMD`, а в дне 3 ещё и
`XKF1`. Не тронуты `ARSP` (IAS), `ATT.Yaw`, `XKF2.VWN/VWE` (ветер по оценке EKF)
и `ORGN`.

* **Детектор.** У самолёта путевая скорость равна воздушной скорости по курсу
  плюс ветер. Ветер, выведенный из GPS (`Spd`,`GCrs` − TAS·[cos ψ, sin ψ]),
  должен совпадать с `XKF2`. На честном полёте невязка меньше 1 м/с. В окне
  подделки она около 50 м/с, хотя по METAR/ERA5 в `evidence/weather/` ветер был
  3–13 м/с.
* **Реконструкция.** Окно подделки ±4 мин. Если `XKF1.PN/PE` расходится с GPS
  (не переписан), берём трек из него. Если совпадает (переписан), трек
  счисляем по воздушной скорости: ∫(TAS·[cos ψ, sin ψ] + W_xkf2)dt от точки
  входа в окно.
* **Центр барражирования.** Каждая точка отстоит от центра на R = V/ω по
  нормали к вектору скорости. Медиана «голосов» устойчива к стопке кругов
  разного радиуса.

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

День 3 по счислению даёт ошибку около 100 м, но все четыре дня попадают в одну
ячейку geohash-6 (~1,2 × 0,6 км).

**Причина крушения** (попутно):

```bash
mavlogdump.py --types ERR,MODE,BAT 00000105.BIN 2>/dev/null | grep -E 'ERR|MODE' | tail -4
```

`ERR 6/1` (батарея, низкий заряд) в 09:51, через 6 минут `ERR 6/2` (критический)
и `MODE 11` (RTL, `Rsn 6` = failsafe). На обратном пути встречный ветер
12–13 м/с, и в 10:10 `ERR 12/2` — крушение. Просадка на `RCOU` вызвана
разрядом, а не отказом двигателя.

## 6. Ключ и контейнер

В `SCRIPTS/FW_NAV.LUA` (модуль `fw_nav_assist`) записан рецепт в комментарии и
base64-контейнер в переменной `C`:

```
marks = { floor(item.p4*255) for each NAV_LOITER_TURNS, ordered by p3 }
cell  = geohash(loiter_centre_lat, loiter_centre_lon, 6)
pass  = base64( marks[i] ~ sha256(cell)[i] ),  i = 1..24
plain = aes-256-cbc -pbkdf2 -d
```

* `NAV_LOITER_TURNS` в логе — это `CMD` с `CId = 18`. Теневые команды выдают
  себя ненулевым `Prm4` и дробным `Prm1`. По 6 штук в каждом из дней 2–5,
  всего 24 байта. **Шесть из них есть только в восстановленном 105.**
* `Lat/Lng` этих команд тоже переписаны на коридор. Ячейку брать из шага 5, а не
  из команд. Иначе пароль получится валидным base64, но неверным.

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

Контейнер можно получить тремя путями, результат побайтно одинаковый (672 байта):

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

Первая цель в расшифрованном задании отстоит от вычисленного центра на
~40 м, а от оценок по `XKF1` — на единицы метров. Это независимое
подтверждение шага 5.

---

## Где обычно ломается решение

| Ошибка | Симптом |
|---|---|
| `fls` без `-f fat32` | `Cannot determine file system type` |
| поиск 105 только через `fls -d` | записи нет в выводе (TSK её отбрасывает), нужен сырой дамп каталога |
| FMT взят из `00000100.BIN` (4.4.4) | лог 105 «парсится», но значения бессмысленные (широта в поле высоты) |
| сигнатурный карвинг (`foremost`/`photorec`) | JPEG (кластеры 15010–15017) внутри лога или обрыв на первом фрагменте |
| не отрезаны нули хвоста | лавина `bad header 0x0000` в pymavlink |
| ячейка из `GPS`/`CAM`/`CMD` | трек коридора → неверный geohash → `bad decrypt` |
| центр по одному дню (особенно день 3) | возможен промах ячейки; нужна согласованность всех дней |
| проигнорирован лог 105 | не хватает 6 из 24 байт пароля |
| `mount` без `tz=UTC` / `fls` без `-z UTC` | времена «съезжают» на ±3 ч, но **относительная** картина та же |
| `KubSTU{…}` из `strings` / `NOTES.TXT` | ложные флаги |

Прочие «шумовые» находки не относятся к решению: `ERR 11` (GPS glitch) в одном
из логов, пропуски в нумерации `/IMAGES` (часть кадров удалена именно в окнах
барражирования), расхождение в 6 минут в акте за день 3 (UTC против UTC+3).

**ATT&CK for ICS:** T0856 Spoof Reporting Message, T0872 Indicator Removal on Host.
