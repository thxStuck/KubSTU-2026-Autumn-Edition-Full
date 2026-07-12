Love is это когда шаурмист с заботой снимает мясо с шампура и не жалеет начинки в ларьке возле университета. А после, ты её берёшь и... она пахнет дымком и тает во рту. Господи, как же это хорошо.
Найдите ларёк с шаурмой, где мы всегда её берём. Во флаге укажите номер телефона с фасада ларька.
Формат флага - `KubSTU{+79xxxxxxxxx}`

---
## Шаг 1 - Определяем район поисков

Само описание особо не сужает район поисков, однако можно посмотреть какие корпуса есть у университета. 
https://kubstu.ru/s-28 - список всех корпусов

![acad_buildings_list.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/acad_buildings_list.png)

Корпуса А, Б, В и Г стоят вместе на территории парка, поэтому будем рассматривать их как один корпус. Корпуса К и С стоят обособлено от вышеперечисленных - их рассматриваем по отдельности.
Сначала определим предназначение каждого из корпусов (какие направления там можно встретить). Для этого обратимся к странице с их списком, картам и [расписанию занятий](https://elkaf.kubstu.ru/timetable/default/time-table-student).

![colledge.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/colledge.png)

![stroifak.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/stroifak.png)

![neftigaz.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/neftigaz.png)

Из источников выше делаем вывод, что корпуса В (колледж), Б (стройфак) и С (нефть и газ) не релевантны для студентов ИБшников. Нас можно встретить в корпусах А (основной), Г (из-за наличия лекционных аудиторий) и К (корпус, где располагается кафедра).

---
## Шаг 2 - Исследуем окрестности корпусов

Исходя из этого нам стоит проверить все ларьки с шаурмой в радиусе 200-300 метров от релевантных корпусов (Почему именно такое расстояние? Оно обусловлено тем, что является оптимальным. За 30-ти минутный перерыв мы успеваем дойти неспешным шагом, сделать заказ, дождаться его и в конце насладиться сие творением восточной кухни).

Начнём с проверки корпуса К:

![k_shawarma_1.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/k_shawarma_1.png)

![k_shawarma_2.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/k_shawarma_2.png)


Здесь у нас только 2 кандидата и оба они из одной сети

![not_larek.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/not_larek.webp)

![not_larek2.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/not_larek2.webp)

На ларьки это не сильно похоже, поэтому про них можно забыть.

Теперь перейдём на улицу Московскую, где у нас уже 6 кандидатов:

![m_shwarma_1.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_1.png)

![m_shwarma_2.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_2.png)

![m_shwarma_3.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_3.png)

![m_shwarma_4.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_4.png)

![m_shwarma_5.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_5.png)

![m_shwarma_6.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_6.png)

![m_shwarma_7.png](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/m_shwarma_7.png)


Тут уже больше точек, будем проверять

---
## Шаг 3 - Финал

Из прошлого шага у нас получилось достаточно много точек, однако круг поисков у нас сузился максимально сильно. 

Проверяем каждую по очереди.

![lavashok.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/lavashok.webp)

Эта точка идёт мимо - не похожа она на ларёк, да и если бы им являлась, то нет номера на фасаде.

![kabul.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/kabul.webp)

Тоже идёт мимо - это вообще чайхана.

![loveis.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/loveis.webp)

Ну тут уже что-то есть. Есть дымоход, значит можно предполагать, что внутри стоит мангал, есть номер на фасаде и название ларька подозрительно схоже с названием задания. Пока что отложим эту точку и проверим остальные.

![dolina.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/dolina.webp)

Это хоть и ларёк, но тут нет мангала и нет номера - мимо.

![chilli.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/chilli.webp)

Тоже самое, что и с прошлой точкой - мимо.

![prozharka.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/prozharka.webp)

Это вообще не ларёк - мимо

![uni.webp](https://github.com/thxStuck/KubSTU-2026-Autumn-Edition/blob/efb9823fbf3b75dc452e502773644594e4c0531b/OSINT/Love%20Is/Love%20Is_files/uni.webp)

Тут у нас кафе, поэтому его и не трогаем.

Из всех вышеперечисленных точек можно сделать вывод, что под описание подходить только одна - Love Is. Возвращаемся к ней и берём телефон с фасада - +79182524547.

Ура, флаг найден - `KubSTU{+79182524547}`
