#!/usr/bin/env python3
"""Solver — ASCII codes: turn each number back into its character."""

codes = open("codes.txt").read().split()
flag = "".join(chr(int(x)) for x in codes)
print(f"[+] FLAG: {flag}")
