#!/usr/bin/env python3
"""
Solver — Caesar shift.
We don't even need to know the shift: try all 26 and look for "KubSTU{".
"""

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

enc = open("cipher.txt").read().strip()

for shift in range(26):
    guess = caesar(enc, -shift)
    if guess.startswith("KubSTU{"):
        print(f"[+] shift = {shift}")
        print(f"[+] FLAG: {guess}")
        break
