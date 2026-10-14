# Latte Art

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

我溜进篮球馆旁的一家咖啡馆，邻桌坐着一个拿笔记本的家伙，从各种做派看都是个 NBA 球探。屏幕上塞满了某种选秀前的笔记。看样子联盟里很快又要多一个俄罗斯人了。路过时我用手机拍下了他的屏幕——可照片拍得一片模糊，根本看不清。我用 OCR 跑了一遍，结果歪歪扭扭。你能搞清楚说的是谁吗？需要：姓和名、选秀顺位号，以及他将代表哪支球队打 NBA 夏季联赛。

**文件：** [scout_note.txt](../../../assets/OSINT/Latte%20Art/scout_note.txt)

Flag 示例 — `KubSTU{Леброн_Джеймс:01:Cleveland_Cavaliers}`

## 🏁 解答

### 第 1 步：清点线索

把所有能变成搜索词的东西都记下来：

| 来自笔记的引文 | 能得到什么 |
| --- | --- |
| «hear his name off that stage», «rights», «2nd-rd» | **NBA 选秀**，第二轮 |
| «Federation-wise… only the **eleventh** of his kind» | 该国选秀史上第 11 位代表 |
| «rights are already promised south, **to Texas**. Same night» | 权利在选秀当晚就归了一支 Texas 球队 |
| «registered club paperwork reads **Krasnodar**» | 俱乐部归属 |
| «million-plus city **on the Don**», «different river, different town» | 家乡 ≠ 俱乐部所在城市（干扰项） |
| «Verify against **Summer** numbers… in **Vegas**» | NBA 夏季联赛，Las Vegas |
| «G», «6'8"», «jumbo lead guard» | 用于核实的位置与身高 |

关键支点是 **eleventh + Federation + Krasnodar** 这个组合。第一条查询就由它构建。

---
### 第 2 步：确认球员

#### 查询 1

```
11-й россиянин в истории НБА выбранный на драфте
```

**来源：** Championat，《Vsevolod Ishchenko——NBA 历史上第 11 位被选中的俄罗斯人》 - https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html

直接命中：文章给出了所有被选中的俄罗斯人的完整名单，其中 2026 年第 56 顺位是 Vsevolod Ishchenko，并指出这个顺位最初属于 "Los Angeles Lakers"，随后该队将其交易给了 "Dallas Mavericks"。

#### 查询 2（备用路线，若第一条无效）

```
Локомотив-Кубань игрок драфт НБА 2026
```

**来源：** sports.ru - https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html

Vsevolod Ishchenko（198 厘米，21 岁），Krasnodar "Lokomotiv" 的球员，在 2026 年选秀中第 56 顺位被选中；他是 Krasnodar 俱乐部培养的，自 15 岁起就在 "Lokomotiv-Kuban" 体系里。

#### 验证假设

把笔记里的特征与找到的资料比对：

| 笔记中的特征 | 事实 | ✓ |
| --- | --- | --- |
| «G»（后卫） | 得分后卫 | ✓ |
| «6'8"»（约 203 厘米） | 198 厘米——接近，球探估测常取整 | ~ |
| «2nd-rd» | 第二轮 | ✓ |
| «Krasnodar» | "Lokomotiv-Kuban" | ✓ |
| «Texas» | "Dallas Mavericks" | ✓ |
| eleventh | 第 11 位俄罗斯人 | ✓ |

**已得到 flag 组成部分：** `Всеволод_Ищенко`

---
### 第 3 步：顺位号——以及来源里的陷阱

#### 查询 3

```
Всеволод Ищенко драфт НБА 2026 какой номер пика
```

顺位号 **56** 得到所有来源一致确认。但**究竟是谁选的他**，媒体说法各异，这点值得弄清：

