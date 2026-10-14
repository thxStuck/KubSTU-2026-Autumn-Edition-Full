# [Beginner] Matryoshka — Community Writeup

> **Команда-автор:** mpei_larpers
> **Источник:** https://ctftime.org/writeup/41134 (CTFtime, пользовательский райтап)
> **Событие:** KubSTU CTF 2026: Autumn
> _Это командный (пользовательский) райтап, скачан с CTFtime._

---

# [Beginner] Matryoshka  
В придачу один файл - matryoshka.zip, а внутри десять ZIP'ов, вложенных друг в  
друга. В каждом уровне лежит README (русский и английский) и следующий  
levelNN.zip под паролем. README объясняет, как из данных открытого уровня  
получить пароль к следующему: где-то это комментарий архива в хитрой кодировке,  
где-то note.txt, где-то candidates.txt. Первый архив вообще без пароля, дальше  
все уровни на ZipCrypto.

Цепочка целиком выглядит так:

1. matryoshka.zip: комментарий `5ox5iae8pv05` - пароль к level02.  
2. `emhhZzEwdWN0NHc2ag==` - base64, даёт `zhag10uct4w6j`.  
3. `795f3274787a376a38766569796c73` - hex, даёт `y_2txz7j8veiyls`.  
4. `fl8insn09afrrlg` - ROT13, получается `sy8vafa09nseeyt`.  
5. Комментария нет; в note.txt вторая строка - пароль `zjcp1s35m_q5`.  
6. `cza2gkmpru` задом наперёд - `urpmkg2azc`.  
7. `120 57 115 104 56 111 117 103 105 55 50 48 107` - десятичные коды символов,  
   получается `x9sh8ougi720k`.  
8. В candidates.txt шесть строк, подходит третья: `nhd7rpralyg`.  
9. `GBUHGMDLGZ4TQMJQ` - base32, даёт `0hs0k6y810`.  
10. В level10.zip лежит flag.txt с флагом.

Вручную проходить это неинтересно, поэтому написал скрипт: он берёт  
комментарий текущего архива, считает все поддерживаемые преобразования (plain,  
base64, hex, ROT13, reverse, десятичные коды, base32 и reverse от каждого  
варианта), подмешивает строки из note.txt и candidates.txt и пробует кандидатов  
по очереди, пока вложенный архив не откроется. Пароли в коде нигде не зашиты —  
скрипт с нуля проходит все десять уровней:

$ python3 [solve.py](http://solve.py) matryoshka.zip out  
    ...  
    FLAG: kubstu{t3n_l4y3rs_d33p_991939c0}

Флаг: `kubstu{t3n_l4y3rs_d33p_991939c0}`

