# Subway 3

> **Category:** Hardware / Stego · **Event:** KubSTU CTF 2026 Autumn · **#271**
> Task author: [@MrKaban4ik](https://t.me/alekseeee) · Source: https://ctf.kubstu-ctf.ru (game 3, challenge #271)

## 📌 Task

The good old subway surf. What could be better.
https://disk.360.yandex.ru/client/aa/d_DKlTBmt6U9gIlg/

## 🏁 Solution

> **Status:** Solution method ✅

### Description

An archive with recordings of Subway Surfers runs is given (as in [Subway 2](../Subway%202/)). There is no explicit text — the information is encoded by what happens on the screen.

### Idea

In each video you need to **count the number of wagons (trains)** the character drives past / over. The resulting number is the **decimal ASCII code** of one flag character.

Adding up the characters from the videos **in order** gives the flag.

```
видео_1 -> N1 вагонов -> chr(N1)
видео_2 -> N2 вагонов -> chr(N2)
...
флаг = chr(N1) + chr(N2) + ... 
```

### Step by step

1. Unpack the archive, sort the videos by name (the order matters — it sets the order of the characters).
2. For each video, count the number of wagons per run. It is convenient to split the video into frames and count manually or semi-automatically:
   ```bash
   # по одному видео: нарезать кадры (например, 5 кадров в секунду) для удобного подсчёта
   ffmpeg -i "video_01.mp4" -vf fps=5 frames_01/%04d.png
   ```
3. Convert each number to a character via the ASCII table and assemble the string.

### Decoder script

Once the wagon counts per video are known (in file order), the flag is assembled like this:

```python
# counts — список: количество вагонов в каждом видео, по порядку
counts = [
    # 75, 85, 66, 83, 84, 85, 123, ...   # пример: K U B S T U {
]

flag = "".join(chr(n) for n in counts)
print(flag)
```

Correctness is easy to check from the beginning: the first numbers must produce `KubSTU{` — that is `75 85 66 83 84 85 123`. If the beginning does not match, the counting or the file order is off somewhere.

### Flag

```
KubSTU{...}
```
> The exact value depends on the videos from the archive (we don't have them at hand right now).
> It is assembled automatically by the script above once `counts` is filled in.

### Notes

- This is the same mechanic as in Subway 2 (there, coins were counted), but here **wagons** are counted.
- The main source of errors is a broken file order and missed / doubled wagons; check against the `KubSTU{` prefix.
