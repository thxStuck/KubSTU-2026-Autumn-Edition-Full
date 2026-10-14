# Subway 2

> **Category:** Hardware / Stego · **Event:** KubSTU CTF 2026: Autumn
> Community writeup by team **mpei_larpers** (tg: [@kunstl3r](https://t.me/kunstl3r)) · Source: https://ctftime.org/writeup/41129 (CTFtime, community writeup)

## 📌 Task

We are given an archive of 24 mp4 videos of Subway Surfers gameplay. Find the hidden flag.

## 🏁 Solution

To get the flag you have to record how many coins are ultimately collected per run in each video. The number of coins in each video is the decimal ASCII code of one flag character, taken in the order of the videos.

```
75 85 66 83 84 85 123 49 116 53 95 114 51 97 49 95 115 117 98 119 119 51 105 125
```

Converting each number to its ASCII character gives the flag.

**Flag:** `KUBSTU{1t5_r3a1_subww3i}`
