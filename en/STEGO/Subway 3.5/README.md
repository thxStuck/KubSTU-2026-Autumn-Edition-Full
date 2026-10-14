# Subway 3.5

> **Category:** Hardware / Stego · **Event:** KubSTU CTF 2026 Autumn · **#306**
> Source: https://ctf.kubstu-ctf.ru (game 3, challenge #306)

## 📌 Task

ZeroDay. There will be no hints. There will be no tips. If there are 0 solutions by the end of the CTF — that's fine. There will be no write-ups.

https://disk.yandex.ru/d/GwEbd1y8cl5nXw

**Files:** [game.mp4](../../../assets/STEGO/Subway%203.5/game.mp4)

## 🏁 Solution

> **Status:** Solution method ✅

### Description

A continuation of the Subway series. In the video, wagons of **two colors — yellow and red** appear.

### Idea

- **Yellow wagons are separators** (delimiters between characters).
- **Red wagons are counted**: the number of red wagons in a segment between yellow separators is the **ASCII code** of one character.
- All characters from the segments, taken in sequence, give the flag.

```
... R R R R Y R R ... R R ... Y R R R ...
    └── 4 ──┘       └─ ? ─┘    └── 3 ──┘
     chr(4)          chr(?)      chr(3)
```

That is, read the stream of wagons in order: yellow = "end of character / boundary", the number of reds between boundaries = the value of the character.

### Step by step

1. Unpack the archive, sort the videos by name.
2. Go through the videos and write out the sequence of wagons with their color (R — red, Y — yellow). For counting it is convenient to cut into frames:
   ```bash
   ffmpeg -i "video.mp4" -vf fps=5 frames/%04d.png
   ```
3. Split the sequence of reds by the yellow separators, count the length of each "red" stretch.
4. Convert each length into a character (`chr`) and assemble the flag.

### Decoder script

```python
# seq — последовательность вагонов по порядку: 'R' (красный) и 'Y' (жёлтый-разделитель)
seq = "RRRR" "Y" "RR" "Y"  # ... и так далее

segments = seq.split("Y")              # делим по жёлтым разделителям
counts = [len(s) for s in segments if s != ""]  # число красных в каждом сегменте
flag = "".join(chr(n) for n in counts)
print(counts)
print(flag)
```

If it is more convenient to count directly in numbers (how many reds in each group):

```python
red_counts = [75, 85, 66, 83, 84, 85, 123]  # пример: даёт 'KubSTU{'
print("".join(chr(n) for n in red_counts))
```

Check: the first groups must give `KubSTU{` → `75 85 66 83 84 85 123`.

### Flag

```
KubSTU{...}
```
> The exact value depends on the videos from the archive. Substitute the computed `red_counts` into the script.

### Notes

- The key difference from Subway 2/3: here there are **two colors** — yellow is not counted into the value, it only marks the character boundary.
- Make sure empty segments (two yellows in a row) do not get into the count, unless by the rules they encode `chr(0)`.
