# Bday party

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn
> 作者团队：mpei_larpers · tg：[@kunstl3r](https://t.me/kunstl3r) · 来源：https://ctftime.org/writeup/41124（CTFtime 社区 writeup）

## 📌 题目

题目给我们一张照片。根据其元数据，照片拍摄于白天、太阳位于天顶之时。题目描述提到群山近在咫尺。

## 🏁 解答

从地形可以明确判断这是郊区（由于出题者来自 Krasnodar，即该市周边地区）。又因为描述说群山近在咫尺，于是我们列出以下候选居民点：Smolenskaya、Krepostnaya、Grigoryevskaya、Stavropolskaya 和 Kaluzhskaya 等哥萨克村（станица）。

Krepostnaya、Stavropolskaya 和 Grigoryevskaya 因地形被排除（它们位于低地）。

我们开始用卫星模式查看 Smolenskaya 和 Kaluzhskaya 两村的地图（所附照片的主要线索是：高压电线、一个游泳池、三座红瓦屋顶的房子以及旁边一座灰色屋顶的房子）。

迟早会发现位于 Yesenina street 的「Sanatoriy dlya dushi」（“心灵疗养院”）。

**Flag：** `KubSTU{44.7822, 38.7781}`
