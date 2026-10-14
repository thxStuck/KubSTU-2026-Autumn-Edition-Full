# RISC-V.

> **Category:** Reverse · **Event:** KubSTU CTF 2026 Autumn
> **Team (author):** mpei_larpers · **Source:** https://ctftime.org/writeup/41128 (CTFtime, user-submitted writeup)
> _This is a team (user-submitted) writeup, downloaded from CTFtime._

## 📌 Task

fw.bin — 16608 bytes of RV32 firmware for a QEMU virt-style machine: UART at 0x10000000, SiFive finisher at 0x100000, payload loaded at 0x80100000.

## 🏁 Solution

The first 0xDC bytes are a bootloader right in flash: it hashes its own code with a variant of FNV-1a (h = rol32((h ^ word) * 0x01000193, 13), base 0x811c9dc5, with zero replaced by 0xdeadbeef), seeds xorshift32 with that hash and XOR-decrypts the next 0x4000 bytes into RAM, then jumps there.

The decrypted payload is the "TR4P-G4T3" firmware: it asks over UART for a 16-character key and checks it with a Feistel-style transform — eight rounds over two 8-byte halves, all built around an RC4 table and 64 bytes of keystream from the fixed key tr4p_d1sp4tch_v1. The transform is bijective, so the valid password is recovered by inverting the target buffer hardcoded in the firmware: RV32-TR4P-G4T3S!. On success the firmware itself prints the flag: RC4 keyed by the final 16-byte state, 39 bytes of PRGA, XOR with a 39-byte mask from rodata.

A separate twist is a home-grown call mechanism built on top of illegal instructions (opcode 0x7f): 0x00X0007F pushes the return address onto the stack and jumps through the dispatcher table at 0x801008bc, while 0x0000107F returns control. The flag about "traps as real control flow" is exactly about this.

During the solve:

- Stage 1 was reproduced in Python: hash over [0x00, 0xDC), xorshift32, XOR of the range [0xE0, 0x40E0) → pay.bin. From the decrypted payload come the strings TR4P-G4T3 bootstrap ok, key>, granted:, denied and the RC4 key.

- The init/check/compare functions were run in Unicorn ([emu_crypto.py](http://emu_crypto.py)) as an oracle — pulling out the S-box and 64 bytes of keystream for an offline model.

- Inverting check: each round is reversible (B_r = A_{r+1}, A_r = B_{r+1} ^ acc), and from the target buffer at 0x801008ac you get the unique password RV32-TR4P-G4T3S!. The forward check produced byte-for-byte the target 8feda32565e6ca9a79578cd1e7b0e0fc and the final state 9d1084ba84b1d2bfb93c5d75c2b889bd.

- The flag (the granted branch at 0x80100460) was assembled offline with the same logic as in the firmware: RC4-KSA from the final state, 39 bytes of PRGA, XOR with the mask at 0x80100884.

- End-to-end proof: [e2e_emu.py](http://e2e_emu.py) loads the unmodified fw.bin into Unicorn (with trap emulation and UART), types in the password itself and gets back from the firmware:

```
TR4P-G4T3 bootstrap ok
      key> RV32-TR4P-G4T3S!
      granted: KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}
```

plus a write of 0x5555 to the SiFive finisher — a sign of success. [crosscheck.py](http://crosscheck.py) compares the string from the emulator against the offline solution: MATCH.

**Flag:** `KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}`
