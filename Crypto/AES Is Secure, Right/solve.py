#!/usr/bin/env python3

import re
from hashlib import sha256
from pathlib import Path

from Crypto.Cipher import AES


import sys

def _find(name):
    here = Path(__file__).resolve().parent
    candidates = []
    if len(sys.argv) > 1:
        candidates.append(Path(sys.argv[1]))
    candidates += [
        here / name,                      # рядом со скриптом
        here.parent / "player" / name,    # admin/ + player/
        Path.cwd() / name,                # текущая папка
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(
        f"{name} не найден. Положи его рядом со скриптом или укажи путь: "
        f"python3 solve.py <путь к {name}>")

OUTPUT_FILE = _find("output.txt")

FLAG_RE = re.compile(r"KubSTU\{[^}]*\}")


def load_ciphertext():
    with OUTPUT_FILE.open("r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    ct_line = next(line for line in lines if line.startswith("ct ="))
    ct_hex = ct_line.split("=", 1)[1].strip()

    hint_line = next((line for line in lines if line.startswith("#")), "")
    first_digit = None
    match = re.search(r"starts with (\d)", hint_line)
    if match:
        first_digit = match.group(1)

    return bytes.fromhex(ct_hex), first_digit


def unprepare(data: bytes, block_size: int = 16):
    if not data or len(data) % block_size != 0:
        return None

    total_blocks = len(data) // block_size
    pad_byte = total_blocks & 0xff

    pad_len = 0
    for byte in reversed(data):
        if byte != pad_byte:
            break
        pad_len += 1

    if pad_len == 0 or pad_len > block_size:
        return None

    return data[:-pad_len]


def decrypt(ciphertext: bytes, pin: str):
    key = sha256(pin.encode()).digest()[:16]
    cipher = AES.new(key, AES.MODE_ECB)

    blocks = [
        ciphertext[i:i + 16]
        for i in range(0, len(ciphertext), 16)
    ]

    blocks = [
        cipher.decrypt(block)
        for block in blocks
    ]

    blocks.reverse()

    shift = sum(int(x) for x in pin) % len(blocks)

    if shift:
        blocks = blocks[-shift:] + blocks[:-shift]

    data = b"".join(blocks)

    return unprepare(data)


def main():
    ciphertext, first_digit = load_ciphertext()
    print(f"[+] ciphertext: {len(ciphertext)} bytes, "
          f"{len(ciphertext) // 16} blocks")

    digits = first_digit if first_digit else "0123456789"
    print(f"[+] PIN candidates: {digits}xxx "
          f"({len(digits) * 1000} total)")

    for first in digits:
        for rest in range(1000):
            pin = f"{first}{rest:03d}"

            plaintext = decrypt(ciphertext, pin)
            if plaintext is None:
                continue

            try:
                text = plaintext.decode("ascii")
            except UnicodeDecodeError:
                continue

            match = FLAG_RE.search(text)
            if not match:
                continue

            print(f"[+] PIN:  {pin}")
            print(f"[+] decrypted text:\n{text}")
            print(f"[+] FLAG: {match.group(0)}")
            return

    print("[-] Flag not found")


if __name__ == "__main__":
    main()
