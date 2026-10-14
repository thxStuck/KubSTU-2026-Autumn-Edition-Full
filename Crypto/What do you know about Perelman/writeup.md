
## Что дано

- `cascade.py` — код «дискретного потока Риччи» на moduli-пространстве
  эллиптических кривых над `F_p`. Фиксирует `p = 4003`, `N = 30`, `η = 1`.
- `curve.png` — 4003×4003 scatter plot точек финальной кривой `E_N`,
  испорченный шумом, двумя **кривыми-обманками** и белыми «дырами».
- `encrypted.txt` — `iv`, `ct` шифрованного AES-CBC флага **и явно
  указанная схема получения ключа** (scrypt с параметрами).

## Наблюдения

Docstring в `cascade.py` навешивает математическую терминологию про Ricci
flow / Perelman / surgery — это **бутафория**. По коду `ricci_step` — просто
пара полиномиальных обновлений по модулю `p`, связанных общей «кривизной»
`K = 4a³ + 27b²` (дискриминант). Единственный секрет, годный в ключ, —
`(a₀, b₀)`; каскад `(a₀,b₀) → (a_N,b_N)` детерминирован.

## Шаг 1 — извлечь точки из PNG

Каждая точка `E_N: y² = x³ + a·x + b` над `F_p` — затемнённый 3×3 маркер.
Центр маркера = пиксель со всеми 8 тёмными соседями (эрозия 3×3).

```python
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
img = np.array(Image.open("curve.png"))
centers = binary_erosion(img < 128, structure=np.ones((3, 3)))
ys, xs = np.where(centers)
points = list(zip(xs.tolist(), ys.tolist()))
```

## Шаг 2 — восстановить `(a_N, b_N)` по точкам (RANSAC)

Из двух точек однозначно решается `(a, b)`:

```
a = ((y₁² - y₂²) - (x₁³ - x₂³)) · (x₁ - x₂)⁻¹  (mod p)
b = y₁² - x₁³ - a·x₁                              (mod p)
```

Пробуем много случайных пар, берём кривую с максимумом инлайнеров. **Кривые-
обманки** нарисованы разрежённо (~35 % точек), поэтому у настоящей `E_N`
инлайнеров заметно больше (в эталоне 3562 против ~1400 у обманок) и RANSAC
уверенно выбирает её. Шум (~2500 точек) и 55 «дыр» снижают долю инлайнеров,
так что пар нужно больше (несколько тысяч проб).

## Шаг 3 — forward-search прообразов

Каскад не сепарабельный (обновление `a` зависит от `b` и наоборот), поэтому
нельзя решать по координатам отдельно — надо перебирать пары. Всех пар
`p² = 16 032 009`, по `N = 30` итераций; в numpy это ~30 сек:

```python
a = np.arange(p, dtype=np.int64)[:, None].repeat(p, axis=1)
b = np.arange(p, dtype=np.int64)[None, :].repeat(p, axis=0)
for _ in range(N):
    Kv = (4 * ((a*a) % p) * a + 27 * ((b*b) % p)) % p
    a, b = (a - 12*((a*a) % p)*Kv) % p, (b - 54*b*Kv) % p
cand = list(zip(*np.where((a == aN) & (b == bN))))   # ~10-30 прообразов
```

## Шаг 4 — расшифровать (медленный KDF)

Ключ получается **медленным memory-hard KDF**, схема опубликована в
`encrypted.txt`:

```
key = scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
             salt=b'perelman/ricci/v2', n=65536, r=8, p=1, dklen=32)
```

scrypt применяется **только к горстке прообразов** (в эталоне 20 штук) —
~0.2 с каждый, итого секунды:

```python
for a0, b0 in cand:
    key = hashlib.scrypt(a0.to_bytes(4,'big') + b0.to_bytes(4,'big'),
                         salt=SALT, n=65536, r=8, p=1, maxmem=256*1024*1024, dklen=32)
    try:
        pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
        if pt.startswith(b"KubSTU{"): print(pt.decode()); break
    except ValueError: pass
```



