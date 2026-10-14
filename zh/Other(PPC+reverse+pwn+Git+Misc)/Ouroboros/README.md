# Ouroboros

> **类别：** Reverse · **赛事：** KubSTU CTF 2026 Autumn
> **战队（作者）：** mpei_larpers · **来源：** https://ctftime.org/writeup/41127 （CTFtime，用户提交的解题报告）
> _这是一篇战队（用户提交）的解题报告，从 CTFtime 下载。_

## 📌 题目

chronos 是一个面向 macOS 的通用（fat）Mach-O，x86_64 + arm64，已 strip。它伪装成「chronosd 2.4.1」——一个需要授权的守护进程，会校验一个 16 字符的激活密钥，随后解密并打印 payload。题目描述里说开发者留下了一堆彩蛋——确实，这个二进制塞满了形似 flag 的诱饵字符串，而真正的 payload 只有在运行时、在二进制自身的 success 分支里才会产生。

## 🏁 解答

关键点（也是名字的由来）：最终的 payload 使用一个 ChaCha 风格的流密码解密，其密钥材料里包含二进制自身 __text 段的 SHA-256，外加 __d5 段里的常量。文件实实在在地把自己的本体当作密钥——Ouroboros（衔尾蛇）。flag 里「keyed by its own text section」正是由此而来。

路上有两道坎：

1. 一个 16 字符的密钥，由一台嵌入在自定义 __DATA.__d3 段里（经 LCG-XOR 编码）的微型栈式 VM 来校验。
2. 反分析：ptrace(PT_DENY_ATTACH)、通过 sysctl(KERN_PROC_PID) 检查 P_TRACED、getenv("DYLD_INSERT_LIBRARIES")、一处计时检查，以及虚拟机检测（kern.hv_vmm_present、拿 hw.model 比对 VMware/VirtualBox/Parallels、hw.logicalcpu）。导入表里其实只有 dyld_get_image_header、dyld_get_image_vmaddr_slide、dlsym 和 getpid，其余的 libc 都在启动时通过 dlsym 解析。

既然一切都是动态解析，最干净的做法不是给二进制打补丁，而是把它放进 Unicorn 里跑：映射镜像，为四个导入和七个 dlsym 函数打桩，执行 __init_offsets 初始化器，然后带着找到的密钥跑 main。模拟器会走完真正的 success 分支并打印出 payload。

过程中：

- 字符串以 {u16 len, u8 key, bytes} 的格式存放在 __d7 中，按如下方式解码：out[i] = (id*0x5b) ^ key ^ data[i] ^ 0x9e，key += 0x1f。由此得到横幅、sysctl 名称、macOS 防火墙的名字（Little Snitch、LuLu……）以及彩蛋。在 __TEXT.__cstring 里有一段 base64 字符串，解码后是诱饵 KubSTU{m4ch0_s3ct10ns_t3ll_st0r13s}。

- __d3（301 字节）由一个 LCG 流解码：s = 0x1337beef; s = s*0x41c64e6d + 0x3039; code[i] = (s>>16) ^ d3[i]。结果是一台栈式 VM：一段由 16 个相同回合组成的程序 y = ((rol8(x ^ acc, r) + A) ^ B)，acc 从 0x5a 开始，目标输出是同一段的最后 16 字节。各回合都是仿射的，所以求逆会得到唯一的密钥：KUBSTU-CHR0N0S26。

- 在 Unicorn 里跑 main 会打印：

```
[+] activation accepted
      [+] payload: KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}
```

坑点：Unicorn 默认的 x86 CPU 没有 SSE4.1，遇到内置检查里的 pmovzxbd/ptest 指令时模拟器会以 UC_ERR_INSN_INVALID 崩溃——引擎必须用 cpu=UC_CPU_X86_SKYLAKE_CLIENT 来构建。

- 校验：39 字节 payload 的 SHA-256 与完整性检查之前嵌入二进制里的常量相符，也就是说确实触发了真正的 success 分支。此外，同一份 [solve.py](http://solve.py) 在 arm64 切片上（__text 和 __d5 不同，因而密钥不同）打印出相同的 payload——两种架构在同一段文本上会合，排除了诱饵的可能。

发现的诱饵（base64 字符串和两条彩蛋字符串）记录在 FLAG_CANDIDATE.txt 中。

**Flag：** `KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}`
