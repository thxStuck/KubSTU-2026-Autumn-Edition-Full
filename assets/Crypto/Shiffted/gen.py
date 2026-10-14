#!/usr/bin/env python3
"""Caesar shift — beginner task generator."""

FLAG = "KubSTU{c43s4r_w0uld_b3_pr0ud}"
SHIFT = 7

def caesar(text, shift):
    out = []
    for ch in text:
        if 'a' <= ch <= 'z':
            out.append(chr((ord(ch) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= ch <= 'Z':
            out.append(chr((ord(ch) - ord('A') + shift) % 26 + ord('A')))
        else:
            out.append(ch)
    return ''.join(out)

if __name__ == "__main__":
    enc = caesar(FLAG, SHIFT)
    with open("cipher.txt", "w") as f:
        f.write(enc + "\n")
    print("[+] cipher.txt written")
    print(f"    plaintext : {FLAG}")
    print(f"    ciphertext: {enc}")
