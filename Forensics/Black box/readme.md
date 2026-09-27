# «Чёрный ящик»

**Категория:** Digital Forensics

**Сложность:** hard

**Формат флага:** `KubSTU{...}`

---

## Что нам выдали

```
evidence/sd_card.dd            посекторный образ microSD полётного контроллера
evidence/sd_card.dd.sha256     контрольная сумма образа
evidence/gcs_laptop/tlogs/     пять журналов телеметрии наземной станции (.tlog)
evidence/gcs_laptop/*.plan     полётное задание (маршрут коридора)
evidence/gcs_laptop/*.param    резервная копия параметров
evidence/gcs_laptop/acts/      пять актов сдачи-приёмки
evidence/weather/              METAR и реанализ ветра за пять суток
evidence/crash_site/           протокол осмотра места происшествия, фото обломков
```

**Легенда.** Подрядчик ООО «ГеоЛинк» ежедневно с 12 по 16 сентября 2026 года выполнял
аэрофотосъёмочное обследование линейной части магистрального газопровода
(коридор длиной 62 км) беспилотным воздушным судном самолётного типа
«Кречет-24» (ArduPlane 4.5.7).

16 сентября на пятом вылете борт не вернулся. Оператор в тот же вечер
обнаружил обломки, извлёк карту памяти и подал заявление о страховом
случае («отказ силовой установки, ветер, штатная работа до последней
минуты»).

На следующий день служба безопасности сельскохозяйственного предприятия, расположенного в стороне
от коридора, сообщила, что четыре дня подряд примерно в одно время над
объектом фиксировался аппарат, круживший 4-7 минут на высоте около 700 м.
На пятый день он не появился - он упал.

Оператор настаивает, что маршрут не нарушался: «вот журналы, смотрите сами».
Телеметрия действительно чистая. Но актов сдачи-приёмки - пять, журналов
наземной станции - пять, а бортовых журналов на карте - четыре, и файл
LASTLOG.TXT утверждает, что последним был вылет № 104.

ЗАДАЧА
------
Установить, что происходило в течение пяти суток; определить координаты
объекта, вокруг которого строились заходы; выяснить действительную причину
падения; восстановить и прочитать полезную нагрузку, оставшуюся на борту.
Флаг находится внутри неё.


---

## Подготовка окружения

Всё делается в Linux (Ubuntu, Kali, или Windows + WSL). Понадобятся:

```bash
# системные утилиты (Debian/Ubuntu/Kali). sleuthkit — набор форензик-команд.
sudo apt update
sudo apt install -y sleuthkit openssl coreutils python3-pip

# python-библиотеки: pymavlink (чтение логов ArduPilot + утилита mavlogdump.py),
# numpy (математика), pyfatfs (чтение FAT32 без монтирования — запасной путь)
pip install --user pymavlink numpy pyfatfs
```

Что чем является:

| Инструмент | Зачем |
|---|---|
| `sha256sum` | проверить, что образ не побился |
| `mount` | подключить образ как диск и ходить по файлам |
| `mmls`, `fls`, `istat`, `blkls` | форензик-обзор ФС из The Sleuth Kit (без монтирования) |
| `mavlogdump.py` | распечатать сообщения бортового лога (ставится вместе с pymavlink) |
| `grep`, `dd`, `cut` | поиск/вырезание кусков файла |
| `openssl` | расшифровать контейнер |
| Python + numpy | три маленьких скрипта для расчётов |

> Если команда `mavlogdump.py` «не найдена», запускайте её полным путём —
> `~/.local/bin/mavlogdump.py …` — или как модуль:
> `python3 -m pymavlink.tools.mavlogdump …` (в зависимости от версии).

Дальше подразумевается, что вы в каталоге пакета (там, где лежит `evidence/`):

```bash
cd ~/dist_ru        # или dist_en — образ в них одинаковый
```

---

## Шаг 1. Осмотр: чего не хватает

**1.1. Проверяем целостность образа.** `sha256sum -c` читает файл `.sha256` и
сверяет контрольную сумму:

```bash
sha256sum -c evidence/sd_card.dd.sha256
# sd_card.dd: OK
```

**1.2. Смотрим содержимое карты.** Образ — это FAT32-том. Подключим его «только
для чтения». Точку монтирования (пустой каталог) нужно создать заранее, иначе
`mount` скажет `mount point does not exist`:

```bash
sudo mkdir -p /mnt/sd
sudo mount -o ro,loop evidence/sd_card.dd /mnt/sd
ls -la /mnt/sd/APM/LOGS/
```

Вывод:

```
00000100.BIN  00000101.BIN  00000102.BIN  00000103.BIN  00000104.BIN  LASTLOG.TXT
```

