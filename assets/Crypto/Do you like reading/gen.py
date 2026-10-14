#!/usr/bin/env python3
"""
Do you like reading? (KubSTU CTF, Crypto, low) — v2 (anti-slop edition)

Флаг режется на NUM_PARTS частей, каждая шифруется своим Caesar-сдвигом (по байту),
и куски вставляются в огромный текстовик из lowercase-мусора.

Дополнительно раскидываются N_FAKE фейковых кластеров — визуально неотличимых от
настоящих, но специально сконструированных так, что НИ ОДИН сдвиг не даёт вывод
в диапазоне символов флага. Это ломает наивный "перебери все кластеры" — реальный
солвер обязан использовать anchor'ы (KubSTU{ и }) и фильтр по charset.

Bulk = чистый [a-z\\n]. Порядок настоящих частей в файле = порядок в флаге.
"""
import os
import random

FLAG        = b"KubSTU{r34d1n6_r3411y_d0e5_m4k3_my_br4in_w0rk_be77er_but_th1s_t45k_1sn7_0ne_0f_7h0s3_c4535}"
NUM_PARTS   = 10
N_FAKE      = 80                        # фейковых кластеров
TARGET_SIZE = 5_500_000_000             # 5.5 ГБ. Для теста поставь 50 * 1024 * 1024
CHUNK_SIZE  = 4 * 1024 * 1024
OUTPUT      = "reading.txt"
LOG         = "gen.log"

BULK_ALPHABET = set(range(0x61, 0x7B)) | {0x0A, 0x0D, 0x20}
FLAG_ALL      = set(b"KubSTU{}abcdefghijklmnopqrstuvwxyz0123456789_")

def is_safe_shift(part: bytes, shift: int) -> bool:
    for b in part:
        c = (b + shift) % 256
        if c in BULK_ALPHABET:
            return False
    return True

def make_fake_cluster(length_range=(7, 20)) -> bytes:
    """Кластер, ни один сдвиг которого не декодит в flag-charset."""
    length = random.randint(*length_range)
    non_bulk = [b for b in range(256) if b not in BULK_ALPHABET]
    while True:
        cand = bytes(random.choice(non_bulk) for _ in range(length))
        if any(all(((b - s) % 256) in FLAG_ALL for b in cand) for s in range(256)):
            continue
        return cand

# 1. Режем флаг сбалансированно
base, extra = divmod(len(FLAG), NUM_PARTS)
sizes = [base + (1 if i < extra else 0) for i in range(NUM_PARTS)]
parts, _idx = [], 0
for sz in sizes:
    parts.append(FLAG[_idx:_idx + sz]); _idx += sz

# 2. Сдвиги
shifts = []
for p in parts:
    cands = [s for s in range(1, 256) if is_safe_shift(p, s)]
    shifts.append(random.choice(cands))

# 3. Шифруем настоящие
enc_parts = [bytes((b + s) % 256 for b in p) for p, s in zip(parts, shifts)]

# 4. Позиции настоящих
segment = TARGET_SIZE // NUM_PARTS
real_positions = sorted(
    random.randint(i * segment + 1024, (i + 1) * segment - 1024)
    for i in range(NUM_PARTS)
)

# 5. Фейки
print(f"[*] Генерирую {N_FAKE} фейков...")
fakes = [make_fake_cluster() for _ in range(N_FAKE)]
fake_positions, occupied = [], list(real_positions)
for fake in fakes:
    for _ in range(1000):
        p = random.randint(1024, TARGET_SIZE - 1024 - len(fake))
        if all(abs(p - op) > 100 for op in occupied):
            fake_positions.append(p); occupied.append(p); break

# 6. Все элементы в порядке позиции
items = [(pos, blob) for pos, blob in zip(real_positions, enc_parts)]
items += [(pos, blob) for pos, blob in zip(fake_positions, fakes)]
items.sort()

# 7. Лог
with open(LOG, "w") as log:
    log.write("=== настоящие ===\n")
    for i, (p, s, e, pos) in enumerate(zip(parts, shifts, enc_parts, real_positions)):
        log.write(f"part {i}: plain={p!r} shift={s:3d} enc={e.hex()} pos={pos}\n")
    log.write(f"\n=== фейки ({len(fakes)}) ===\n")
    for i, (pos, blob) in enumerate(zip(fake_positions, fakes)):
        log.write(f"fake {i}: len={len(blob):2d} enc={blob.hex()} pos={pos}\n")

# 8. Bulk-шаблоны
def make_template():
    buf = bytearray(random.choices(range(0x61, 0x7B), k=CHUNK_SIZE))
    i = 0
    while i < len(buf):
        i += random.randint(60, 100)
        if i < len(buf): buf[i] = 0x0A
    return bytes(buf)

templates = [make_template() for _ in range(4)]

# 9. Пишем
print(f"[*] Пишу {TARGET_SIZE / 1024**2:.1f} МБ → {OUTPUT}")
cursor, item_idx = 0, 0
with open(OUTPUT, "wb") as f:
    while cursor < TARGET_SIZE:
        if item_idx < len(items) and cursor >= items[item_idx][0]:
            _, blob = items[item_idx]
            f.write(blob); cursor += len(blob); item_idx += 1
            continue
        next_stop = items[item_idx][0] if item_idx < len(items) else TARGET_SIZE
        fill = min(CHUNK_SIZE, next_stop - cursor, TARGET_SIZE - cursor)
        tpl = random.choice(templates)
        off = random.randint(0, CHUNK_SIZE - fill) if CHUNK_SIZE > fill else 0
        f.write(tpl[off:off + fill]); cursor += fill

print(f"[+] {cursor} байт, {len(real_positions)} real + {len(fake_positions)} fake")
print(f"[+] Сдвиги: {shifts}")
print(f"[+] Детали в {LOG}")
