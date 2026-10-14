# Subway 2

> **类别：** Hardware / Stego · **赛事：** KubSTU CTF 2026: Autumn
> 由战队 **mpei_larpers** 撰写的社区 writeup（tg：[@kunstl3r](https://t.me/kunstl3r)） · 来源：https://ctftime.org/writeup/41129 (CTFtime，社区 writeup)

## 📌 题目

给了我们一个包含 24 个 Subway Surfers 游戏录像 mp4 的压缩包。找出隐藏的 flag。

## 🏁 解答

要得到 flag，需要记录每个视频中一局跑酷最终收集了多少枚金币。每个视频中的金币数就是 flag 中一个字符的十进制 ASCII 码，按视频顺序排列。

```
75 85 66 83 84 85 123 49 116 53 95 114 51 97 49 95 115 117 98 119 119 51 105 125
```

将每个数字转换成对应的 ASCII 字符即可得到 flag。

**Flag：** `KUBSTU{1t5_r3a1_subww3i}`
