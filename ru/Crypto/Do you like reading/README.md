# Do you like reading

> **Категория:** Crypto · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задание

`reading.txt` — огромный текстовый файл. Флаг спрятан в нём в виде байтовых кластеров, выделяющихся на фоне обычного текста `[a-z\n]` — каждый настоящий кластер является частью флага, зашифрованной своим Caesar-сдвигом, но большинство кластеров — фейки. Восстановите флаг.

**Файлы:** [gen.py](../../../assets/Crypto/Do%20you%20like%20reading/gen.py), [solve.py](../../../assets/Crypto/Do%20you%20like%20reading/solve.py), [gen.log](../../../assets/Crypto/Do%20you%20like%20reading/gen.log)

## 🏁 Решение

### Наблюдения
- Файл слишком большой для блокнота / `less`.
- `tr -d 'a-z\n' < reading.txt | xxd | less` показывает вкрапления байтов не из `[a-z\n]` — заглавные, цифры, знаки препинания, control-байты.
- Аномалий много (~90 кластеров), длина разная (от 7 до 20 байт).
- Большинство из них — **фейки**. Настоящих частей флага только 10.

### Идея
Каждый настоящий кластер — часть флага, зашифрованная своим Caesar-сдвигом по байту. Фейки сконструированы так, что **никакой** сдвиг не даёт вывод в диапазоне символов флага — это ломает наивный «перебрать все кластеры».

Порядок настоящих частей в файле = порядок в флаге.

### Решение
Три вещи, которые нужно понять:
1. Файл огромный → нужна стрим-обработка (mmap идеален).
2. Кластеров много (фейков в разы больше настоящих) → нужен anchor: первая часть начинается на `KubSTU{`, последняя оканчивается на `}`.
3. Для средних частей — фильтр по узкому charset `[a-z0-9_]`; при неоднозначности выбираем сдвиг с максимумом подчёркиваний (в реальном флаге они частые, в случайном сдвиге — редкие).

```python
import mmap, re

CORE  = set(b"abcdefghijklmnopqrstuvwxyz0123456789_")
CLOSE = CORE | {ord("}")}
HEAD, TAIL = b"KubSTU{", b"}"

def dec(blob, s): return bytes((b - s) % 256 for b in blob)

# 1. Поиск кластеров: mmap + regex по всему файлу.
#    Ядро само подгрузит нужные страницы, ничего не держим в RAM целиком.
clusters = []
with open("reading.txt", "rb") as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        for match in re.finditer(rb"[^a-z\n\r ]+", m):
            clusters.append((match.start(), match.group()))

# 2. HEAD: первый кластер, декодящийся во что-то с префиксом KubSTU{
head_i, head_dec = None, None
for i, (_, blob) in enumerate(clusters):
    for s in range(256):
        d = dec(blob, s)
        if d.startswith(HEAD):
            head_i, head_dec = i, d; break
    if head_i is not None: break

# 3. TAIL: последний кластер, декодящийся во что-то с суффиксом }
tail_i, tail_dec = None, None
for i in range(len(clusters) - 1, -1, -1):
    _, blob = clusters[i]
    for s in range(256):
        d = dec(blob, s)
        if d.endswith(TAIL) and all(c in CLOSE for c in d):
            tail_i, tail_dec = i, d; break
    if tail_i is not None: break

# 4. MIDDLE: между head и tail оставляем только кластеры с валидным
# CORE-декодом. Фейки естественно отфильтруются (нет валидного сдвига).
# Среди валидных сдвигов выбираем с максимумом подчёркиваний.
middle = []
for i in range(head_i + 1, tail_i):
    _, blob = clusters[i]
    best = None
    for s in range(1, 256):
        d = dec(blob, s)
        if all(c in CORE for c in d):
            score = d.count(b"_")
            if best is None or score > best[0]:
                best = (score, d)
    if best: middle.append(best[1])

print((head_dec + b"".join(middle) + tail_dec).decode())
```

**Флаг:** `KubSTU{r34d1n6_r3411y_d0e5_m4k3_my_br4in_w0rk_be77er_but_th1s_t45k_1sn7_0ne_0f_7h0s3_c4535}`
