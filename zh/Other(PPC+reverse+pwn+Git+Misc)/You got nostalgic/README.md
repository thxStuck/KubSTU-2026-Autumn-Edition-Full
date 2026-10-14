# You got nostalgic

> **类别：** Misc / Stego · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

> What a wonderful place, but how did I get here?
> 多么美妙的地方，可我是怎么来到这里的？

![The image](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/the-image.png)

## 🏁 解答

### 初步分析

我们拿到一张 PNG 图片。先用常规的隐写和元数据工具跑一遍。我使用 [Aperi'Solve](https://github.com/Zeecka/AperiSolve) 和 [ExifTool](https://exiftool.org/)：

![AperiSolve](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/aperisolve.png)

滤镜、LSB 和 alpha 通道都没有揭示任何有用的东西，所以值得更仔细地看看元数据和可读字符串。大部分元数据看起来很普通（日期、KubSTU 和白宫的 GPS 坐标），但其中有几个奇怪的字段，内容看上去毫无意义，像是同一个字符串的若干片段。每个片段都以一个数字开头——那是它的序号：

```
1 FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G
2 (SKe^*=*0EMpMdpGijJd81A
3 @HkdoY?I9D=6ii,'#f
4 ]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

去掉数字，按顺序把片段拼接起来：

```
FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G(SKe^*=*0EMpMdpGijJd81A@HkdoY?I9D=6ii,'#f]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

### 解码字符串

这个字符串看起来像某种编码的输出。我们在 CyberChef 里尝试不同选项：ROT13、Base32、Base64 等等。Base92 给出了有意义的文本——一个 Google Drive 链接：

![CyberChef](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cyberchef.png)

```
https://drive.google.com/file/d/1s2sqWhknYnbWEhgggjvBzkrP90OU4x-j/view?usp=sharing
```

### Minecraft 实例

该链接指向一个名为 `CL0S3.zip` 的压缩包。下载并解压后，我们看到一个 Minecraft 实例的文件夹结构——`mods`、`coremods`、`resourcepacks`、`saves` 等等：

![CL0S3 folder](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cl0s3-folder.png)

我们不知道游戏版本，于是再次回到图片的元数据——`Comment` 字段里写着 `version 1.12.2`：

![Hidden version](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/hidden-version.png)

在任意启动器中启动 1.12.2 版本，把解压出来的文件夹设为游戏目录（如果 `mods` 里有模组，1.12.2 需要 Forge）。在单人游戏菜单中，我们看到几个存档：

![Saves](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/saves.png)

世界 `here?`（文件夹 `4lm0st_th3r3`）是唯一一个名字和预览都不同的。进入它：

![Uncompleted flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/uncompleted-flag.png)

迎接我们的是一个 10×5 的物品展示框网格，其中两个已经放着地图，还有一本写了些文字的书：

![Book](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/book.png)

```
hello whoever got to
this point.
I hope you enjoy this
challenge.
Finish this grid if you
want a flag.
```

### 填满网格

为了弄清网格该用什么来填，我们从一个已放好的展示框里把物品取出来——是一张地图。上面显示着原始图片的一个片段，也就是说题目描述里的那张图被切成了一张张地图。

先来搞清楚 Minecraft 里自定义图片究竟是怎么出现在地图上的：

![Google search](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/google-search.png)

*（搜索关键词："how to put your own photo on Minecraft maps"。AI 概览解释说，自定义图片会被转换成地图数据文件，放进世界的 `data` 文件夹里，然后在游戏中用 `/give` 命令获取。）*

由此我们得到两个提示：

1. 地图数据存放在 `.minecraft/saves/<World_name>/data` 下，文件名为 `map_<number>.dat`。在我们这里就是 `saves/4lm0st_th3r3/data`。
2. 任何一张地图都可以用下面的命令按编号发给自己：

```
/give @p filled_map 1 <map_number>
```

这个语法正是在 1.12.2 中生效（地图编号作为 data value 传入）。从 1.13 起命令写法不同：`/give @p filled_map{map:<number>}`——这又是一个为什么找对版本很重要的理由。

`data` 文件夹里有 65 张地图（`map_0.dat` … `map_64.dat`），而网格只有 50 个框。所以有一部分地图是干扰项。例如，其中一张是 KubSTU 的 logo：

![KubSTU logo](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/kubstu-logo.png)

从这里起有两条路可走。

**方案 1（出题人设计的）。** 把地图一张张发给自己，并放进展示框。图片由编号 0–49 的地图拼成。

**方案 2（无需手动摆放）。** 每个 `map_N.dat` 都是一个 gzip 压缩的 NBT 文件，其 `data.colors` 字段里存着一个 128×128 字节的数组——指向 Minecraft 地图调色板的索引。你可以用脚本（例如 Python + `nbtlib`）读取这些文件，用 1.12 调色板把索引转成 RGB，并在游戏之外把这些地图拼成一整张图片。

## Flag

当编号 0–49 的地图正确放进展示框后，图片里就浮现出 flag：

![Flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/flag.png)

**Flag：** `KubSTU{n0st4lg14_1s_h3r3}`
