# BRO, SORRY

> **Category:** Hardware / Stego · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

The noise at the factory has died down, but something is still working on its own frequencies. Find the hidden flag.

Flag format: `KubSTU{...}`.

**Files:** [bro_stego_with_hint.png](../../../assets/STEGO/BRO,%20SORRY/bro_stego_with_hint.png)

## 🏁 Solution

The challenge file should first be checked with standard steganography tools. In particular, it is useful to look at the PNG metadata:

```bash
exiftool bro_stego_with_hint.png
```

The metadata contains a hint:

```text
stego_hint: key-bro
comment: Look into 8x8 frequency blocks
```

From the hint it follows that the key is `bro`, and the data must be searched for in the frequency representation of the image split into 8×8 blocks.

### DCT steganography

For each block of the image, the **discrete cosine transform** (DCT) is computed. It converts the pixel luminance values into a set of frequency coefficients.

The challenge uses the image's luminance channel. One hidden bit is determined by comparing two mid-frequency coefficients. If the first coefficient of the pair is greater than or equal to the second, a `1` is read; otherwise a `0` is read.

The coefficient pairs used:

| Pair | First coefficient | Second coefficient |
|---:|---:|---:|
| 1 | `(2, 3)` | `(3, 2)` |
| 2 | `(1, 4)` | `(4, 1)` |
| 3 | `(2, 4)` | `(4, 2)` |
| 4 | `(3, 3)` | `(4, 3)` |

Indices are zero-based. The choice of block and pair is made in a pseudo-random order built from the key `bro`.

### Data recovery

The resulting bits are combined into bytes. A correct stream starts with the signature:

```text
KSTU-DCT1
```

After the signature come the message length, the flag itself, and a CRC32 checksum. The CRC is needed to verify the correctness of the key and the integrity of the data.

For automatic extraction you can use the attached script:

```bash
python3 stego_dct.py decode bro_stego_with_hint.png --key bro
```

Result:

```text
KubSTU{dct_clouds_hide_more_than_weather}
```

**Flag:** `KubSTU{dct_clouds_hide_more_than_weather}`
