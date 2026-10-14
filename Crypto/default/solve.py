#!/usr/bin/env python3
"""
Solve: e не дана — перебираем малые нечётные значения и берём e-й корень.
"""

from Crypto.Util.number import long_to_bytes
import gmpy2

with open("output.txt") as f:
    exec(f.read())  # n, c

for e in [3, 5, 7, 11, 13, 17, 19, 23]:
    m, exact = gmpy2.iroot(c, e)
    if not exact:
        continue
    try:
        flag = long_to_bytes(int(m)).decode()
    except UnicodeDecodeError:
        continue
    if "KubSTU{" in flag:
        print(f"[+] e = {e}")
        print(flag)
        break
else:
    print("[-] не нашли — возможно, m^e >= n, атака не подходит")