```bash
cat /mnt/sd/APM/LOGS/LASTLOG.TXT      # какой лог автопилот считает последним
# 104
```

> `-o ro,loop` — «только чтение» (`ro`, чтобы не испортить улику) через
> loop-устройство (`loop`, подключить файл как диск). По окончании работы
> отмонтируйте: `sudo umount /mnt/sd`.
>
> **Нет прав root или вы под Windows?** Возьмите файлы без монтирования — на
> чистом Python:
> ```bash
> python3 - <<'EOF'
> from pyfatfs.PyFatFS import PyFatFS
> fs = PyFatFS('evidence/sd_card.dd')
> print(fs.listdir('/APM/LOGS'))
> for n in ('00000100','00000101','00000102','00000103','00000104'):
>     open(n+'.BIN','wb').write(fs.openbin('/APM/LOGS/'+n+'.BIN').read())
> print('логи 100-104 извлечены в текущий каталог')
> EOF
> ```

**1.3. Первая нестыковка.** Актов сдачи-приёмки — пять
(`ls evidence/gcs_laptop/acts/`), журналов НСУ — пять
(`ls evidence/gcs_laptop/tlogs/`), а бортовых логов на карте — **четыре**, и
`LASTLOG.TXT = 104`. Значит, лог пятого вылета `00000105.BIN` существовал и был
удалён. **Вернуть его — задача Шага 2.**

**1.4. Смотрим версии прошивки.** В каждом логе первые сообщения `MSG` — это
баннер загрузки. Распечатаем их утилитой `mavlogdump.py` (сначала извлеките
логи в текущий каталог, см. врезку в 1.2, либо копируйте из `/mnt/sd/...`):

```bash
mavlogdump.py --types MSG 00000100.BIN | head -1
# 2026-09-12 08:40:20.00: MSG {TimeUS : ..., Message : ArduPlane V4.4.4 (b7c02e51)}

mavlogdump.py --types MSG 00000101.BIN | grep -i arduplane
# 2026-09-12 08:40:20.00: MSG {..., Message : ArduPlane V4.5.7 (3a1f9d72)}
```

Запомните: `00000100.BIN` — это короткая наземная гонка двигателя на **другой
версии прошивки (4.4.4)**. Логи 101–104 (и удалённый 105) — на 4.5.7. Это
пригодится и станет ловушкой на Шаге 2.

---

## Шаг 2. Восстановление удалённого лога `00000105.BIN`

### Что такое бортовой лог (DataFlash)

Лог ArduPilot — это поток сообщений. Каждое начинается с двух байт-маркера
`A3 95`, потом байт типа, потом данные:

```
0xA3 0xA5  <тип>  <данные...>
```

Сообщения типа `FMT` (тип 128) идут **в начале файла** и описывают формат всех
остальных типов. Поэтому парсер сначала читает таблицу `FMT`, а уже потом
понимает остальное.

### Три проблемы пятого лога

1. **Файл фрагментирован** — лежит двумя кусками, между которыми вклинен снимок
   `IMG_0844.JPG` (карта была почти заполнена, свободное место рваное).
2. **Начало затёрто** — на освободившиеся кластеры лёг новый `LASTLOG.TXT`
   («104»), и вместе с началом уничтожен блок `FMT`.
3. **Хвост оборван** — удар о землю обесточил борт на середине сообщения.

Посмотреть на удалённую запись можно утилитой `fls` из sleuthkit
(`-r` — рекурсивно, `-d` — только удалённое):

```bash
fls -o 0 -rd evidence/sd_card.dd | grep -i '\.BIN'
# ... 00000105.BIN (удалён, стартовый кластер потерян)
```

Обычный «карвинг по сигнатуре» (`foremost`, `scalpel`, `photorec`) здесь даёт
**битый файл**: берёт только первый кусок и вклеивает внутрь JPEG. Нужен ручной
разбор — он в одном скрипте ниже.

### Скрипт восстановления (копируйте целиком)

Сохраните в файл `recover_105.py` (например: `nano recover_105.py`, вставьте,
`Ctrl+O`, `Enter`, `Ctrl+X`) и запустите `python3 recover_105.py`. Рядом должен
лежать извлечённый интактный лог `00000101.BIN` — он донор таблицы `FMT`.

