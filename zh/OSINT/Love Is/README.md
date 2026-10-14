# Love Is

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

Love is 就是：在大学旁边那个小摊（larёk）上，卷饼师傅满怀心意地把肉从扦子上取下来，馅料从不吝啬。然后，你接过来……它散发着烟熏的香气，入口即化。天哪，这感觉太棒了。
找出我们总去买卷饼（shawarma）的那个小摊。在 flag 里写出小摊门面上的电话号码。
Flag 格式 — `KubSTU{+79xxxxxxxxx}`

## 🏁 解答

### 第 1 步 — 确定搜索范围

题目描述本身并没有把搜索范围缩小多少，不过我们可以看看大学有哪些教学楼。
https://kubstu.ru/s-28 — 所有教学楼的清单。

![acad_buildings_list.png](../../../assets/OSINT/Love%20Is/acad_buildings_list.png)

A、B、V、G 楼一起坐落在公园范围内，所以我们把它们当作一栋楼看待。K 楼和 S 楼与上述几栋分开独立——单独考虑。
首先确定每栋楼的用途（那里能遇到哪些专业）。为此我们查阅列出它们的页面、地图以及[课程表](https://elkaf.kubstu.ru/timetable/default/time-table-student)。

![colledge.png](../../../assets/OSINT/Love%20Is/colledge.png)

![stroifak.png](../../../assets/OSINT/Love%20Is/stroifak.png)

![neftigaz.png](../../../assets/OSINT/Love%20Is/neftigaz.png)

由以上来源得出结论：V 楼（学院）、B 楼（建筑系）和 S 楼（石油天然气）与信息安全学生无关。我们会出现在 A 楼（主楼）、G 楼（因为有阶梯教室）和 K 楼（系所在的楼）。

---
### 第 2 步 — 查探教学楼周边

据此，我们应该检查相关教学楼半径 200–300 米内所有的卷饼小摊（为什么偏偏是这个距离？因为它最合适。在 30 分钟的课间，我们能够不紧不慢地走到那里、点单、等餐，最后享用这道东方美食）。

先从 K 楼开始查：

![k_shawarma_1.png](../../../assets/OSINT/Love%20Is/k_shawarma_1.png)

![k_shawarma_2.png](../../../assets/OSINT/Love%20Is/k_shawarma_2.png)

这里只有 2 个候选，而且都来自同一家连锁。

![not_larek.webp](../../../assets/OSINT/Love%20Is/not_larek.webp)

![not_larek2.webp](../../../assets/OSINT/Love%20Is/not_larek2.webp)

它们不太像小摊，所以可以忽略。

现在转到 Moskovskaya St，这里我们已经有 6 个候选：

![m_shwarma_1.png](../../../assets/OSINT/Love%20Is/m_shwarma_1.png)

![m_shwarma_2.png](../../../assets/OSINT/Love%20Is/m_shwarma_2.png)

![m_shwarma_3.png](../../../assets/OSINT/Love%20Is/m_shwarma_3.png)

![m_shwarma_4.png](../../../assets/OSINT/Love%20Is/m_shwarma_4.png)

![m_shwarma_5.png](../../../assets/OSINT/Love%20Is/m_shwarma_5.png)

![m_shwarma_6.png](../../../assets/OSINT/Love%20Is/m_shwarma_6.png)

![m_shwarma_7.png](../../../assets/OSINT/Love%20Is/m_shwarma_7.png)

这里点位更多了，逐一来查。

---
### 第 3 步 — 收尾

上一步我们得到了相当多的点位，不过搜索圈已经收得尽可能小了。

逐个检查。

![lavashok.webp](../../../assets/OSINT/Love%20Is/lavashok.webp)

这个点排除——不像小摊，而且就算是，门面上也没有电话号码。

![kabul.webp](../../../assets/OSINT/Love%20Is/kabul.webp)

也排除——这其实是一家茶馆（chaikhana）。

![loveis.webp](../../../assets/OSINT/Love%20Is/loveis.webp)

这里就有点意思了。有烟囱，意味着里面大概有烤炉（mangal），门面上有电话号码，而且小摊的名字和题目名称惊人地相似。先把这个点放一放，把其余的查完。

![dolina.webp](../../../assets/OSINT/Love%20Is/dolina.webp)

这虽然是个小摊，但这里既没有烤炉也没有号码——排除。

![chilli.webp](../../../assets/OSINT/Love%20Is/chilli.webp)

和上一个点一样——排除。

![prozharka.webp](../../../assets/OSINT/Love%20Is/prozharka.webp)

这根本不是小摊——排除。

![uni.webp](../../../assets/OSINT/Love%20Is/uni.webp)

这里是一家咖啡馆，所以不碰它。

从上述所有点位可以得出结论：符合描述的只有一个——Love Is。回到它那里，取下门面上的电话——+79182524547。

好耶，flag 找到了——`KubSTU{+79182524547}`

**Flag：** `KubSTU{+79182524547}`
