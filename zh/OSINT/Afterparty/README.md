# Afterparty

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

春季 KubSTU CTF 结束后，我们出去放松，走进了一家店。这里真的很棒，我们玩 Uno 玩得很开心，顺便还为秋季 CTF 攒下了素材。

我想我们还会再去那里不止一次 :)

![cocktail.jpg](../../../assets/OSINT/Afterparty/cocktail.jpg)

找出我们消遣的那家店，并说出我那杯鸡尾酒的名字。

Flag 格式：`KubSTU{VenueName_CocktailName}`

**文件：** [cocktail.jpg](../../../assets/OSINT/Afterparty/cocktail.jpg)

## 🏁 解答

### 第 1 步：把照片拆解成线索

一开始就把所有能抓住的细节都记下来，不只是那只酒杯：
- **郁金香杯和一只定制高球杯。** 这种造型是创意鸡尾酒的典型特征，而非普通酒吧/酒馆。
- **杯子反光里的一簇火焰。** 说明后面有类似火的东西（壁炉或电视）。
- **背景里有一只水烟壶。** 特制底座上盛着液体的圆形容器，轮廓清晰可辨。这家店几乎肯定是水烟吧或带水烟的酒吧。
- **右侧有一个红色皮革物件。** 看起来像是皮面菜单（后面得到证实）。
- **灯光与背景。** 暖色低照度，木质吧台家具——典型的 lounge 风格。

城市可由上下文锁定：KubSTU + 信息安全 = **Krasnodar**。

### 第 2 步：缩小地理范围

我们搜索 "bar street in Krasnodar" / "restaurant street in Krasnodar"。稳定出现的是市中心的 **Krasnaya St** 以及与其平行的 **Rashpilevskaya** 和 **Krasnoarmeyskaya**。

![bar_rest_mile.png](../../../assets/OSINT/Afterparty/bar_rest_mile.png)

这一带有 300+ 家各式店铺——逐一排查太多，所以我们用第 1 步的线索来过滤。

### 第 3 步：严格过滤

在市中心所有店铺中，我们只保留同时满足以下条件的：
1. **水烟吧 / 带水烟的酒吧**（线索——背景里的水烟壶）。
2. **做创意鸡尾酒。**
3. **高端档次**（从酒杯和陈设判断）。

经过这样的过滤，剩下约 10–15 个候选。此时可以走两条路：
- **以图搜图**
- 在 2GIS / Yandex Maps 上**直接搜索**

### 第 4 步：确认店铺

我们把候选逐一对照点评照片相册和官方内容，寻找与原照片的细节吻合之处：

| 原照片中的线索 | 店铺相册中的佐证 |
|---|---|
| 水烟壶、底座 | 其他照片中同一款水烟 |
| 红色皮革物件 | 红色皮面菜单 |
| 木质台面 | 同款风格的吧台家具 |
| 提基 / 陶瓷器皿 | 该店其他照片中可见 |

所有吻合都指向同一处：**DeepSmoke，Krasnoarmeyskaya St, 68。**

![cocktail_writeup.png](../../../assets/OSINT/Afterparty/cocktail_writeup.png)

### 第 5 步：识别鸡尾酒

我们打开 DeepSmoke 的鸡尾酒菜单（来自 Yandex Maps 照片的菜单），寻找一款装在相似酒杯里的无酒精鸡尾酒。

吻合：**「Tanzania」**（无酒精）——日本无酒精金酒、芒果汤力、青柠汁、椰子糖浆。

![tanzania.webp](../../../assets/OSINT/Afterparty/tanzania.webp)

酒杯造型与装饰签都与原照片吻合——就是它。

**Flag：** `KubSTU{DeepSmoke_Tanzania}` · `KubSTU{DeepSmoke_Танзания}`
