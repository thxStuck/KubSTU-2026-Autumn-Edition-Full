# AES Is Secure, Right

> **Категория:** Crypto · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задание

Стажёр обернул AES-128 в самодельный шифр (`intern_cipher.py`) и оставил его вывод в `output.txt`: шифртекст `ct` плюс подсказку, раскрывающую первую цифру PIN. Ключ AES выводится из 4-значного PIN. Восстановите флаг.

**Файлы:** [generate.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/generate.py), [solve.py](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/solve.py), [SECRETS.txt](../../../assets/Crypto/AES%20Is%20Secure%2C%20Right/SECRETS.txt)

## 🏁 Решение

### Суть
Примитив честный — AES-128. Слабость во всём, что вокруг: ключ выводится из **4-значного PIN** (`sha256(pin)[:16]`), а подсказка в `output.txt` ещё и сообщает первую цифру. Пространство ключей схлопывается до 1000 вариантов — AES ломать не нужно, его просто перебирают по PIN.

### Разбор
`intern_cipher.py` перед шифрованием делает две нестандартные вещи:

1. **Своё дополнение** `prepare()`: добивает данные до кратности 16, но байтом-заполнителем служит **число блоков**, а не длина паддинга (не PKCS#7). Значит `Crypto.Util.Padding.unpad()` не подходит — обратную операцию пишем сами.
2. **Перестановка блоков**: циклический сдвиг на `shift = sum(цифр PIN) % число_блоков`, затем разворот списка.

Шифрование: `plaintext → prepare → блоки → сдвиг → reverse → AES-ECB`.

Решение — обратить всё для каждого PIN из `2000..2999`:

```
ciphertext → AES-ECB decrypt → reverse → обратный сдвиг → склеить → unpad
```

Шифруется не голый флаг, а короткая справка об отзыве сертификата (флаг внутри, последней строкой) — 9 блоков. На 9 блоках `shift` реально пробегает разные значения, так что перестановку надо честно обратить, а не угадать один из двух исходов (что было бы при 2 блоках).

### Решение

```python
from hashlib import sha256
from Crypto.Cipher import AES

def unprepare(d, bs=16):
    tb = len(d)//bs; pb = tb & 0xff; pl = 0
    for b in reversed(d):
        if b != pb: break
        pl += 1
    return None if (pl == 0 or pl > bs) else d[:-pl]

def decrypt(ct, pin):
    c = AES.new(sha256(pin.encode()).digest()[:16], AES.MODE_ECB)
    bl = [c.decrypt(ct[i:i+16]) for i in range(0, len(ct), 16)]
    bl.reverse()
    sh = sum(int(x) for x in pin) % len(bl)
    if sh: bl = bl[-sh:] + bl[:-sh]
    return unprepare(b"".join(bl))

# первая цифра PIN известна из подсказки -> 1000 кандидатов
for rest in range(1000):
    pin = f"2{rest:03d}"
    pt = decrypt(ct, pin)
    if pt and b"KubSTU{" in pt:
        print(pt.decode()); break
```

**Флаг:** `KubSTU{c3rt1f1c4t3_r3v0k3d}`