```python
#!/usr/bin/env python3
# recover_105.py — восстановление удалённого фрагментированного лога 00000105.BIN
# Требуется: рядом лежит извлечённый интактный лог 00000101.BIN (та же прошивка 4.5.7).
import struct

img = open('evidence/sd_card.dd', 'rb').read()

# --- читаем геометрию FAT32 из загрузочного сектора (первые 512 байт) ---
bps   = struct.unpack_from('<H', img, 11)[0]      # байт в секторе (512)
spc   = img[13]                                    # секторов в кластере (16 -> кластер 8 КБ)
res   = struct.unpack_from('<H', img, 14)[0]      # резервных секторов до таблицы FAT
nfat  = img[16]                                    # сколько копий таблицы FAT
fatsz = struct.unpack_from('<I', img, 36)[0]      # размер одной FAT в секторах
tot   = struct.unpack_from('<I', img, 32)[0]      # всего секторов в томе
data_start = ((res + nfat*fatsz) + spc - 1)//spc*spc   # сектор начала области данных
nclus  = (tot - data_start)//spc                   # сколько всего кластеров
cbytes = spc*bps                                   # размер кластера в байтах
fat = struct.unpack_from('<%dI' % (nclus+2), img, res*bps)   # сама таблица FAT

def cluster(c):                                    # вернуть байты кластера номер c
    off = (data_start + (c-2)*spc)*bps
    return img[off:off+cbytes]

# 1) ТЕЛО ЛОГА = кластеры, помеченные в FAT как СВОБОДНЫЕ (файл удалён),
#    но фактически набитые маркерами A3 95. Кластеры JPEG заняты в FAT и
#    отсекаются сами собой — «ловушка склейки картинки» не срабатывает.
body_clusters = [c for c in range(2, nclus+2)
                 if (fat[c] & 0x0FFFFFFF) == 0 and cluster(c).count(b'\xa3\x95') >= 20]
body = b''.join(cluster(c) for c in sorted(body_clusters))
print(len(body_clusters), 'кластеров тела,', len(body), 'байт')

# 2) ТАБЛИЦА FMT — из интактного лога той же прошивки (101). Берём его префикс
#    до первого НЕ-FMT сообщения (то есть весь блок объявлений форматов).
donor = open('00000101.BIN', 'rb').read()
i = 0
while i < len(donor)-3:
    if donor[i] == 0xA3 and donor[i+1] == 0x95:
        if donor[i+2] != 128:        # 128 = FMT; первое не-FMT = конец блока
            break
        i += 89                       # длина одной записи FMT
    else:
        i += 1
header = donor[:i]

# 3) в теле пропускаем начальный мусор до первого плотного участка маркеров
start = next(k for k in range(len(body)-2)
             if body[k] == 0xA3 and body[k+1] == 0x95
             and body.count(b'\xa3\x95', k, k+4096) >= 20)

# 4) отрезаем нулевое дополнение последнего кластера (хвост оборван ударом),
#    иначе pymavlink завалит консоль сообщениями «bad header 0x0000»
data = (header + body[start:]).rstrip(b'\x00')
open('00000105.BIN', 'wb').write(data)
print('00000105.BIN записан:', len(data), 'байт')
```

> **Ловушка.** Донором `FMT` НЕЛЬЗЯ брать `00000100.BIN` — там прошивка 4.4.4 с
> другими номерами типов, и поля молча «поедут» (широта прочитается как высота).
> Мы взяли `00000101.BIN` (4.5.7) — правильно (см. баннеры из Шага 1.4).

Проверяем, что лог читается (`2>/dev/null` глушит служебные предупреждения):

```bash
mavlogdump.py --types MSG 00000105.BIN 2>/dev/null | head -3
# ...
# 2026-09-16 08:59:03.11: MSG {..., Message : NAV: link timeout, cache active}
```

Строка `NAV: link timeout, cache active` — уже интересная зацепка: во время
полёта что-то сработало «по потере связи». Держим в уме.

> **Про «bad header 0x0000».** Если пропустить шаг 4 скрипта или не глушить
> stderr, pymavlink выдаст тысячи строк `bad header 0x0000 at …` — это не
> ошибка, а нули в конце оборванного лога. Шаг 4 (`rstrip`) их убирает.

Теперь у нас пять читаемых логов: `00000101…00000105.BIN`.

---

## Шаг 3. Когда правили логи (времена файлов)

Оператор подделал логи **не в полёте, а вечером после падения**. Это видно по
временам файлов. Смонтируем с `tz=UTC`, чтобы `ls` показал время ровно как оно
записано на карте (без пересчёта под ваш часовой пояс):

```bash
sudo mount -o ro,loop,tz=UTC evidence/sd_card.dd /mnt/sd
ls -la --time-style=full-iso /mnt/sd/APM/LOGS/
```

Или без монтирования — командой `fls` (столбцы времени: изменён / доступ /
создан):

```bash
fls -o 0 -lr evidence/sd_card.dd | grep -iE '\.BIN|LASTLOG'
```

