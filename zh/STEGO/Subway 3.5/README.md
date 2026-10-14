# Subway 3.5

> **类别：** Hardware / Stego · **赛事：** KubSTU CTF 2026 Autumn · **#306**
> 来源：https://ctf.kubstu-ctf.ru (game 3, challenge #306)

## 📌 题目

ZeroDay。不会有提示。不会有窍门。如果到 CTF 结束时有 0 份解答——那也没关系。不会有 writeup。

https://disk.yandex.ru/d/GwEbd1y8cl5nXw

**文件：** [game.mp4](../../../assets/STEGO/Subway%203.5/game.mp4)

## 🏁 解答

> **状态：** 解题方法 ✅

### 描述

Subway 系列的续作。视频中出现**两种颜色的车厢——黄色和红色**。

### 思路

- **黄色车厢是分隔符**（字符之间的界限）。
- **红色车厢被计数**：两个黄色分隔符之间一段内的红色车厢数量就是一个字符的 **ASCII 码**。
- 把各段的所有字符按顺序拼接起来，就得到 flag。

```
... R R R R Y R R ... R R ... Y R R R ...
    └── 4 ──┘       └─ ? ─┘    └── 3 ──┘
     chr(4)          chr(?)      chr(3)
```

也就是说，按顺序读取车厢流：黄色 =「字符结束 / 边界」，边界之间红色的数量 = 该字符的值。

### 分步解法

1. 解压压缩包，按文件名对视频排序。
2. 遍历视频，写出车厢及其颜色的序列（R——红色，Y——黄色）。计数时切分成帧很方便：
   ```bash
   ffmpeg -i "video.mp4" -vf fps=5 frames/%04d.png
   ```
3. 按黄色分隔符切分红色序列，数出每一段「红色」区段的长度。
4. 把每个长度转换成一个字符（`chr`），拼接出 flag。

### 解码脚本

```python
# seq — последовательность вагонов по порядку: 'R' (красный) и 'Y' (жёлтый-разделитель)
seq = "RRRR" "Y" "RR" "Y"  # ... и так далее

segments = seq.split("Y")              # делим по жёлтым разделителям
counts = [len(s) for s in segments if s != ""]  # число красных в каждом сегменте
flag = "".join(chr(n) for n in counts)
print(counts)
print(flag)
```

如果直接用数字来数更方便（每组有多少个红色）：

```python
red_counts = [75, 85, 66, 83, 84, 85, 123]  # пример: даёт 'KubSTU{'
print("".join(chr(n) for n in red_counts))
```

检验：前几组应当得到 `KubSTU{` → `75 85 66 83 84 85 123`。

### Flag

```
KubSTU{...}
```
> 确切的值取决于压缩包里的视频。把数出的 `red_counts` 代入脚本即可。

### 注意事项

- 与 Subway 2/3 的关键区别：这里有**两种颜色**——黄色不计入数值，只用来划分字符边界。
- 注意不要让空的区段（连续两个黄色）进入计数，除非按规则它们编码 `chr(0)`。
