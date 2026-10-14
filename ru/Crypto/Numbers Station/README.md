# Numbers Station

> **Категория:** Crypto · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задание

`codes.txt` содержит одну строку чисел, разделённых пробелами:
`75 117 98 83 84 85 123 ...`

Расшифруйте сообщение.

**Файлы:** [gen.py](../../../assets/Crypto/Numbers%20Station/gen.py), [solve.py](../../../assets/Crypto/Numbers%20Station/solve.py)

## 🏁 Решение

### Идея
Это ASCII-коды символов в десятичной системе. Каждое число — код одной буквы. Подсказка: `75` = `K`, `117` = `u`, `98` = `b` → уже видно `Kub…`.

### Решение
Перевести каждое число в символ:

```python
codes = open("codes.txt").read().split()
flag = "".join(chr(int(x)) for x in codes)
print(flag)
```

**Флаг:** `KubSTU{d3c1m4l_15_my_l4n6u4g3}`