Времена изменения (mtime):

| файл | создан | **изменён** |
|---|---|---|
| `00000101.BIN` | 12.09 08:41 | 12.09 10:29 |
| `00000102.BIN` | 13.09 08:38 | **16.09 22:14** |
| `00000103.BIN` | 14.09 08:44 | **16.09 22:14** |
| `00000104.BIN` | 15.09 08:40 | **16.09 22:15** |
| `LASTLOG.TXT`  | 12.09 | **16.09 22:17** |

Четыре объекта за **разные сутки** изменены в пределах трёх минут вечером
16 сентября — через ~12 часов после падения. Это пакетная правка: карту
подключали к ПК и переписывали в файлах координаты. **Лог первого дня
(`00000101.BIN`) не тронут** — оператор начал подделывать со второго вылета.
Значит, день 1 — наш эталон честного полёта.

> **Про часовые пояса.** В FAT32 время хранится без пояса. Если смонтировать
> без `tz=UTC` на системе с UTC+3, `ls` прибавит 3 часа (`22:14` → `01:14`
> следующего дня) — это не порча данных, а пересчёт при отображении. Важна не
> сама метка, а то, что 102–104 и `LASTLOG` изменены **вместе**, а 101 — нет.

---

## Шаг 4. Доказательство подделки трека (ветровой треугольник)

Оператор переписал координаты `GPS`, `POS` и геотеги камеры `CAM`, чтобы трек
шёл по коридору. Но всё переписать нельзя — остались нетронутыми:

* `ARSP.Airspeed` — **воздушная** скорость (от трубки Пито);
* `ATT.Yaw` — курс (куда смотрит нос);
* `XKF2.VWN/VWE` — **бортовая оценка ветра**, которую автопилот считал в полёте.

**Идея.** Самолёт летит в воздушной массе, поэтому путевая скорость (по земле) =
воздушная скорость (по курсу) + ветер. Значит, зная записанный GPS-трек и
воздушную скорость с курсом, можно вычислить, **какой ветер был бы нужен**,
чтобы такой трек получился. На честном полёте этот «вычисленный» ветер совпадёт
с тем, что автопилот сам оценил (`XKF2`). А в окне подделки — разойдётся на
десятки м/с (никакого такого ветра в реальности не было — см. `evidence/weather/`,
там 3–6 м/с).

Скрипт `wind_check.py` (самодостаточный — читает все пять логов сам):

```python
#!/usr/bin/env python3
# wind_check.py — сравниваем ветер, вытекающий из GPS-трека, с бортовой оценкой
# ветра (XKF2). Совпадают -> честно; расходятся -> трек подделан.
import numpy as np
from pymavlink import mavutil

RHO0 = 1.225
def rho(alt): return RHO0 * (1 - 2.25577e-5*alt)**4.25588   # плотность воздуха
def rs(ts, vs, t): return np.interp(t, ts, vs)              # интерполяция по времени

def load(path, types):
    m = mavutil.mavlink_connection(path); d = {k: [] for k in types}
    while True:
        x = m.recv_match(type=types)
        if x is None: break
        d[x.get_type()].append(x.to_dict())
    return {k: {c: np.array([r[c] for r in v]) for c in v[0]} for k, v in d.items() if v}

for day, path in [(1,'00000101.BIN'),(2,'00000102.BIN'),(3,'00000103.BIN'),
                  (4,'00000104.BIN'),(5,'00000105.BIN')]:
    s = load(path, ['GPS','ATT','ARSP','XKF2'])
    t   = s['GPS']['TimeUS']/1e6
    yaw = np.radians(rs(s['ATT']['TimeUS']/1e6,
                        np.degrees(np.unwrap(np.radians(s['ATT']['Yaw']))), t))
    ias = rs(s['ARSP']['TimeUS']/1e6, s['ARSP']['Airspeed'], t)
    tas = ias*np.sqrt(RHO0/rho(s['GPS']['Alt']))            # истинная возд. скорость
    crs = np.radians(s['GPS']['GCrs'])
    iwn = s['GPS']['Spd']*np.cos(crs) - tas*np.cos(yaw)     # ветер из GPS, север
    iwe = s['GPS']['Spd']*np.sin(crs) - tas*np.sin(yaw)     # ветер из GPS, восток
    ewn = rs(s['XKF2']['TimeUS']/1e6, s['XKF2']['VWN'], t)  # ветер по EKF, север
    ewe = rs(s['XKF2']['TimeUS']/1e6, s['XKF2']['VWE'], t)  # ветер по EKF, восток
    resid = np.hypot(iwn-ewn, iwe-ewe)                      # расхождение
    verdict = 'ЧИСТО' if resid.max() < 5 else 'ПОДДЕЛКА'
    print(f'день {day}: расхождение ветра  макс={resid.max():5.1f} м/с   -> {verdict}')
```

