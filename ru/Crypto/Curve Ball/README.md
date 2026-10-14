# Curve Ball

> **Категория:** Crypto · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задание

Цепочка из двух жёстко связанных эллиптических кривых (плюс кривая-приманка C3) и зашифрованный AES флаг. Каждый слой — отдельная нетривиальная атака, и цепочка решается только строго последовательно. Восстановите флаг.

**Файлы:** [gen.py](../../../assets/Crypto/Curve%20Ball/gen.py), [solve.sage](../../../assets/Crypto/Curve%20Ball/solve.sage), [gen.log](../../../assets/Crypto/Curve%20Ball/gen.log), [скриншот](../../../assets/Crypto/Curve%20Ball/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-10-02%20022018.png)

## 🏁 Решение

### Обзор
Цепочка из двух эллиптических кривых, жёстко связанных. Каждый слой — отдельная нетривиальная атака. Решается полностью только последовательно.

```
C1 (general Weierstrass)
   -> привести к короткой форме
   -> посчитать #E1, обнаружить #E1 = p1  (АНОМАЛЬНАЯ)
   -> Smart's attack -> k1
k1 -> SHA256 -> ключ AES -> расшифровать параметры C2
C2 (supersingular, embedding degree 2)
   -> MOV attack (distortion map + Weil pairing)
   -> smooth DLP в GF(p2^2)* (Pohlig-Hellman) -> k2
AES(key = SHA256("k1:k2")) -> флаг
```

Приманка: C3 — обычная кривая, которую игрок может попытаться атаковать, но она не ведёт к флагу (на ней ни одна из атак не даёт полезного результата).

---

### Слой 0 — распознавание
C1 дана в **полной форме Вейерштрасса** `y² + a1·xy + a3·y = x³ + a2·x² + a4·x + a6`. Игрок приводит к короткой `y² = x³ + Ax + B` (стандартные b/c-инварианты) и считает порядок (`E.order()` в Sage).

Ключевое наблюдение: **#E1 = p1**. Это аномальная кривая, и для неё ECDLP решается за линейное время через Smart's attack. Без подсчёта порядка кривая выглядит как обычный неподъёмный 256-битный ECDLP — в этом ловушка слоя 0.

---

### Слой 1 — Smart's attack (SSSA)
Для аномальной кривой (`#E = p`) существует изоморфизм в аддитивную группу `F_p` через подъём в p-адическое поле `Q_p` и формальный логарифм.

```python
def smart_attack(G, P, p):
    E = G.curve()
    Eqp = EllipticCurve(Qp(p, 2), [ZZ(t) for t in E.a_invariants()])
    Gl = Eqp.lift_x(ZZ(G.xy()[0]))
    if (ZZ(Gl.xy()[1]) % p) != (ZZ(G.xy()[1]) % p): Gl = -Gl
    Pl = Eqp.lift_x(ZZ(P.xy()[0]))
    if (ZZ(Pl.xy()[1]) % p) != (ZZ(P.xy()[1]) % p): Pl = -Pl
    pG, pP = p*Gl, p*Pl                    # push into the formal group
    tG = -(pG.xy()[0]) / (pG.xy()[1])      # p-adic elliptic log
    tP = -(pP.xy()[0]) / (pP.xy()[1])
    return Integer((tP / tG) % p)
```

Результат — `k1`, секретный скаляр C1.

---

### Связь слоёв
Параметры C2 зашифрованы AES-CBC, ключ выводится из `k1`:

```python
key1 = SHA256(b"C1->C2:" + str(k1).encode())
plaintext = JSON {p2, a, b, G2, P2}
```

Без Smart's на C1 параметры C2 недоступны — подобрать k1 (258 бит) невозможно. Это делает цепочку строго последовательной.

---

### Слой 2 — MOV attack
После расшифровки C2 оказывается supersingular: `y² = x³ + x` над `p2 ≡ 3 (mod 4)`, `#E2 = p2 + 1`, embedding degree 2. Порядок **гладкий** (специально сконструирован), поэтому DLP после переноса решается.

MOV переносит ECDLP в `GF(p2²)*` через спаривание Вейля. Вместо случайного поиска вспомогательной точки используется **distortion map** `φ(x,y) = (−x, i·y)` (где `i² = −1`), который гарантирует невырожденное спаривание:

```python
F2e = GF(p2**2, 'i', modulus=x**2 + 1); i = F2e.gen()
E2e = EllipticCurve(F2e, [a, b])
def distort(P):
    x, y = P.xy(); return E2e(-x, i*y)
alpha = G2e.weil_pairing(distort(G2e), n)
beta  = P2e.weil_pairing(distort(G2e), n)

# beta = alpha^k2 в GF(p2^2)* ; порядок гладкий -> Pohlig-Hellman
ord_alpha = alpha.multiplicative_order()
k2_partial = discrete_log(beta, alpha, ord=ord_alpha, operation='*')

# Weil pairing может потерять часть 2-компоненты порядка, так что
# discrete_log даёт k2 только по модулю ord_alpha. Недостающий кофактор
# n/ord_alpha крошечный (делитель 2-части) — добираем полный k2
# коротким перебором (максимум ~16 итераций):
cof = n // ord_alpha
for j in range(cof):
    cand = k2_partial + j * ord_alpha
    if cand * G2 == P2:
        k2 = cand; break
```

Результат — `k2`.

**Тонкость (критична для стабильности):** Weil pairing `e(G, φ(G))` для supersingular может иметь порядок `ord_alpha < n`, теряя часть степени двойки (`p2+1` содержит `2^k`). Поэтому `discrete_log` восстанавливает `k2 mod ord_alpha`, и при неудачном `k2` полный секрет не получается напрямую. Короткий перебор кофактора добирает недостающие биты. Без этого шага солвер падает на части случайных ключей.

---

### Слой 3 — флаг

```python
key = SHA256(f"{k1}:{k2}")
flag = AES-CBC-decrypt(iv, ct, key)
```

**Флаг:** `KubSTU{45_f0r_311ip71c_curv3_g30m37ry_4nd_cryp70gr4phy_1n_g3ner41_1_63l13v3_y0u_w3re_46l3_70_501ve_i7}`
