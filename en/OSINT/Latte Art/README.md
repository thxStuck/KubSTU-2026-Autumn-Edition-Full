# Latte Art

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

I dropped into a coffee shop by the basketball arena, and at the next table there was a guy with a laptop — by every habit an NBA scout. The screen was packed with some pre-draft notes. It seems the league is about to get one more Russian. Walking past, I snapped his screen with my phone — but the shot came out completely blurry, impossible to read. I ran it through OCR, and it came out crooked. Can you figure out who it's about? We need the surname and first name, the pick number, and the team he will play for in the NBA Summer League.

**Files:** [scout_note.txt](../../../assets/OSINT/Latte%20Art/scout_note.txt)

Flag example — `KubSTU{Леброн_Джеймс:01:Cleveland_Cavaliers}`

## 🏁 Solution

### Step 1. Inventory of signals

We write down everything that can be turned into a search query:

| Quote from the artifact | What it gives |
| --- | --- |
| «hear his name off that stage», «rights», «2nd-rd» | **NBA draft**, second round |
| «Federation-wise… only the **eleventh** of his kind» | The 11th representative of the country in draft history |
| «rights are already promised south, **to Texas**. Same night» | Rights went to a Texas club right after the draft |
| «registered club paperwork reads **Krasnodar**» | Club affiliation |
| «million-plus city **on the Don**», «different river, different town» | Home town ≠ club town (distractor) |
| «Verify against **Summer** numbers… in **Vegas**» | NBA Summer League, Las Vegas |
| «G», «6'8"», «jumbo lead guard» | Position and height for verification |

The key pivot is the combination **eleventh + Federation + Krasnodar**. The first query is built from it.

---
### Step 2. Identifying the player

#### Query 1

```
11-й россиянин в истории НБА выбранный на драфте
```

**Source:** Championat, "Vsevolod Ishchenko — the 11th Russian in NBA history to be drafted" - https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html

A direct hit: the article gives the full list of drafted Russians, where with the 56th pick of 2026 appears Vsevolod Ishchenko, and it is noted that originally this pick belonged to the "Los Angeles Lakers", after which the club traded it to the "Dallas Mavericks".

#### Query 2 (alternative route, if the first didn't work)

```
Локомотив-Кубань игрок драфт НБА 2026
```

**Source:** sports.ru - https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html

Vsevolod Ishchenko (198 cm, 21 years old), a player of Krasnodar's "Lokomotiv", was selected 56th in the 2026 draft; he is a product of the Krasnodar club and has been in the "Lokomotiv-Kuban" system since the age of 15.

#### Verifying the hypothesis

We check the signs from the note against the found profile:

| Sign in the note | Fact | ✓ |
| --- | --- | --- |
| «G» (guard) | shooting guard | ✓ |
| «6'8"» (~203 cm) | 198 cm — close, scouting estimates round up | ~ |
| «2nd-rd» | second round | ✓ |
| «Krasnodar» | "Lokomotiv-Kuban" | ✓ |
| «Texas» | "Dallas Mavericks" | ✓ |
| eleventh | 11th Russian | ✓ |

**Flag component obtained:** `Всеволод_Ищенко`

---
### Step 3. The pick number — and the catch in the sources

#### Query 3

```
Всеволод Ищенко драфт НБА 2026 какой номер пика
```

The pick number — **56** — is confirmed unanimously by all sources. But **who exactly selected him** is described differently by the media, and this is worth understanding:

| Source | Wording |
| --- | --- |
| sports.ru 🔗 [link](https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html) | "selected by the «Lakers» at number 56" |
| Sportbox 🔗 [link](https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas) | "«Chicago» selected Ishchenko at number 56… according to the prior agreement, the player was to go to the «Los Angeles Lakers»" |
| Vedomosti 🔗 [link](https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina) | "The «Dallas Mavericks» club selected Ishchenko at number 56… originally «Chicago Bulls» was to pick 56th, but the club traded this asset to the «Los Angeles Lakers», and they — to «Dallas»" |

**Real rights chain:** Chicago → Lakers → Dallas, all on draft night. That is exactly why the artifact says "the club that actually calls him up won't keep him five minutes" and "don't let the on-stage cap fool you" — the note describes precisely this confusion.

**Flag component obtained:** `56`

---
### Step 4. The team in the Summer League

The artifact points directly: «Verify against Summer numbers… If the passing shows up in Vegas».

#### Query 4

```
Ищенко Летняя лига НБА 2026 статистика
```

**Source:** Championat, report on the final match - https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html

The final, fifth match of "Dallas" in the Summer League was against "New York" and ended in a 110:88 win; Ishchenko's stats — 15 points, three rebounds, seven assists, one steal and one block in 27 minutes, which became his personal record for points and assists in the tournament. Average stats for the tournament: 9.5 points, 4.4 rebounds, 3.0 assists, 1.2 steals and 0.8 blocks in 27.5 minutes.

#### Full picture by matches (for verification)

| Match | Result | Ishchenko | Source |
| --- | --- | --- | --- |
| vs "Golden State" (debut) | loss | 7 points | [Championat](https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html) |
| vs "Lakers" | loss | 8 points | [metaratings](https://metaratings.ru/news/dallas-obygral-oklakhomu-v-matche-letnei-ligi-nba-ishenko-nabral-12-ochkov-634938/) |
| vs "Memphis" | 96:88 win | 6 points, 5 reb, 4 ast, 3 blocks, 32 min | [Championat](https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html) |
| vs "Oklahoma" | 97:87 win | 12 points, 7 reb, 3 ast, 2 steals, 29 min | [Sport-Express](https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/) |
| vs "New York" | 110:88 win | **15 points, 7 assists**, 27 min | [Championat](https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html) |

In all five matches Ishchenko played for the **"Dallas Mavericks"**.

**Flag component obtained:** `Dallas_Mavericks`

---
### Assembling the flag

```
KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}
```

| Component | Value | Where from |
| --- | --- | --- |
| Surname | Ищенко | list of 11 Russians |
| First name | Всеволод | same |
| Pick number | 56 | 2026 draft reports |
| Summer League team | Dallas Mavericks | Summer League box scores |

---
### Full list of sources

1. **Championat** — the 11th Russian in draft history (full list) https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html
2. **sports.ru** — selection at number 56, trade to "Dallas" https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html
3. **Vedomosti.Sport** — breakdown of the Chicago → Lakers → Dallas chain https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina
4. **Sportbox** — "Chicago selected… and traded to «Dallas»" https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas
5. **Championat** — final Summer League match, personal records, average stats https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html
6. **Championat** — the match against "Memphis", guarding Cameron Boozer https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html
7. **Sport-Express** — the match against "Oklahoma" 17.07.2026 https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/
8. **Championat** — the debut match against "Golden State" https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html
9. **Kommersant** — a Russian in the draft for the second year in a row https://www.kommersant.ru/doc/8765152
10. **sports.ru (blog)** — summary of all drafted Russians + the undrafted ones (Mozgov, Shved, Bazarevich) https://www.sports.ru/basketball/blogs/3415820.html

**Flag:** `KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}`