```bash
python3 wind_check.py 2>/dev/null
```

```
день 1: расхождение ветра  макс=  0.6 м/с   -> ЧИСТО
день 2: расхождение ветра  макс= 50.5 м/с   -> ПОДДЕЛКА
день 3: расхождение ветра  макс= 52.3 м/с   -> ПОДДЕЛКА
день 4: расхождение ветра  макс= 50.2 м/с   -> ПОДДЕЛКА
день 5: расхождение ветра  макс= 54.4 м/с   -> ПОДДЕЛКА
```

День 1 чист — метод не даёт ложных срабатываний. Дни 2–5 подделаны. (Кто хочет
увидеть глазами — поставьте `MAVExplorer.py 00000102.BIN` и постройте графики
`GPS.Spd`, `ARSP.Airspeed`, `ATT.Yaw`.)

---

## Шаг 5. Что было на самом деле: точка интереса и причина падения

### 5.1. Причина падения — одними CLI-командами

Версия «отказ двигателя» не подтверждается. Смотрим события и питание пятого
лога:

```bash
mavlogdump.py --types ERR,MODE 00000105.BIN 2>/dev/null | tail -5
```

```
2026-09-16 09:51:42: ERR  {Subsys : 6, ECode : 1}          # аккумулятор: низкий заряд
2026-09-16 09:57:49: ERR  {Subsys : 6, ECode : 2}          # аккумулятор: критический
2026-09-16 09:57:49: MODE {Mode : 11, ModeNum : 11, Rsn : 6}   # -> режим RTL (возврат) по failsafe
2026-09-16 10:10:25: ERR  {Subsys : 12, ECode : 2}         # крушение
```

```bash
mavlogdump.py --types BAT 00000105.BIN 2>/dev/null | tail -1
# BAT {Volt : 14.32, Curr : 20.8, ...}   # напряжение просело до 14.3 В
```

Картина: `Subsys 6` — это батарея. Сначала низкий заряд, через 6 минут —
критический, срабатывает failsafe и режим `RTL` (возврат домой), а ещё через
~13 минут — `Subsys 12` (крушение). Пятый заход был самым долгим и посадил
батарею; на обратном пути встречный ветер (см. `evidence/weather/`, к полудню
12–13 м/с) добил её. Никакого «отказа двигателя» — банально не хватило энергии.

### 5.2. Где на самом деле кружил борт (точка интереса)

Координаты `GPS`, `POS`, `CAM` и даже координаты `Lat/Lng` теневых команд
подделаны на коридор. Настоящий трек надо **вычислить** по нетронутым данным:

* дни 2, 4, 5 — из `ORGN` (точка старта) + `XKF1.PN/PE` (позиция автопилота в
  метрах от старта);
* день 3 — там `XKF1` тоже переписан, поэтому счисляем путь по воздушной
  скорости и курсу с поправкой на ветер.

Центр окружности, вокруг которой борт нарезал круги, лежит в стороне от каждой
точки трека на один радиус — поэтому каждая точка «голосует» за центр, и медиана
даёт устойчивую оценку даже для стопки кругов разного радиуса.

Скрипт `triangulate.py` (самодостаточный):