| 来源 | 措辞 |
| --- | --- |
| sports.ru 🔗 [链接](https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html) | “被 **«Lakers»** 以第 56 顺位选中” |
| Sportbox 🔗 [链接](https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas) | “**Chicago** 以第 56 顺位选中 Ishchenko……按事先约定，该球员应前往 "Los Angeles Lakers"” |
| Vedomosti 🔗 [链接](https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina) | “"Dallas Mavericks" 以第 56 顺位选中 Ishchenko……原本第 56 顺位应由 "Chicago Bulls" 选，但该队把这一资产交易给了 "Los Angeles Lakers"，后者又交易给 "Dallas"” |

**真实的权利链条：** Chicago → Lakers → Dallas，全都在选秀当晚完成。这正是为什么笔记里写着 «the club that actually calls him up won't keep him five minutes» 和 «don't let the on-stage cap fool you»——笔记描述的正是这种混乱。

**已得到 flag 组成部分：** `56`

---
### 第 4 步：夏季联赛的球队

笔记直接指明方向：«Verify against Summer numbers… If the passing shows up in Vegas»。

#### 查询 4

```
Ищенко Летняя лига НБА 2026 статистика
```

**来源：** Championat，最后一场比赛的报道 - https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html

"Dallas" 在夏季联赛的最后一场、也是第五场比赛对阵 "New York"，以 110:88 获胜；Ishchenko 的数据——27 分钟内 15 分、3 个篮板、7 次助攻、1 次抢断和 1 次封盖，这成为他本届赛事得分和助攻的个人纪录。赛事场均：27.5 分钟 9.5 分、4.4 篮板、3.0 助攻、1.2 抢断和 0.8 封盖。

#### 逐场完整概览（用于核实）

| 比赛 | 结果 | Ishchenko | 来源 |
| --- | --- | --- | --- |
| vs "Golden State"（首秀） | 负 | 7 分 | [Championat](https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html) |
| vs "Lakers" | 负 | 8 分 | [metaratings](https://metaratings.ru/news/dallas-obygral-oklakhomu-v-matche-letnei-ligi-nba-ishenko-nabral-12-ochkov-634938/) |
| vs "Memphis" | 96:88 胜 | 6 分、5 板、4 助、3 帽、32 分钟 | [Championat](https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html) |
| vs "Oklahoma" | 97:87 胜 | 12 分、7 板、3 助、2 断、29 分钟 | [Sport-Express](https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/) |
| vs "New York" | 110:88 胜 | **15 分、7 助攻**、27 分钟 | [Championat](https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html) |

五场比赛中 Ishchenko 都代表 **"Dallas Mavericks"** 出战。

**已得到 flag 组成部分：** `Dallas_Mavericks`

---
### 拼出 flag

```
KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}
```

| 组成部分 | 取值 | 出处 |
| --- | --- | --- |
| 姓 | Ищенко | 11 名俄罗斯人名单 |
| 名 | Всеволод | 同上 |
| 顺位号 | 56 | 2026 选秀报道 |
| 夏季联赛球队 | Dallas Mavericks | 夏季联赛技术统计 |

---
### 完整来源列表

1. **Championat** — 选秀史上第 11 位俄罗斯人（完整名单） https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html
2. **sports.ru** — 第 56 顺位被选中，交易至 "Dallas" https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html
3. **Vedomosti.Sport** — Chicago → Lakers → Dallas 链条解析 https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina
4. **Sportbox** — “Chicago 选中……并交易至 "Dallas"” https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas
5. **Championat** — 夏季联赛最后一场、个人纪录、场均数据 https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html
6. **Championat** — 对阵 "Memphis"，对位 Cameron Boozer https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html
7. **Sport-Express** — 对阵 "Oklahoma" 17.07.2026 https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/
8. **Championat** — 对阵 "Golden State" 的首秀 https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html
9. **Kommersant** — 连续第二年有俄罗斯人进入选秀 https://www.kommersant.ru/doc/8765152
10. **sports.ru（博客）** — 所有被选中俄罗斯人的汇总 + 未被选中者（Mozgov、Shved、Bazarevich） https://www.sports.ru/basketball/blogs/3415820.html

**Flag：** `KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}`
