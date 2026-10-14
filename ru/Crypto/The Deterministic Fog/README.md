# The Deterministic Fog

> **Категория:** Crypto (LWE + LCG) · **Событие:** KubSTU CTF 2026 Autumn
> Подробный райтап команды mpei_larpers ([CTFtime](https://ctftime.org/writeup/41123))

## 📌 Задание

`output.json` содержит матрицы `A`, `R`, векторы `b`, `ciphertext`, параметры и калибровку. Параметры LWE: секрет из 40 элементов, 200 публичных уравнений, `q=257`, шум в диапазоне `[-100,100]`. LCG имеет 48-битное состояние. Восстановите флаг.

**Файлы:** [generate.py](../../../assets/Crypto/The%20Deterministic%20Fog/generate.py), [solution_fog.py](../../../assets/Crypto/The%20Deterministic%20Fog/solution_fog.py), [SECRETS.txt](../../../assets/Crypto/The%20Deterministic%20Fog/SECRETS.txt), [скриншот](../../../assets/Crypto/The%20Deterministic%20Fog/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-08%20234600.png)

## 🏁 Решение

### Суть
Снаружи — честный LWE (`n=40, m=200, q=257`, шумная система). На деле LWE решать не нужно: шум **детерминированный**. Его источник — публичный **усечённый LCG**

```
x_{i+1} = (mult · x_i + inc) mod 2^48      (mult, inc, mod_bits — в output.json)
```

с секретным 48-битным сидом `x_0`. Прибор публикует короткий **калибровочный след** `calibration` — старшие 8 бит первых 24 состояний (`x_i >> 40`). По этому следу сид восстанавливается **решёткой** (классическая реконструкция усечённого LCG, FHKLLS).

### Почему не берётся «в лоб»
- **Граница шума `bound = 100 > q/4 = 64`.** Шум нельзя «округлить», значит это **не** обычный small-noise LWE — generic-BDD-атака на LWE не работает, нужно воспроизвести точный поток шума.
- **Сид 48-битный** → перебор `2⁴⁸` мёртв.
- **В калибровке скрыто 40 младших бит** каждого выхода (показаны только 8 старших) → перебор младших бит `2⁴⁰` тоже мёртв. Остаётся только решётка.
- Поэтому единственный путь к флагу идёт через решётку; её не обойти.

### Разбор
**Шаг 1. Восстановить сид решёткой.** Состояние линейно по `x_0`: `x_i = α_i·x_0 + β_i (mod M)`, а `x_0 = (calib[0]·2⁴⁰) + l_0`, где `l_0` — скрытые 40 бит. Из `x_i = (calib[i]·2⁴⁰) + l_i`, `0 ≤ l_i < 2⁴⁰`, строим решётку на неизвестных `(l_0, …)` и ищем короткий вектор (LLL). 24 выборок хватает с запасом; выход проверяем, прогнав LCG вперёд и сверив старшие биты.

**Шаг 2. Воспроизвести поток шума.** Из `x_0` прогоняем LCG: калибровка берёт состояния `x_0…x_{23}`, рабочий поток шума продолжается с `x_{24}` (центрируем: `e = x mod 201 − 100`). Первые `m=200` значений ушли в `b`, следующие `len(flag)·8` — в шифртекст.

**Шаг 3. Снять LWE (теперь это линейная система).** Зная шум `e`, публичные выборки дают `A·s = b − e (mod q)` — обычная линейная система над `F₂₅₇`, решается Гауссом (`m=200 ≫ n=40`, решение единственно).

**Шаг 4. Расшифровать.** Для каждой строки шифртекста `val = (c_j − e_{m+j} − ⟨R_j, s⟩) mod q`; бит `0`, если `val` ближе к `0`, иначе `1` (кодирование `bit·⌊q/2⌋`). Собираем биты в флаг.

---

### Подробный командный райтап (mpei_larpers)

**Суть:** LWE-шум выдаёт детерминированный 48-битный LCG. Калибровка раскрывает верхние 8 бит первых 24 состояний. Восстанавливаем seed решёткой, повторяем поток шума и снимаем шум с LWE-системы.

#### 1. Исходные данные
В `output.json` находятся матрицы `A`, `R`, векторы `b`, `ciphertext`, параметры и калибровка. Параметры LWE: секрет из 40 элементов, 200 публичных уравнений, `q=257`, шум в диапазоне `[-100,100]`. LCG имеет 48-битное состояние.

Публичные уравнения:

```text
b[i] = dot(A[i], secret) + noise[i] mod q
```

Генератор шума:

```text
x[i+1] = (mult * x[i] + inc) mod 2^48
noise[i] = x[i] mod 201 - 100
```

`mult` и `inc` известны. Восстановить нужно только `x[0]`.

#### 2. Восстанавливаем начальное состояние LCG
Калибровочное значение — `y[i]=x[i]>>40`. Обозначим `B=2^40`, `M=2^48`. Тогда:

```text
x[i] = y[i] * B + z[i]
0 <= z[i] < B
```

`z[i]` — неизвестные младшие 40 бит. Раскроем рекурсию:

```text
x[i] = A[i] * x[0] + C[i] mod M
```

Коэффициенты:

```text
A[0] = 1                 C[0] = 0
A[i+1] = A[i] * mult mod M
C[i+1] = C[i] * mult + inc mod M
```

Подставив `x[0]=y[0]*B+z[0]`, получаем для каждого калибровочного значения:

```text
A[i] * z[0] + D[i] = k[i] * M + u[i]
0 <= u[i] < B
```

Остатки `u[i]` меньше `B`, поэтому представляем систему решёткой и ищем близкий вектор через LLL и Babai CVP. Проверка кандидата полным прогоном LCG даёт:

```text
seed = 194990846919092
```

##### Восстановление seed
Установите зависимости:

```bash
python3 -m pip install fpylll cysignals
```

Скрипт читает калибровку из архива, строит решётку и принимает кандидата, только если совпали все значения:

```python
import json
from zipfile import ZipFile

from fpylll import CVP, IntegerMatrix, LLL

ARCHIVE = "The Deterministic Fog.zip"
MEMBER = "The Deterministic Fog/output.json"

with ZipFile(ARCHIVE) as archive:
    data = json.loads(archive.read(MEMBER))

sampler = data["sampler"]
mult = sampler["mult"]
inc = sampler["inc"]
M = 1 << sampler["mod_bits"]
B = 1 << sampler["hide"]
ys = data["calibration"]
n = len(ys)

# Коэффициенты в x[i] = A[i]*x[0] + C[i] (mod M).
A, C = [], []
aa, cc = 1, 0
for _ in ys:
    A.append(aa)
    C.append(cc)
    aa = aa * mult % M
    cc = (cc * mult + inc) % M

# После подстановки x[0] = y[0]*B + z[0] получаем
# общую неизвестную z[0] и ограниченные остатки для каждой строки.
D = [(A[i] * ys[0] * B + C[i] - ys[i] * B) % M
     for i in range(n)]

# Базис порождает координаты A[i]*z + k[i]*M и последнюю координату z.
basis = IntegerMatrix(n + 1, n + 1)
for i in range(n):
    basis[i, i] = M
for i in range(n):
    basis[n, i] = A[i]
basis[n, n] = 1

LLL.reduction(basis)
target = [-value for value in D] + [0]
nearest = CVP.babai(basis, target)
low_part = int(nearest[-1])

def calibration(seed):
    x = seed
    trace = []
    for _ in ys:
        trace.append(x >> sampler["hide"])
        x = (mult * x + inc) % M
    return trace

seed = None
for candidate_low in (low_part, -low_part):
    if 0 <= candidate_low < B:
        candidate = ys[0] * B + candidate_low
        if calibration(candidate) == ys:
            seed = candidate
            break

if seed is None:
    raise ValueError("Кандидат решётки не совпал с калибровочной трассой")

print("Recovered seed:", seed)
```

Полная проверка трассы отсекает ложные ближайшие векторы.

#### 3. Воссоздаём поток шума
Сначала делаем 24 перехода до `x[24]`. Затем генерируем шум для 200 строк `b`, потом по одному значению для каждого бита `ciphertext`. Порядок должен совпадать с кодом задания.

```python
mask = M - 1
x = seed
for _ in range(sampler["calib"]):
    x = (mult * x + inc) & mask

count = len(data["b"]) + len(data["ciphertext"])
noise = []
for _ in range(count):
    noise.append(
        x % (2 * data["params"]["bound"] + 1)
        - data["params"]["bound"]
    )
    x = (mult * x + inc) & mask
```

Теперь весь поток шума известен.

#### 4. Находим секрет LWE по модулю 257
Вычитаем первые 200 значений шума из `b`. Остаётся система линейных уравнений:

```text
A * secret = b - noise mod 257
```

Решаем методом Гаусса над полем `F_257`. Ранг матрицы — 40, поэтому секрет определяется однозначно.

```python
q = data["params"]["q"]
rows = data["A"]
rhs = [
    (value - error) % q
    for value, error in zip(data["b"], noise)
]
n_secret = data["params"]["n"]
matrix = [
    [value % q for value in row] + [target]
    for row, target in zip(rows, rhs)
]

pivots = []
r = 0
for col in range(n_secret):
    pivot = next(
        (i for i in range(r, len(matrix)) if matrix[i][col] % q),
        None,
    )
    if pivot is None:
        continue

    matrix[r], matrix[pivot] = matrix[pivot], matrix[r]
    inverse = pow(matrix[r][col], -1, q)
    matrix[r] = [(value * inverse) % q for value in matrix[r]]

    for i in range(len(matrix)):
        if i != r and matrix[i][col]:
            factor = matrix[i][col]
            matrix[i] = [
                (a - factor * b) % q
                for a, b in zip(matrix[i], matrix[r])
            ]

    pivots.append(col)
    r += 1
    if r == n_secret:
        break

if r != n_secret:
    raise ValueError(f"Неожиданный ранг матрицы: {r}")

secret = [0] * n_secret
for row_index, col in enumerate(pivots):
    secret[col] = matrix[row_index][-1]

# Проверяем найденный секрет во всех 200 публичных уравнениях.
assert all(
    sum(a * b for a, b in zip(row, secret)) % q == value
    for row, value in zip(rows, rhs)
)
```

`assert` проверяет секрет по всем 200 уравнениям.

#### 5. Снимаем шифрование и собираем флаг
Каждое значение `ciphertext` кодирует один бит открытого текста. Для бита `m`, строки `R` и шума `e` шифрование вычисляет:

```text
c = dot(R, secret) + e + m*(q//2) mod q
```

Вычитаем из `c` известные `dot(R, secret)` и шум `e`. Остаток `0` означает бит 0, `128` — бит 1. Байты собираем от старшего бита к младшему.

```python
bit_errors = noise[len(data["b"]):]
bits = []

for value, row, error in zip(
    data["ciphertext"], data["R"], bit_errors
):
    phase = (
        value
        - sum(a * b for a, b in zip(row, secret))
        - error
    ) % q
    bits.append(1 if q // 4 < phase < 3 * q // 4 else 0)

plaintext = bytes(
    sum(bits[offset + j] << (7 - j) for j in range(8))
    for offset in range(0, len(bits), 8)
)
flag = plaintext.decode("ascii")

assert flag.startswith("KubSTU{") and flag.endswith("}")
print(flag)
```

Результат:

```text
KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}
```

#### Проверка результата
1. Seed воспроизводит все 24 значения `calibration`.
2. Секрет удовлетворяет 200 уравнениям LWE.
3. Каждый очищенный бит равен `0` или `128`.
4. Байты образуют ASCII-флаг формата `KubSTU{...}`.

**Причина уязвимости:** шум детерминирован, а калибровка частично раскрывает состояние LCG.

**Флаг:** `KubSTU{lw3_574nd5_f0r_l0v3ly_w153_c4pyb4r4}`
