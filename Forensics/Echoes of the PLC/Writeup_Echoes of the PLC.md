CRY
Задача проверяет не поиск открытой строки, а **корреляцию трёх протоколов**. В крупном перемешанном дампе MQTT публикует манифест, Modbus/TCP передаёт зашифрованные блоки, а ICMP Echo Reply содержит маски для каждого блока.

## Шаг 1. Найти манифест MQTT

Начните с фильтра:

```wireshark
tcp.port == 1883
```

Среди MQTT-обменов найдите публикацию с темой `facility/maintenance/calibration-manifest`. Удобный дополнительный фильтр:

```wireshark
tcp contains "calibration-manifest"
```

Выберите пакет этого потока и откройте **Follow → TCP Stream**. JSON-манифест описывает алгоритм:

```json
{
  "source": "Modbus/TCP unit=7 function=0x04",
  "order": "transaction_id ascending",
  "mask": "ICMP Echo Reply id=3199; sequence = transaction_id - 0x4000",
  "final": "zlib"
}
```

Эта подсказка делает цепочку решения однозначной: угадывать шифр, источник ключа или формат результата не нужно.

## Шаг 2. Отобрать Modbus-блоки

Примените фильтр:

```wireshark
tcp.port == 502 && ip.addr == 10.20.7.7
```

В ответах сервера `10.20.7.7` найдите кадры с **Unit Identifier = 7** и **Function Code = 0x04**. Их девять. У каждого ответа есть Modbus transaction ID и бинарные данные чтения. Сохраните пары вида:

```text
transaction_id -> data
```

Отсортируйте блоки по `transaction_id` по возрастанию.

## Шаг 3. Отобрать ICMP-маски

Примените фильтр:

```wireshark
icmp.type == 0 && icmp.ident == 3199
```

Это ICMP Echo Reply с целевым identifier. Для Modbus transaction ID `0x4000 + N` возьмите ICMP-пакет с sequence `N`. Его data payload имеет ту же длину, что и соответствующий Modbus-блок, и является маской XOR.

## Шаг 4. Восстановить контейнер

Для каждого Modbus-блока выполните побайтовый XOR с соответствующим ICMP payload. Склейте восстановленные блоки по transaction ID. Результат — корректный zlib-поток, который нужно распаковать.

Полный эталонный разбор находится в `validate_and_solve.py`. Ключевой фрагмент преобразования выглядит так:

```python
restored = bytearray()
for transaction_id, encrypted_block in sorted(modbus_blocks.items()):
    sequence = transaction_id - 0x4000
    mask = icmp_masks[sequence]
    restored.extend(
        byte ^ mask[index]
        for index, byte in enumerate(encrypted_block)
    )

print(zlib.decompress(bytes(restored)).decode())
```

После распаковки выводится журнал калибровки и флаг.

> Флаг: `KubSTU{modbus_echoes_keep_the_secret}`