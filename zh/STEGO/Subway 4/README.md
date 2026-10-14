# Subway 4

> **类别：** Hardware / Stego · **赛事：** KubSTU CTF 2026 Autumn · **#309**
> 来源：https://ctf.kubstu-ctf.ru (game 3, challenge #309)

## 📌 题目

又是这个地铁

https://disk.360.yandex.ru/client/aa/d_gG4FXiJyQRLKaw

## 🏁 解答

> **状态：** 解题方法 ✅

### 描述

Subway 系列的终章。与前几部不同，不需要数任何东西——**flag 就藏在视频帧里，藏在黑暗中**。在正常亮度下看不见（极暗的像素几乎与黑色背景融为一体）。

### 思路

需要**拉出阴影 / 提高亮度和对比度**，flag 文字就会在暗部显现出来。

### 分步解法

#### 方案 1 — 通过 ffmpeg（直接在视频中提高亮度/伽马/对比度）

```bash
# сильно осветляем и тянем контраст, смотрим результат
ffmpeg -i subway4.mp4 -vf "eq=brightness=0.6:contrast=4:gamma=3" subway4_bright.mp4
```

也可以通过 `curves` 拉伸色阶：

```bash
ffmpeg -i subway4.mp4 -vf "curves=all='0/0 0.1/0.9 1/1'" subway4_levels.mp4
```

#### 方案 2 — 切分成帧并处理图片

```bash
ffmpeg -i subway4.mp4 -vf fps=2 frames/%04d.png
```

然后对每一帧提亮（Python/PIL），增强亮度和对比度：

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

或者激进地「裁剪」黑色阈值，让任何并非纯黑的像素都变成白色：

```python
from PIL import Image
img = Image.open("frames/0007.png").convert("L")
# всё, что ярче 8 из 255 — делаем белым; остальное чёрным
bw = img.point(lambda x: 255 if x > 8 else 0)
bw.save("frames/0007_threshold.png")
```

#### 方案 3 — 交互式

在编辑器（GIMP/Photoshop/任意视频编辑器）中打开视频/帧，手动提高 **Levels/Curves/Exposure**——flag 会在最暗的帧中显现出来。

### 到哪里找

flag 通常不是出现在所有帧上，而是在一小段里。把提亮后的视频完整看一遍，或对所有帧跑一遍阈值处理，用眼睛寻找带有 `KubSTU{...}` 文字的那一帧。

### Flag

```
KubSTU{...}
```
> 确切的值要从显现出来（提亮后）的那一帧读取——我们目前手头没有视频。

### 注意事项

- 本题的要点不是数学，而正是对**亮度/对比度/色阶**的处理。
- 如果均匀提亮没有效果，试着拆分成 R/G/B 通道——文字可能只藏在某一个通道里。
