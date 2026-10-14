# Color Illusion

> **类别：** Hardware / Stego · **赛事：** KubSTU CTF 2026 Autumn · **#263**
> 题目作者：[@van_1pi](https://t.me/van_1pi)

## 📌 题目

一位艺术家声称这幅画里藏着一条信息。
“并非所有颜色都如它们看上去那样，”他神秘地说。

**文件：** [stego-easy.zip](../../../assets/STEGO/Color%20Illusion/stego-easy.zip)

## 🏁 解答

解压压缩包并打开 `colors.gif`。提示（“并非所有颜色都如它们看上去那样”）指向的是**颜色值**，而不是可见的图像。检查图像的颜色平面 / 调色板——例如使用 **Aperisolve**、**Stegsolve**（位平面浏览器）或导出调色板——flag 就由异常的颜色条目拼出。

**Flag：** `KubSTU{Pr0bAbly_ea8y_steG0}`