```python
#!/usr/bin/env python3
# triangulate.py — истинный трек каждого "грязного" вылета и центр барражирования.
import numpy as np
from pymavlink import mavutil

M_LAT = 111132.0
def m_lon(lat): return 111320.0*np.cos(np.radians(lat))
def rs(ts, vs, t): return np.interp(t, ts, vs)
B32 = '0123456789bcdefghjkmnpqrstuvwxyz'

def geohash(lat, lon, prec=6):
    la, lo = [-90.,90.], [-180.,180.]; out=[]; bit=0; ch=0; even=True
    while len(out) < prec:
        if even:
            mid=(lo[0]+lo[1])/2
            if lon>mid: ch|=(16>>bit); lo[0]=mid
            else: lo[1]=mid
        else:
            mid=(la[0]+la[1])/2
            if lat>mid: ch|=(16>>bit); la[0]=mid
            else: la[1]=mid
        even=not even
        if bit<4: bit+=1
        else: out.append(B32[ch]); bit=0; ch=0
    return ''.join(out)

def load(path, types):
    m=mavutil.mavlink_connection(path); d={k:[] for k in types}
    while True:
        x=m.recv_match(type=types)
        if x is None: break
        d[x.get_type()].append(x.to_dict())
    return {k:{c:np.array([r[c] for r in v]) for c in v[0]} for k,v in d.items() if v}

def sm(a, w):
    w=max(3,w|1); pad=w//2
    ext=np.concatenate([np.full(pad,a[0]),a,np.full(pad,a[-1])])
    return np.convolve(ext,np.ones(w)/w,'same')[pad:pad+len(a)]

def orbit_centre(t, n, e, vn, ve):
    w=max(3,int(round(3.0/np.median(np.diff(t)))))
    crs=np.unwrap(np.arctan2(sm(ve,w),sm(vn,w)))
    omega=sm(np.gradient(crs,t),w); v=np.hypot(vn,ve)
    with np.errstate(divide='ignore',invalid='ignore'): r=v/omega
    ok=(np.abs(omega)>0.02)&(np.abs(r)>150)&(np.abs(r)<700)
    return np.median(n[ok]-r[ok]*ve[ok]/v[ok]), np.median(e[ok]+r[ok]*vn[ok]/v[ok])

def window(path):                      # окно подделки = где расходится ветер
    s=load(path,['GPS','ATT','ARSP','XKF2']); t=s['GPS']['TimeUS']/1e6
    yaw=np.radians(rs(s['ATT']['TimeUS']/1e6,np.degrees(np.unwrap(np.radians(s['ATT']['Yaw']))),t))
    tas=rs(s['ARSP']['TimeUS']/1e6,s['ARSP']['Airspeed'],t)*np.sqrt(1/(1-2.25577e-5*s['GPS']['Alt'])**4.25588)
    crs=np.radians(s['GPS']['GCrs'])
    iwn=s['GPS']['Spd']*np.cos(crs)-tas*np.cos(yaw); iwe=s['GPS']['Spd']*np.sin(crs)-tas*np.sin(yaw)
    resid=np.hypot(iwn-rs(s['XKF2']['TimeUS']/1e6,s['XKF2']['VWN'],t),
                   iwe-rs(s['XKF2']['TimeUS']/1e6,s['XKF2']['VWE'],t))
    idx=np.where(np.convolve(resid,np.ones(25)/25,'same')>8)[0]
    return t[idx[0]]-240, t[idx[-1]]+240

def centre(path):
    org=load(path,['ORGN'])['ORGN']; lat0=float(org['Lat'][0]); lon0=float(org['Lng'][0])
    k1=load(path,['XKF1'])['XKF1']; tk=k1['TimeUS']/1e6
    gps=load(path,['GPS'])['GPS']; tg=gps['TimeUS']/1e6
    rn=(gps['Lat']-lat0)*M_LAT; re=(gps['Lng']-lon0)*m_lon(lat0)
    w0,w1=window(path)
    if np.max(np.abs(k1['PN']-rs(tg,rn,tk)))>500:            # XKF1 не тронут
        m=(tk>=w0)&(tk<=w1)
        cn,ce=orbit_centre(tk[m],k1['PN'][m],k1['PE'][m],k1['VN'][m],k1['VE'][m])
    else:                                                   # XKF1 переписан -> счисление
        att=load(path,['ATT'])['ATT']; ar=load(path,['ARSP'])['ARSP']
        ba=load(path,['BARO'])['BARO']; k2=load(path,['XKF2'])['XKF2']
        ta=att['TimeUS']/1e6; m=(ta>=w0)&(ta<=w1); tt=ta[m]
        yaw=np.radians(np.degrees(np.unwrap(np.radians(att['Yaw'])))[m])
        alt=rs(ba['TimeUS']/1e6,ba['Alt'],tt)+float(org['Alt'][0])
        tas=rs(ar['TimeUS']/1e6,ar['Airspeed'],tt)*np.sqrt(1/(1-2.25577e-5*alt)**4.25588)
        vn=tas*np.cos(yaw)+rs(k2['TimeUS']/1e6,k2['VWN'],tt)
        ve=tas*np.sin(yaw)+rs(k2['TimeUS']/1e6,k2['VWE'],tt)
        dt=np.diff(tt,prepend=tt[0]); n=np.cumsum(vn*dt)+rs(tg,rn,w0); e=np.cumsum(ve*dt)+rs(tg,re,w0)
        cn,ce=orbit_centre(tt,n,e,vn,ve)
    return lat0+cn/M_LAT, lon0+ce/m_lon(lat0)

pts=[centre(p) for p in ['00000102.BIN','00000103.BIN','00000104.BIN','00000105.BIN']]
for i,(la,lo) in zip((2,3,4,5),pts):
    print(f'день {i}: центр {la:.5f}, {lo:.5f}  geohash6={geohash(la,lo)}')
lat=float(np.mean([p[0] for p in pts])); lon=float(np.mean([p[1] for p in pts]))
print(f'\nОБЪЕКТ ИНТЕРЕСА: {lat:.5f}, {lon:.5f}   geohash6 = {geohash(lat,lon)}')
```

