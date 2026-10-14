# InfoSec hangout

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn
> **难度：** 中等

## 📌 题目

今年夏天，我们团队再次参加了一个知名的俄罗斯信息安全活动。此行照片很多，但并非所有地点都记得清。帮忙辨认这张照片里的场所，并以 `KubSTU{Name}` 的格式写出 flag。

![task.jpg](../../../assets/OSINT/InfoSec%20hangout/task.jpg)

**文件：** [task.jpg](../../../assets/OSINT/InfoSec%20hangout/task.jpg)

## 🏁 解答

1. 照片里看到一本护照和一张机票。可以推断这是机场。

2. 照片角落里还能看到拍摄的日期和时间。按这个日期，俄罗斯只有一个大型活动——OFFZONE。由此判断照片是在 Offzone 第二天拍的，所以这是莫斯科的机场。

3. 然后东看西看飞往 Krasnodar 的航班时刻表，发现 Vnukovo 有延误；那里并非一目了然，所以也可以靠暴力枚举。

4. 剩下的就是翻看 Vnukovo 里所有店铺的照片，找到这样的地板和红色椅子。

![场所内景](https://avatars.mds.yandex.net/get-altay/13604236/2a00000194ace6bcc4a8452a21012304cdc4/L_height)

**Flag：** `KubSTU{Шоколадница}`
