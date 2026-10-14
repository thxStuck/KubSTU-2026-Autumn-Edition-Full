#!/usr/bin/env python3
"""ASCII codes — beginner task generator."""

FLAG = "KubSTU{d3c1m4l_15_my_l4n6u4g3}"

if __name__ == "__main__":
    codes = " ".join(str(ord(c)) for c in FLAG)
    with open("codes.txt", "w") as f:
        f.write(codes + "\n")
    print("[+] codes.txt written")
    print(f"    plaintext: {FLAG}")
    print(f"    codes    : {codes}")
