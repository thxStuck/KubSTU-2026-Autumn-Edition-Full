# Timing

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

We are given a sample for analysis. It must be opened and the flag recovered.

## 🏁 Solution

The sample must be opened for analysis, for example in autopsy.

The objects `draft_notes.tmp` and `unused_ledger.tmp` are small decoy entries. In the root of the file system there is a deleted `sync_7D3.tmp`; the neighboring log `Logs/TRANSFER.LOG` links this object to the last operation Batch 7D3.

Despite the `.tmp` extension, magic-number detection identifies the target file as a **PE32 executable**. In Autopsy it should be saved via the context action Extract File(s). The size of the correct file is **14 848 bytes**, and its first bytes are `4D 5A` (`MZ`). The original name may be displayed with the first character restored or with a deletion mark: this is a normal consequence of the FAT record and does not affect extraction.

In the function that builds the buffer before the `fwrite` call, there are two short byte arrays. First they are concatenated, and for each byte with index `i` the operation is performed:

```text
shuffled[i] = encoded[i] XOR ((0x51 + 0x23 × i) mod 256)
```

Then the first two 16-byte blocks are swapped, and the remainder is copied unchanged:

```text
plain[0:16]   = shuffled[16:32]
plain[16:32]  = shuffled[0:16]
plain[32:]    = shuffled[32:]
```

After these actions, we get:

```text
KubSTU{aU70p5y_D3l373d_P3_4nd_r3v3r53}
```

**Flag:** `KubSTU{aU70p5y_D3l373d_P3_4nd_r3v3r53}`
