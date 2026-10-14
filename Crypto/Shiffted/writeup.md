
## Что дано
`cipher.txt` с одной строкой: `RbiZAB{j43z4y_d0bsk_i3_wy0bk}`

## Идея
Это шифр Цезаря (сдвиг): каждая буква сдвинута на фиксированное число
позиций в алфавите. Цифры, скобки и подчёркивания не тронуты.

Подсказка видна сразу: флаги начинаются с `KubSTU{`, а в шифртексте
стоит `RbiZAB{`. Значит `R→K`, `b→u`, … — сдвиг одинаковый. `R`(17) →
`K`(10): сдвиг на 7 назад.

## Решение
Сдвинуть каждую букву на 7 назад. Или просто перебрать все 26 сдвигов и
взять тот, где получается `KubSTU{`:

```python
def caesar(t, s):
    r = ""
    for c in t:
        if c.isupper(): r += chr((ord(c)-65+s)%26+65)
        elif c.islower(): r += chr((ord(c)-97+s)%26+97)
        else: r += c
    return r

enc = open("cipher.txt").read().strip()
for s in range(26):
    g = caesar(enc, -s)
    if g.startswith("KubSTU{"):
        print(g); break
```

