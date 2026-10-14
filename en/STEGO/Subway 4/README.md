# Subway 4

> **Category:** Hardware / Stego · **Event:** KubSTU CTF 2026 Autumn · **#309**
> Source: https://ctf.kubstu-ctf.ru (game 3, challenge #309)

## 📌 Task

This subway again

https://disk.360.yandex.ru/client/aa/d_gG4FXiJyQRLKaw

## 🏁 Solution

> **Status:** Solution method ✅

### Description

The finale of the Subway series. Unlike the previous parts, you don't need to count anything — **the flag is hidden right in the video frames, in the dark**. At normal brightness it is not visible (the very dark pixels almost merge with the black background).

### Idea

You need to **pull out the shadows / raise the brightness and contrast**, and the flag text will appear in the dark areas.

### Step by step

#### Variant 1 — via ffmpeg (raise brightness/gamma/contrast right in the video)

```bash
# сильно осветляем и тянем контраст, смотрим результат
ffmpeg -i subway4.mp4 -vf "eq=brightness=0.6:contrast=4:gamma=3" subway4_bright.mp4
```

You can also stretch the levels via `curves`:

```bash
ffmpeg -i subway4.mp4 -vf "curves=all='0/0 0.1/0.9 1/1'" subway4_levels.mp4
```

#### Variant 2 — cut into frames and process the images

```bash
ffmpeg -i subway4.mp4 -vf fps=2 frames/%04d.png
```

Then brighten each frame (Python/PIL), boosting brightness and contrast:

```python
from PIL import Image, ImageEnhance
import glob, os

os.makedirs("bright", exist_ok=True)
for p in glob.glob("frames/*.png"):
    img = Image.open(p).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(5.0)   # поднять яркость
    img = ImageEnhance.Contrast(img).enhance(3.0)     # поднять контраст
    img.save(os.path.join("bright", os.path.basename(p)))
```

Or aggressively "clip" the black threshold so that any not-perfectly-black pixel becomes white:

```python
from PIL import Image
img = Image.open("frames/0007.png").convert("L")
# всё, что ярче 8 из 255 — делаем белым; остальное чёрным
bw = img.point(lambda x: 255 if x > 8 else 0)
bw.save("frames/0007_threshold.png")
```

#### Variant 3 — interactively

Open the video/frames in an editor (GIMP/Photoshop/any video editor) and manually raise the **Levels/Curves/Exposure** — the flag will show through in the darkest frames.

### Where to look

The flag usually appears not on all frames, but on a short stretch. Watch the brightened video all the way through or run threshold processing over all frames and look for the frame with the text `KubSTU{...}` by eye.

### Flag

```
KubSTU{...}
```
> The exact value is read off the revealed (brightened) frame — we don't have the video at hand right now.

### Notes

- The point of the task is not math, but specifically working with **brightness/contrast/levels**.
- If a uniform fill doesn't help, try splitting into R/G/B channels — the text may be hidden in only one channel.
