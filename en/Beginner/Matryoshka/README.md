# Matryoshka

> **Category:** Beginner / PPC · **Event:** KubSTU CTF 2026 Autumn
> Author team: mpei_larpers · Source: https://ctftime.org/writeup/41134 (CTFtime community writeup)

## 📌 Task

You get a single file — matryoshka.zip, and inside it ten ZIPs nested one within another. Each level holds a README (Russian and English) and the next `levelNN.zip` under a password. The README explains how to derive the next password from the data of the open level: in one place it is the archive comment in a tricky encoding, elsewhere a note.txt, elsewhere a candidates.txt. The first archive has no password at all; after that every level uses ZipCrypto.

## 🏁 Solution

The full chain looks like this:

1. matryoshka.zip: comment `5ox5iae8pv05` — password to level02.
2. `emhhZzEwdWN0NHc2ag==` — base64, gives `zhag10uct4w6j`.
3. `795f3274787a376a38766569796c73` — hex, gives `y_2txz7j8veiyls`.
4. `fl8insn09afrrlg` — ROT13, gives `sy8vafa09nseeyt`.
5. No comment; in note.txt the second line is the password `zjcp1s35m_q5`.
6. `cza2gkmpru` reversed — `urpmkg2azc`.
7. `120 57 115 104 56 111 117 103 105 55 50 48 107` — decimal character codes, gives `x9sh8ougi720k`.
8. In candidates.txt there are six lines; the third one fits: `nhd7rpralyg`.
9. `GBUHGMDLGZ4TQMJQ` — base32, gives `0hs0k6y810`.
10. In level10.zip lies flag.txt with the flag.

Going through this by hand is no fun, so I wrote a script: it takes the current archive's comment, computes all supported transforms (plain, base64, hex, ROT13, reverse, decimal codes, base32, and reverse of every variant), mixes in the lines from note.txt and candidates.txt, and tries the candidates one by one until the nested archive opens. No passwords are hard-coded anywhere in the code — the script walks all ten levels from scratch:

```
$ python3 solve.py matryoshka.zip out
    ...
    FLAG: kubstu{t3n_l4y3rs_d33p_991939c0}
```

**Flag:** `kubstu{t3n_l4y3rs_d33p_991939c0}`
