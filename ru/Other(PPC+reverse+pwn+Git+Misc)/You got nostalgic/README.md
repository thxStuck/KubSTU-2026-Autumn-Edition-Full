# You got nostalgic

> **Категория:** Misc / Stego · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задание

> What a wonderful place, but how did I get here?
> Какое замечательное место, но как я сюда попал?

![The image](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/the-image.png)

## 🏁 Решение

### Первичный анализ

Дано изображение в формате PNG. Проверим его стандартными инструментами на стеганографию и метаданные. Я использую [Aperi'Solve](https://github.com/Zeecka/AperiSolve) и [ExifTool](https://exiftool.org/):

![AperiSolve](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/aperisolve.png)

Фильтры, LSB и альфа-каналы ничего полезного не дают, значит стоит присмотреться к метаданным и читаемым строкам. Большая часть метаданных выглядит обычно (даты, GPS-координаты КубГТУ и белого дома), но среди них есть странные поля с бессмысленным на вид содержимым, похожим на части одной строки. Каждый фрагмент начинается с цифры — это его порядковый номер:

```
1 FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G
2 (SKe^*=*0EMpMdpGijJd81A
3 @HkdoY?I9D=6ii,'#f
4 ]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

Отбрасываем номера и склеиваем фрагменты по порядку:

```
FeT-g/Y7xIi\X;b!2>v^e_c(?/hwp,M?G(SKe^*=*0EMpMdpGijJd81A@HkdoY?I9D=6ii,'#f]w,UGf2ak/VbZ1@^qxB]9VJ72+I
```

### Декодирование строки

Строка похожа на результат какой-то кодировки. Перебираем варианты в CyberChef: ROT13, Base32, Base64 и т.д. На Base92 получаем осмысленный текст — ссылку на Google Drive:

![CyberChef](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cyberchef.png)

```
https://drive.google.com/file/d/1s2sqWhknYnbWEhgggjvBzkrP90OU4x-j/view?usp=sharing
```

### Инстанс Minecraft

По ссылке лежит архив `CL0S3.zip`. Скачиваем, распаковываем и видим структуру папки инстанса Minecraft — `mods`, `coremods`, `resourcepacks`, `saves` и т.д.:

![CL0S3 folder](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/cl0s3-folder.png)

Версия игры нам неизвестна, поэтому снова возвращаемся к метаданным картинки — в поле `Comment` находим `version 1.12.2`:

![Hidden version](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/hidden-version.png)

Запускаем версию 1.12.2 в любом лаунчере, указав распакованную папку как игровую директорию (если в `mods` лежат моды, понадобится Forge для 1.12.2). В меню одиночной игры видим несколько сохранений:

![Saves](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/saves.png)

Мир `here?` (папка `4lm0st_th3r3`) — единственный с отличающимся именем и превью. Заходим в него:

![Uncompleted flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/uncompleted-flag.png)

Нас встречают сетка рамок 10×5, в двух из которых уже вставлены карты, и книга с текстом:

![Book](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/book.png)

```
hello whoever got to
this point.
I hope you enjoy this
challenge.
Finish this grid if you
want a flag.
```

### Заполнение сетки

Чтобы понять, чем заполнять сетку, забираем содержимое одной из заполненных рамок — это карта. Видно, что на ней фрагмент исходного изображения, то есть картинка из условия разрезана на карты.

Выясним, как в Minecraft вообще попадают пользовательские изображения на карты:

![Google search](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/google-search.png)

Отсюда получаем две подсказки:

1. Данные карт хранятся в `.minecraft/saves/<Имя_мира>/data` в файлах `map_<номер>.dat`. В нашем случае это `saves/4lm0st_th3r3/data`.
2. Любую карту можно выдать себе по номеру командой:

```
/give @p filled_map 1 <номер_карты>
```

Такой синтаксис работает именно в 1.12.2 (номер карты передаётся как data value). Начиная с 1.13 команда выглядит иначе: `/give @p filled_map{map:<номер>}` — ещё одна причина, почему важно было найти правильную версию.

В папке `data` лежит 65 карт (`map_0.dat` … `map_64.dat`), а рамок в сетке 50. Значит часть карт — отвлекающие. Например, среди них находится логотип КубГТУ:

![KubSTU logo](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/kubstu-logo.png)

Дальше задача сводится к двум вариантам.

**Вариант 1 (задуманный автором).** Выдаём себе карты по одной и расставляем по рамкам. Изображение собирается из карт с номерами 0–49.

**Вариант 2 (без ручной расстановки).** Каждый `map_N.dat` — это сжатый gzip NBT-файл, в котором в поле `data.colors` лежит массив из 128×128 байт — индексы цветов палитры карт Minecraft. Можно прочитать файлы скриптом (например, Python + `nbtlib`), перевести индексы в RGB по палитре версии 1.12 и склеить карты в одно изображение вне игры.

## Флаг

После правильной расстановки карт 0–49 по рамкам на картинке проявляется флаг:

![Flag](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/You%20got%20nostalgic/flag.png)

**Флаг:** `KubSTU{n0st4lg14_1s_h3r3}`
