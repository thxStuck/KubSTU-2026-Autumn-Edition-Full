

## Суть
`params.txt`: `n = 64`, список `w` из 64 весов (~84 бита), и `ciphertexts` —
7 чисел. Схема (которую надо восстановить из данных): сообщение дополняется,
бьётся на 64-битные блоки (MSB first), каждый блок шифруется одним и тем же
публичным ключом `w` как

    c = Σ w[i] · bit[i]   (i = 0..63)

Это **low-density subset-sum (рюкзак)**. Плотность `d = n / log2(max w) ≈
64/84 ≈ 0.76`.

## Почему одного LLL мало
Теоретическая граница CJLOSS — `d < 0.9408` — асимптотическая и предполагает
идеальный SVP-оракул. На практике **чистый LLL** уверенно решает рюкзак лишь
примерно до `d ≈ 0.64` (граница Lagarias–Odlyzko). При `d ≈ 0.76` LLL
находит лишь «мусорные» короткие векторы, настоящий `(±1)`-вектор не
всплывает. Нужна более сильная редукция — **BKZ**.

## Решение
Для каждого блока строим CJLOSS-решётку `(n+1)×(n+1)`:

```
rows i<n:  [ 2·e_i ,  K·w_i ]
row  n  :  [ 1 … 1 ,  K·s   ]
```

(`K` — большой множитель, загоняющий сумму-координату в ноль). Короткий
вектор `(±1, …, ±1, 0)` = `2·bit_i − 1` → биты блока.

```python
from fpylll import IntegerMatrix, LLL, BKZ
K = 1 << 64
def rec(s):
    B = IntegerMatrix(n+1, n+1)
    for i in range(n): B[i,i]=2; B[i,n]=w[i]*K
    for j in range(n): B[n,j]=1
    B[n,n]=s*K
    LLL.reduction(B)
    BKZ.reduction(B, BKZ.Param(block_size=30))   # LLL alone НЕ хватает
    for r in range(n+1):
        row=[B[r,j] for j in range(n+1)]
        if row[n]==0 and all(abs(x)==1 for x in row[:n]):
            for sg in (1,-1):
                bits=[(sg*row[j]+1)//2 for j in range(n)]
                if all(b in (0,1) for b in bits) and sum(w[i]*bits[i] for i in range(n))==s:
                    return bits
```

Собираем биты 7 блоков, переводим в байты, снимаем нулевой паддинг.