```bash
python3 triangulate.py 2>/dev/null
```

```
день 2: центр 45.04671, 39.42442  geohash6=ubh030
день 3: центр 45.04564, 39.42333  geohash6=ubh030
день 4: центр 45.04671, 39.42445  geohash6=ubh030
день 5: центр 45.04672, 39.42446  geohash6=ubh030

ОБЪЕКТ ИНТЕРЕСА: 45.04644, 39.42416   geohash6 = ubh030
```

Все четыре дня сходятся в одну ячейку — **geohash-6 = `ubh030`**. Это и есть та
точка, вокруг которой борт кружил. Запомните ячейку — она нужна для пароля.

> По любым двум суткам точность не набирается — задание принципиально
> многодневное, поэтому нам и понадобилось восстановить все пять логов.

---

## Шаг 6. Ключ и флаг

### 6.1. Рецепт ключа — прямо в бортовом скрипте

На карте лежат два Lua-скрипта. Прочитаем «подозрительный»:

```bash
cat /mnt/sd/APM/scripts/fw_nav_assist.lua        # или из извлечённого каталога
```

В его комментариях описана схема пароля к контейнеру:

```
marks = { floor(Prm4 * 255) для каждой команды NAV_LOITER_TURNS, по радиусу Prm3 }
cell  = geohash(широта_центра, долгота_центра, 6)
mask  = sha256(cell)[:24]
pass  = base64( marks[i] XOR mask[i] )
plain = openssl aes-256-cbc -pbkdf2 -d
```

По-русски: в теневых миссиях (командах `NAV_LOITER_TURNS`) спрятаны байты (в
поле `Prm4`), а пароль — это те байты, «сложенные по XOR» с хешем geohash-ячейки
**настоящей** точки из Шага 5, переведённые в base64.

Убедиться, что теневые команды есть, можно так (в штатной миссии `Prm4` = 0, а у
теневых точек `Prm1` — дробное число витков):

```bash
mavlogdump.py --types CMD 00000105.BIN 2>/dev/null | grep 'CId : 18' | head -3
# CMD {..., CId : 18, Prm1 : 1.333, Prm3 : 310.0, Prm4 : 0.4196, Lat : 45.109, Lng : 39.448, ...}
```

> Обратите внимание: `Lat/Lng` этих команд (45.109, 39.448) — это **подделанный**
> коридор, а НЕ настоящая точка (45.046, 39.424) из Шага 5. Поэтому geohash
> нужно брать из `triangulate.py`, а не из координат команд — иначе получится
> неверный пароль.

### 6.2. Собираем пароль (один скрипт)

`make_key.py` — принимает ячейку из Шага 5 аргументом, читает четыре «грязных»
лога, собирает пароль:

```python
#!/usr/bin/env python3
# make_key.py <geohash-ячейка>   — собрать пароль по рецепту из fw_nav_assist.lua
import sys, hashlib, base64
from pymavlink import mavutil

cell = sys.argv[1] if len(sys.argv) > 1 else 'ubh030'    # ячейка из triangulate.py

def marks(path):
    m = mavutil.mavlink_connection(path); out = []
    while True:
        x = m.recv_match(type='CMD')
        if x is None: break
        if int(x.CId) == 18:                              # NAV_LOITER_TURNS
            out.append((x.Prm3, round(x.Prm4*255)))       # (радиус, спрятанный байт)
    return [b for _, b in sorted(out)]                    # порядок задаёт радиус Prm3

allmarks = bytes(sum((marks(p) for p in
    ['00000102.BIN','00000103.BIN','00000104.BIN','00000105.BIN']), []))
mask = hashlib.sha256(cell.encode()).digest()[:24]
passphrase = base64.b64encode(bytes(a ^ b for a, b in zip(allmarks, mask))).decode()
print('пароль:', passphrase)
```

```bash
python3 make_key.py ubh030 2>/dev/null
# пароль: W+IHlDGtxh96SNBjniW4EUz3gj1pygXh
```

> Шесть из 24 байт лежат **только в пятом логе** — том, что мы восстанавливали на
> Шаге 2. Без него пароль не собрать.

### 6.3. Достаём контейнер и расшифровываем — CLI

Контейнер `.nav_cache` удалён, но остался в неразмеченном пространстве, причём в
двух копиях. Найдём все места, где начинается зашифрованный блок openssl
(сигнатура `Salted__`):

