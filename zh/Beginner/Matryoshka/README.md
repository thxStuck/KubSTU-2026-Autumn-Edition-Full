# Matryoshka

> **类别:** Beginner / PPC · **赛事:** KubSTU CTF 2026 Autumn
> 作者团队: mpei_larpers · 来源: https://ctftime.org/writeup/41134 (CTFtime 社区题解)

## 📌 题目

附带只有一个文件——matryoshka.zip，里面是十个相互嵌套的 ZIP。每一层都放着一个 README（俄文和英文）和下一个带密码的 `levelNN.zip`。README 解释了如何从当前已打开层的数据推导出下一层的密码：有的地方是以某种刁钻编码呈现的压缩包注释，有的地方是 note.txt，有的地方是 candidates.txt。第一个压缩包完全没有密码，之后每一层都用 ZipCrypto。

## 🏁 解题过程

整条链如下：

1. matryoshka.zip：注释 `5ox5iae8pv05` — level02 的密码。
2. `emhhZzEwdWN0NHc2ag==` — base64，得到 `zhag10uct4w6j`。
3. `795f3274787a376a38766569796c73` — hex，得到 `y_2txz7j8veiyls`。
4. `fl8insn09afrrlg` — ROT13，得到 `sy8vafa09nseeyt`。
5. 没有注释；note.txt 的第二行就是密码 `zjcp1s35m_q5`。
6. `cza2gkmpru` 反转 — `urpmkg2azc`。
7. `120 57 115 104 56 111 117 103 105 55 50 48 107` — 十进制字符码，得到 `x9sh8ougi720k`。
8. candidates.txt 里有六行，第三行合适：`nhd7rpralyg`。
9. `GBUHGMDLGZ4TQMJQ` — base32，得到 `0hs0k6y810`。
10. level10.zip 里放着带 flag 的 flag.txt。

手动走一遍没什么意思，于是写了个脚本：它取当前压缩包的注释，计算所有支持的变换（plain、base64、hex、ROT13、reverse、十进制码、base32，以及每种变体的 reverse），再混入 note.txt 和 candidates.txt 里的行，逐个尝试候选，直到嵌套压缩包被打开为止。代码里任何地方都没有硬编码密码——脚本从零把十层全部走通：

```
$ python3 solve.py matryoshka.zip out
    ...
    FLAG: kubstu{t3n_l4y3rs_d33p_991939c0}
```

**Flag:** `kubstu{t3n_l4y3rs_d33p_991939c0}`
