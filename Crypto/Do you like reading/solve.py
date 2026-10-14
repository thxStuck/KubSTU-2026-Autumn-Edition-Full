#!/usr/bin/env python3
"""
Solver для Do you like reading? v2 (anti-slop edition)

1. Стримом находим все кластеры не-lowercase байтов (могут быть настоящими или фейками).
2. Head-кластер: ищем среди всех тот, у которого какой-то сдвиг даёт префикс "KubSTU{".
3. Tail-кластер: тот, у которого декод оканчивается на "}" и весь в CORE ∪ {}}.
4. Middle: между head и tail, оставляем только кластеры с валидным CORE-декодом
   (фейки построены так, что не декодятся никаким сдвигом → сами отфильтруются).
   Выбор сдвига внутри middle — по максимуму подчёркиваний.
"""
import mmap, re

FILE = "reading.txt"

CORE  = set(b"abcdefghijklmnopqrstuvwxyz0123456789_")
CLOSE = CORE | {ord("}")}
HEAD, TAIL = b"KubSTU{", b"}"

def dec(blob, s): return bytes((b - s) % 256 for b in blob)

# --- поиск кластеров через mmap + regex (быстро на файлах любого размера) ---
clusters = []
with open(FILE, "rb") as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        for match in re.finditer(rb"[^a-z\n\r ]+", m):
            clusters.append((match.start(), match.group()))

print(f"[+] всего кластеров: {len(clusters)}")

# --- head: любой кластер, декодящийся в что-то с префиксом KubSTU{ ---
head_i = head_dec = None
for i, (_, blob) in enumerate(clusters):
    for s in range(256):
        d = dec(blob, s)
        if d.startswith(HEAD):
            head_i, head_dec = i, d; break
    if head_i is not None: break

# --- tail: последний кластер, декодящийся в что-то с суффиксом } и весь в CLOSE ---
tail_i = tail_dec = None
for i in range(len(clusters) - 1, -1, -1):
    _, blob = clusters[i]
    for s in range(256):
        d = dec(blob, s)
        if d.endswith(TAIL) and all(c in CLOSE for c in d):
            tail_i, tail_dec = i, d; break
    if tail_i is not None: break

print(f"[+] head #{head_i} → {head_dec.decode()}")
print(f"[+] tail #{tail_i} → {tail_dec.decode()}")

# --- middle: между head и tail, с валидным CORE-декодом ---
middle = []
skipped = 0
for i in range(head_i + 1, tail_i):
    _, blob = clusters[i]
    best = None
    for s in range(1, 256):
        d = dec(blob, s)
        if all(c in CORE for c in d):
            score = d.count(b"_")
            if best is None or score > best[0]:
                best = (score, d)
    if best:
        middle.append(best[1])
    else:
        skipped += 1

print(f"[+] middle: {len(middle)} настоящих, {skipped} фейков отфильтровано")

flag = head_dec + b"".join(middle) + tail_dec
print(f"\n[+] FLAG: {flag.decode()}")
