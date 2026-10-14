# RISC-V.

> **类别：** Reverse · **赛事：** KubSTU CTF 2026 Autumn
> **战队（作者）：** mpei_larpers · **来源：** https://ctftime.org/writeup/41128 （CTFtime，用户提交的解题报告）
> _这是一篇战队（用户提交）的解题报告，从 CTFtime 下载。_

## 📌 题目

fw.bin —— 16608 字节的 RV32 固件，面向 QEMU virt 风格的机器：UART 位于 0x10000000，SiFive finisher 位于 0x100000，payload 加载到 0x80100000。

## 🏁 解答

前 0xDC 字节是直接位于 flash 中的引导加载器：它用 FNV-1a 的一个变体对自身代码做哈希（h = rol32((h ^ word) * 0x01000193, 13)，基值 0x811c9dc5，零被替换为 0xdeadbeef），用这个哈希给 xorshift32 播种，并将接下来的 0x4000 字节 XOR 解密到 RAM，然后跳转过去。

解密后的 payload 是「TR4P-G4T3」固件：它通过 UART 索要一个 16 字符的密钥，并用一个 Feistel 风格的变换来校验——对两个 8 字节半区进行八个回合，一切都围绕一张 RC4 表和由固定密钥 tr4p_d1sp4tch_v1 生成的 64 字节密钥流展开。该变换是双射的，所以有效密码可以通过对固件中硬编码的目标缓冲区求逆来恢复：RV32-TR4P-G4T3S!。成功时固件会自己打印 flag：以最终的 16 字节状态为密钥做 RC4，取 39 字节 PRGA，再与来自 rodata 的 39 字节掩码做 XOR。

另有一处花招——一套建立在非法指令之上的自制调用机制（opcode 0x7f）：0x00X0007F 把返回地址压入栈并通过 0x801008bc 处的派发表跳转，而 0x0000107F 则交还控制权。那条关于「陷阱即真正的 control flow」的 flag 正是说的这个。

求解过程中：

- 第 1 阶段用 Python 复现：对 [0x00, 0xDC) 做哈希、xorshift32、对区间 [0xE0, 0x40E0) 做 XOR → pay.bin。从解密后的 payload 里得到字符串 TR4P-G4T3 bootstrap ok、key>、granted:、denied 以及 RC4 密钥。

- 把 init/check/compare 函数放进 Unicorn（[emu_crypto.py](http://emu_crypto.py)）当作预言机来跑——取出 S-box 和 64 字节密钥流，用于离线模型。

- 对 check 求逆：每个回合都可逆（B_r = A_{r+1}，A_r = B_{r+1} ^ acc），从 0x801008ac 处的目标缓冲区得到唯一的密码 RV32-TR4P-G4T3S!。正向校验逐字节产出目标 8feda32565e6ca9a79578cd1e7b0e0fc 和最终状态 9d1084ba84b1d2bfb93c5d75c2b889bd。

- flag（0x80100460 处的 granted 分支）用与固件相同的逻辑离线拼出：从最终状态做 RC4-KSA，取 39 字节 PRGA，再与 0x80100884 处的掩码做 XOR。

- 端到端验证：[e2e_emu.py](http://e2e_emu.py) 把未修改的 fw.bin 加载进 Unicorn（带陷阱模拟和 UART），自己敲入密码，并从固件得到：

```
TR4P-G4T3 bootstrap ok
      key> RV32-TR4P-G4T3S!
      granted: KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}
```

外加向 SiFive finisher 写入 0x5555 —— 成功的标志。[crosscheck.py](http://crosscheck.py) 将模拟器输出的字符串与离线解进行比对：MATCH。

**Flag：** `KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}`
