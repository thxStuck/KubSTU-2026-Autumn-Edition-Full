# It really isn't enough

> **Категория:** Crypto · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задание

`challenge.txt` даёт вам два открытых ключа RSA (A и B), зашифрованный RSA-OAEP ключ и два шифртекста AES-GCM. Три слоя, каждый требует отдельной атаки, плюс несколько ловушек. Название — прямая подсказка к слою 1: обычного Wiener'а **it really isn't enough**. Восстановите настоящий флаг.

**Файлы:** [solve.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/solve.sage), [bd_core.sage](../../../assets/Crypto/It%20really%20isn%27t%20enough/bd_core.sage), [source_reference.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/source_reference.py), [gen.py](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.py), [gen.log](../../../assets/Crypto/It%20really%20isn%27t%20enough/gen.log)

## 🏁 Решение

### Структура задачи
Три слоя, каждый требует отдельной атаки, плюс четыре ложных пути.

| Слой / ловушка | Механизм | Что происходит |
|---|---|---|
| Слой 1 (RSA A) | `d ≈ N^0.26` | Wiener не хватает → нужен Boneh-Durfee |
| Ловушка: ключ B | `d ≈ N^0.24` | Wiener ломает за секунду → `blob` = издёвка |
| Слой 2a (ct1) | AES-GCM, валидный тег | фейк-флаг `k3ep_1o0k1ng` |
| Слой 2b (ct2) | AES-GCM, тег сломан | наивный `decrypt_and_verify` падает |
| Ловушка: `d` в source | фейк-константа | хеш даёт неверный ключ |

Название — прямая подсказка к слою 1: обычного Wiener'а **it really isn't enough**.

### Слой 1 — Boneh-Durfee
У ключа A приватная экспонента `d ≈ N^0.26`:
- Wiener работает только при `d < N^0.25` → **не берёт**;
- Boneh-Durfee работает при `d < N^0.292` → **берёт**.

Ключ B — приманка с `d ≈ N^0.24`: классический Wiener ломает его мгновенно, но `blob` под ним расшифровывается в строку-издёвку. Это отсекает тех, кто рефлекторно кидается на первый знакомый паттерн (особенно LLM).

**Суть атаки.** Из `e·d ≡ 1 (mod φ)` и `φ = N + 1 − (p+q)` получаем уравнение с малыми корнями:

```
f(x, y) = 1 + x·(A + y) ≡ 0  (mod e),   A = (N+1)/2,  y ≈ -(p+q)/2
```

`|x| ~ N^delta`, `|y| ~ N^0.5`. Строим решётку из x- и y-shift полиномов (Herrmann–May), редуцируем LLL, берём резольвенту двух коротких векторов, находим корень → восстанавливаем `d`, затем факторизуем `N` из `(e, d)`.

Расшифровав `enc_key` (RSA-OAEP) и `src_ct` (AES-GCM), получаем `source.py`.

### Слой 2 — nonce reuse + сломанный тег
`source.py` показывает:
- `key = SHA256(str(d))` — от **настоящего** `d`. Рядом лежит константа `d = 0x...` с комментарием "private exponent" — это **фейк** (ловушка); использовать нужно `d`, полученный из Boneh-Durfee.
- Два GCM-шифротекста с **одним nonce**.

**ct1** — валидный тег → расшифровывается в фейк-флаг `k3ep_1o0k1ng`. Слопер сдаёт его и получает «неверно».

**ct2** — тот же nonce, но тег намеренно испорчен. `decrypt_and_verify` бросит `ValueError`. Ключевое понимание: **GCM = CTR + GMAC**. Сломана только целостность, не конфиденциальность — расшифровать можно в обход тега:

```python
real = AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(ct2[:-16])  # без verify
```

→ настоящий флаг.

```
sage: cd /path/to/folder        # тут challenge.txt, bd_core.sage, solve.sage
sage: load("solve.sage")
```

Пайплайн: Boneh-Durfee → `d` → факторизация → RSA-OAEP → AES-GCM(source) → парсинг nonce/ct → `SHA256(str(d))` → `decrypt` без verify на ct2.

Фейк-флаг (ct1): `KubSTU{7h15_15_n07_7h3_r34l_0n3_k3ep_1o0k1ng}`

**Флаг:** `KubSTU{50met1me5_7h3_m057_c0mp13x_7h1ng5_turn_0ut_70_b3_51mpl3_y0u_ju57_n33d_t0_74k3_4_cl053r_lo0k}`