```bash
grep -abo 'Salted__' evidence/sd_card.dd
# 105881600:Salted__     <- копия A (целая)
# 105889792:Salted__     <- копия B (оборвана ударом, не расшифруется)
# 141469635:Salted__     <- ещё фрагмент
```

> `grep -abo` печатает смещение (в байтах) каждого совпадения. Первое число —
> позиция в файле.

Вырежем копию A (её длина 672 байта) командой `dd` и расшифруем паролем из 6.2:

```bash
dd if=evidence/sd_card.dd of=cache_A.bin bs=672 count=1 skip=105881600 \
   iflag=skip_bytes status=none

openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
    -pass pass:W+IHlDGtxh96SNBjniW4EUz3gj1pygXh -in cache_A.bin
```

> `dd` копирует кусок файла: `skip=105881600 iflag=skip_bytes` — начать с этого
> байта, `bs=672 count=1` — взять 672 байта. `openssl enc -d` — расшифровать
> (`-d`), алгоритм `aes-256-cbc`, вывод ключа из пароля `-pbkdf2 -iter 100000`.

Вывод:

```json
{
  "tasking_id": "GRANIT-4",
  "poi": [
    { "name": "Granit-4 relay node", "priority": 1,
      "lat": 45.04669, "lon": 39.42444, "note": "primary; five passes 12-16 Sep" },
    ...
  ],
  "next_window": "2026-09-19T06:00:00Z",
  "flag": "KubSTU{f0ur_qu13t_d4ys_th3n_0n3_l0ud_cr4sh_th3_w1nd_tr14ngl3_n3v3r_l13s}"
}
```

Первым в списке целей стоит та самая точка `45.04669, 39.42444` из Шага 5 — это
подтверждает, что мы всё нашли верно.

> Если хочется автоматом перебрать все кандидаты — вот цикл: он вырезает каждый
> и пробует пароль, флаг покажет только рабочая копия A:
> ```bash
> for off in $(grep -abo 'Salted__' evidence/sd_card.dd | cut -d: -f1); do
>     dd if=evidence/sd_card.dd of=c.bin bs=4096 count=1 skip=$off iflag=skip_bytes status=none
>     echo "=== $off ==="
>     openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
>         -pass pass:W+IHlDGtxh96SNBjniW4EUz3gj1pygXh -in c.bin 2>/dev/null | grep -a 'KubSTU{'
> done
> ```

---

## Флаг

```
KubSTU{f0ur_qu13t_d4ys_th3n_0n3_l0ud_cr4sh_th3_w1nd_tr14ngl3_n3v3r_l13s}
```

---

## Ловушки (и почему они не работают)

* `00000100.BIN` — наземная гонка на прошивке 4.4.4. Если взять её донором `FMT`
  для пятого лога — поля поедут. Всегда сверяйте баннер прошивки (Шаг 1.4).
* «Отказ двигателя» из протокола — в логе есть просадка на выходе `RCOU`, но это
  следствие разряда батареи (`ERR Subsys 6`), а не причина.
* `ERR Subsys 11` (`GPS_GLITCH`) в одном из логов выглядит «естественным сбоем»,
  но к подделке отношения не имеет.
* Расхождение 6 минут во времени посадки в акте за 3-й день — это часовые пояса
  (бортовые логи и метео — в UTC; акты и протоколы — в местном UTC+3), а не
  подлог.
* Пропуски в нумерации `/IMAGES` — частично штатный брак; целенаправленно
  удалённые кадры отличаются тем, что попадают в окна барражирования.
* На карте есть строки вида `KubSTU{...}`, которые находит `strings`, — это
  **ложные флаги**. Настоящий флаг только в расшифрованном контейнере.

## Чему учит задание

1. **Самоописывающиеся форматы** (DataFlash) и восстановление их из
   фрагментированного неразмеченного пространства FAT32 с переносом заголовков.
2. **Кросс-проверка подсистем БПЛА:** GPS против EKF (`XKF1`), ветровой
   треугольник (`ARSP` + `ATT` против бортовой оценки ветра `XKF2`). Подделка
   одной подсистемы выдаёт себя нестыковкой с другой.
3. **Специфика самолётного типа:** ветровой треугольник даёт улику, которой у
   мультикоптера нет, и требует внешних метеоданных.
4. **Анти-форензика на уровне файловой системы:** времена файлов рассказывают,
   *когда* правили логи.
5. **Реконструкция геометрии по датчикам:** истинная траектория и центр
   барражирования не читаются из лога напрямую — их нужно вычислить.

Учебный контекст: MITRE ATT&CK for ICS — T0856 (Spoof Reporting Message),
T0872 (Indicator Removal on Host).
