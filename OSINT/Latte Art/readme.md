# Latte art

Забежал в кофейню у баскетбольной арены, и за соседним столиком - мужик с ноутом, по всем повадкам скаут из НБА. Экран забит какими-то пред-драфтовыми заметками. Кажется, скоро в лиге станет на одного россиянина больше. Проходя мимо, я сфоткал его экран на телефон - но кадр вышел совсем мыльный, читать невозможно. Прогнал через OCR, вышло криво. Разберёшься, о ком речь? Нужны фамилия и имя, номер пика и команда за которую он проведёт летнюю лигу НБА.
![scout_note.txt]()

Пример флага - `KubSTU{Леброн_Джеймс:01:Cleveland_Cavaliers}`

---
## Шаг 1. Инвентаризация сигналов

Выписываем всё, что можно превратить в поисковый запрос:

| Цитата из артефакта                                                   | Что даёт                                       |
| --------------------------------------------------------------------- | ---------------------------------------------- |
| «hear his name off that stage», «rights», «2nd-rd»                    | **Драфт НБА**, второй раунд                    |
| «Federation-wise… only the **eleventh** of his kind»                  | 11-й представитель страны в истории драфта     |
| «rights are already promised south, **to Texas**. Same night»         | Права ушли в техасский клуб сразу после драфта |
| «registered club paperwork reads **Krasnodar**»                       | Клубная принадлежность                         |
| «million-plus city **on the Don**», «different river, different town» | Родной город ≠ клубный (дистрактор)            |
| «Verify against **Summer** numbers… in **Vegas**»                     | Летняя лига НБА, Лас-Вегас                     |
| «G», «6'8"», «jumbo lead guard»                                       | Позиция и рост для верификации                 |

Ключевой стержень - связка **eleventh + Federation + Krasnodar**. Из неё строится первый запрос.

---
## Шаг 2. Идентификация игрока

### Запрос 1

```
11-й россиянин в истории НБА выбранный на драфте
```

**Источник:** Чемпионат, «Всеволод Ищенко — 11-й россиянин в истории НБА, выбранный на драфте» - https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html

Прямое попадание: в материале приведён полный список задрафтованных россиян, где <cite index="9-1">под 56-м пиком 2026 года значится Всеволод Ищенко, и отмечено, что изначально этот пик принадлежал «Лос-Анджелес Лейкерс», после чего клуб обменял его в «Даллас Маверикс»</cite>.

### Запрос 2 (альтернативный маршрут, если первый не сработал)

```
Локомотив-Кубань игрок драфт НБА 2026
```

**Источник:** sports.ru - https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html

<cite index="2-1">Всеволод Ищенко (198 см, 21 год), игрок краснодарского «Локомотива», выбран под 56-м номером на драфте-2026; он воспитанник краснодарского клуба и находится в системе «Локомотива-Кубань» с 15 лет</cite>.

### Верификация гипотезы

Сверяем признаки из заметки с найденным профилем:

| Признак в заметке | Факт                                        | ✓   |
| ----------------- | ------------------------------------------- | --- |
| «G» (защитник)    | атакующий защитник                          | ✓   |
| «6'8"» (~203 см)  | 198 см — близко, скаутские оценки округляют | ~   |
| «2nd-rd»          | второй раунд                                | ✓   |
| «Krasnodar»       | «Локомотив-Кубань»                          | ✓   |
| «Texas»           | «Даллас Маверикс»                           | ✓   |
| eleventh          | 11-й россиянин                              | ✓   |

**Компонент флага получен:** `Всеволод_Ищенко`

---
## Шаг 3. Номер пика - и подвох в источниках

### Запрос 3

```
Всеволод Ищенко драфт НБА 2026 какой номер пика
```

Номер пика - **56** - подтверждается всеми источниками единогласно. Но вот **кто именно его выбрал**, СМИ описывают по-разному, и это стоит понимать:

| Источник                                                                                                                                                                         | Формулировка                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| sports.ru 🔗 [ссылка](https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html)                                                  | «выбран **«Лейкерс»** под 56-м номером»                                                                                                                                                                      |
| Спортбокс 🔗 [ссылка](https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas) | <cite index="7-1">«**Чикаго** выбрал Ищенко под 56-м номером… согласно предварительной договорённости, игрок должен был отправиться в «Лос-Анджелес Лейкерс»»</cite>                                         |
| Ведомости 🔗 [ссылка](https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina)                                              | <cite index="3-1">«Клуб «Даллас Маверикс» выбрал Ищенко под 56-м номером… изначально 56-м должен был выбирать «Чикаго Буллз», но этот актив клуб обменял в «Лос-Анджелес Лейкерс», а те — в «Даллас»»</cite> |

**Реальная цепочка прав:** Чикаго → Лейкерс → Даллас, всё в ночь драфта. Именно поэтому в артефакте написано «the club that actually calls him up won't keep him five minutes» и «don't let the on-stage cap fool you» - заметка описывает ровно эту путаницу.

