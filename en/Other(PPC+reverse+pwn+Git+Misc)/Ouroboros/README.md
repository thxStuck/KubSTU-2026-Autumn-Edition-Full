# Ouroboros

> **Category:** Reverse · **Event:** KubSTU CTF 2026 Autumn
> **Team (author):** mpei_larpers · **Source:** https://ctftime.org/writeup/41127 (CTFtime, user-submitted writeup)
> _This is a team (user-submitted) writeup, downloaded from CTFtime._

## 📌 Task

chronos is a universal (fat) Mach-O binary for macOS, x86_64 + arm64, stripped. It masquerades as "chronosd 2.4.1" — a licensed daemon that validates a 16-character activation key and, after that, decrypts and prints a payload. The description says the developer left a bunch of easter eggs — and indeed the binary is stuffed with decoy flag-like strings, while the real payload is only produced in the binary's own success branch at runtime.

## 🏁 Solution

The trick (and the name): the final payload is decrypted with a ChaCha-style stream cipher whose key material contains the SHA-256 of the binary's own __text section plus constants from the __d5 section. The file literally uses its own body as the key — Ouroboros. Hence the flag about being "keyed by its own text section".

Two things stand in the way:

1. A 16-character key, checked by a tiny stack VM baked (LCG-XOR) into a custom __DATA.__d3 section.
2. Anti-analysis: ptrace(PT_DENY_ATTACH), a P_TRACED check via sysctl(KERN_PROC_PID), getenv("DYLD_INSERT_LIBRARIES"), a timing check and VM detection (kern.hv_vmm_present, hw.model against VMware/VirtualBox/Parallels, hw.logicalcpu). The import table actually contains only dyld_get_image_header, dyld_get_image_vmaddr_slide, dlsym and getpid; the rest of libc is resolved via dlsym at startup.

Since everything is resolved dynamically, the cleanest approach is not to patch the binary but to run it in Unicorn: map the image, stub the four imports and seven dlsym functions, run the __init_offsets initializer, then main with the recovered key. The emulator goes through the real success branch and prints the payload.

Along the way:

- Strings live in __d7 in the format {u16 len, u8 key, bytes} and are decoded as out[i] = (id*0x5b) ^ key ^ data[i] ^ 0x9e, key += 0x1f. Out of there come the banner, sysctl names, the names of macOS firewalls (Little Snitch, LuLu...) and easter eggs. In __TEXT.__cstring there is a base64 string that decodes into the decoy KubSTU{m4ch0_s3ct10ns_t3ll_st0r13s}.

- __d3 (301 bytes) is decoded by an LCG stream: s = 0x1337beef; s = s*0x41c64e6d + 0x3039; code[i] = (s>>16) ^ d3[i]. The result is a stack VM: a program of 16 identical rounds y = ((rol8(x ^ acc, r) + A) ^ B), acc starts at 0x5a, and the target output is the last 16 bytes of the same section. The rounds are affine, so inversion yields the unique key: KUBSTU-CHR0N0S26.

- Running main in Unicorn prints:

```
[+] activation accepted
      [+] payload: KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}
```

Pitfall: Unicorn's default x86 CPU has no SSE4.1, and on the pmovzxbd/ptest instructions from the built-in checks the emulator crashes with UC_ERR_INSN_INVALID — the engine has to be built with cpu=UC_CPU_X86_SKYLAKE_CLIENT.

- Checks: the SHA-256 of the 39-byte payload matches a constant embedded in the binary right before the integrity check, i.e. it was indeed the real success branch that fired. Plus the same [solve.py](http://solve.py) on the arm64 slice (different __text and __d5, hence a different key) prints the same payload — the two architectures converge on the same text, ruling out a decoy.

The discovered decoys (the base64 string and two easter-egg strings) are documented in FLAG_CANDIDATE.txt.

**Flag:** `KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}`
