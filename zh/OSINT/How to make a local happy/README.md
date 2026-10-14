# How to make a local happy

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

要让一个 Krasnodar 本地人开心，所需甚少——只要封闭一条街就行。以前每个周末都这么做，如今只在特殊场合才封。找出这条街，以及它最后一次被封的日期。

Flag 格式：`KubSTU{StreetName_dd.mm-dd.mm}`
示例：`KubSTU{Severnaya_31.12-07.01}`

## 🏁 解答

### 第 1 步：找出这条街

“封街让人们开心”意味着把它变成步行街。我们搜索：

```
пешеходная улица Краснодар
```

![promenade_st.png](../../../assets/OSINT/How%20to%20make%20a%20local%20happy/promenade_st.png)

最前面的结果就指向 **Krasnaya St**——城市的中央大街。多年来，它从 Pushkinskaya Square 到 Dlinnaya 的一段在周末被封闭，市民非常喜欢。

2020 年因疫情暂停了这一做法，2022 年反恐委员会彻底禁止了封街。此后 Krasnaya 只在个别活动时才封闭。题目里所说的“只在特殊场合”正是指此。

> Chapaeva St（“Krasnodar 的 Arbat”）在周末也是步行街，但它至今仍每周封闭。所以它不符合题意。

### 第 2 步：寻找最后一次封街

```
улица Красная перекрыта
```

![marathon.png](../../../assets/OSINT/How%20to%20make%20a%20local%20happy/marathon.png)

最新新闻（BFM Kuban、93.ru）：为庆祝城市日（City Day），Krasnaya 上举办了一场跑步活动，从 Postovaya 到 Kalinina 的一段**自 9 月 26 日 22:00 起至 9 月 27 日 14:00** 封闭交通。

### 第 3 步：拼出 flag

```
KubSTU{Krasnaya_26.09-27.09}
```

西里尔字母版本同样接受：`KubSTU{Красная_26.09-27.09}`。

**Flag：** `KubSTU{Krasnaya_26.09-27.09}` · `KubSTU{Красная_26.09-27.09}`