**Компонент флага получен:** `56`

---
## Шаг 4. Команда в Летней лиге

Артефакт прямо указывает направление: «Verify against Summer numbers… If the passing shows up in Vegas».

### Запрос 4

```
Ищенко Летняя лига НБА 2026 статистика
```

**Источник:** Чемпионат, отчёт о заключительном матче - https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html

<cite index="19-1">Заключительный, пятый матч «Далласа» в Летней лиге прошёл против «Нью-Йорка» и завершился победой 110:88; статистика Ищенко — 15 очков, три подбора, семь передач, один перехват и один блок-шот за 27 минут, что стало его личным рекордом по очкам и передачам в турнире</cite>. <cite index="19-1">Средняя статистика за турнир: 9,5 очка, 4,4 подбора, 3,0 передачи, 1,2 перехвата и 0,8 блок-шота за 27,5 минуты</cite>.

### Полная картина по матчам (для верификации)

|Матч|Результат|Ищенко|Источник|
|---|---|---|---|
|vs «Голден Стэйт» (дебют)|поражение|7 очков|[Чемпионат](https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html)|
|vs «Лейкерс»|поражение|8 очков|[metaratings](https://metaratings.ru/news/dallas-obygral-oklakhomu-v-matche-letnei-ligi-nba-ishenko-nabral-12-ochkov-634938/)|
|vs «Мемфис»|96:88 победа|6 очков, 5 подб., 4 пер., 3 блока, 32 мин|[Чемпионат](https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html)|
|vs «Оклахома»|97:87 победа|12 очков, 7 подб., 3 пер., 2 перехв., 29 мин|[Спорт-Экспресс](https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/)|
|vs «Нью-Йорк»|110:88 победа|**15 очков, 7 передач**, 27 мин|[Чемпионат](https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html)|

Во всех пяти матчах Ищенко выступал за **«Даллас Маверикс»**.

**Компонент флага получен:** `Dallas_Mavericks`

---
## Сборка флага

```
KubSTU{Всеволод_Ищенко:56:Dallas_Mavericks}
```

| Компонент  | Значение         | Откуда                 |
| ---------- | ---------------- | ---------------------- |
| Фамилия    | Ищенко           | список 11 россиян      |
| Имя        | Всеволод         | там же                 |
| Номер пика | 56               | отчёты о драфте-2026   |
| Команда ЛЛ | Dallas Mavericks | бокс-скоры Летней лиги |

---
## Полный список источников

1. **Чемпионат** — 11-й россиянин в истории драфта (полный список) https://www.championat.com/basketball/news-6520016-vsevolod-ischenko-11-j-rossiyanin-v-istorii-nba-vybrannyj-na-drafte.html
2. **sports.ru** — выбор под 56-м номером, обмен в «Даллас» https://www.sports.ru/basketball/1117266487-vsevolod-ishhenko-vybran-pod-56-m-nomerom-na-drafte-nba.html
3. **Ведомости.Спорт** — разбор цепочки Чикаго → Лейкерс → Даллас https://www.vedomosti.ru/sport/basketball/articles/2026/06/25/1208922-na-drafte-nba-2026-vibrali-rossiyanina
4. **Спортбокс** — «Чикаго выбрал… и обменял в «Даллас»» https://news.sportbox.ru/Vidy_sporta/Basketbol/NBA/spbnews_NI2338572_Chikago_vybral_Ishhenko_na_drafte_NBA_pod_56m_nomerom_i_obmenal_rossijanina_v_Dallas
5. **Чемпионат** — заключительный матч ЛЛ, личные рекорды, средняя статистика https://www.championat.com/basketball/article-6549638-poslednij-match-vsevoloda-ischenko-za-dallas-v-letnej-lige-nba-lichnye-rekordy-statistika-rossiyanina-igra-s-nyu-jork-niks.html
6. **Чемпионат** — матч с «Мемфисом», опека Кэмерона Бузера https://www.championat.com/basketball/article-6543892-letnyaya-liga-nba-2026-vsevolod-ischenko-provyol-tretij-match-za-dallas-kak-rossiyanin-proyavil-sebya-v-igre-s-memfisom-statistika.html
7. **Спорт-Экспресс** — матч с «Оклахомой» 17.07.2026 https://www.sport-express.net/basketball/nba/news/oklahoma-dallas-rezultat-matcha-vsevoloda-ischenko-v-letney-lige-nba-17-iyulya-2026-2440012/
8. **Чемпионат** — дебютный матч с «Голден Стэйт» https://www.championat.com/basketball/news-6538756-dallas-proigral-golden-stejt-v-letnej-lige-nba-u-ischenko-sem-ochkov.html
9. **Коммерсантъ** — второй год подряд россиянин на драфте https://www.kommersant.ru/doc/8765152
10. **sports.ru (блог)** — сводка всех задрафтованных россиян + незадрафтованные (Мозгов, Швед, Базаревич) https://www.sports.ru/basketball/blogs/3415820.html
