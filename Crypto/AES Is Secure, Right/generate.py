#!/usr/bin/env python3
"""
Organizer-only generator for "AES Is Secure, Right?".

Reproduces the shipped instance exactly (fixed PIN), so re-running it
regenerates the identical player/output.txt. Set RANDOMIZE=True to mint a
fresh instance (new PIN) instead.

The encrypted payload is a short certificate-revocation note with the flag
on the last line. It spans several AES blocks on purpose: with only 2
blocks the `shift = sum(digits) % blocks` mechanic would collapse to a coin
flip and the block-permutation step would never really be exercised.
"""
import re
import sys
import secrets
from hashlib import sha256
from pathlib import Path

ADMIN = Path(__file__).resolve().parent
PLAYER = ADMIN.parent / "player"
sys.path.insert(0, str(PLAYER))

from intern_cipher import prepare, transform          # noqa: E402
from Crypto.Cipher import AES                          # noqa: E402

FLAG = "KubSTU{c3rt1f1c4t3_r3v0k3d}"

CERTIFICATE = (
    "CERTIFICATE OF COMPLETION\n"
    "Course: Information Security Basics\n"
    "Issued to: KubSTU Intern Lab\n"
    "Status: REVOKED\n"
    f"Reason: {FLAG}\n"
)

RANDOMIZE = False
FIXED_PIN = "2785"          # the shipped instance


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


def self_check(secret_bytes, pin, ciphertext):
    """Padding round-trip + full decrypt must recover the flag before shipping."""
    assert unprepare(prepare(secret_bytes)) == secret_bytes, "padding round-trip failed"

    key = sha256(pin.encode()).digest()[:16]
    cipher = AES.new(key, AES.MODE_ECB)
    blocks = [cipher.decrypt(ciphertext[i:i + 16]) for i in range(0, len(ciphertext), 16)]
    blocks.reverse()
    shift = sum(int(x) for x in pin) % len(blocks)
    if shift:
        blocks = blocks[-shift:] + blocks[:-shift]
    recovered = unprepare(b"".join(blocks))
    assert recovered == secret_bytes, "full pipeline self-check failed"

    text = recovered.decode("ascii")
    m = re.search(r"KubSTU\{[^}]*\}", text)
    assert m and m.group(0) == FLAG, "flag not recoverable from decrypted text"
    return len(ciphertext) // 16


def generate_pin():
    return secrets.choice("123456789") + "".join(secrets.choice("0123456789") for _ in range(3))


def main():
    secret_bytes = CERTIFICATE.encode("ascii")
    pin = generate_pin() if RANDOMIZE else FIXED_PIN

    ciphertext = transform(secret_bytes, pin)
    blocks = self_check(secret_bytes, pin, ciphertext)
    assert blocks >= 3, "secret too short: block-permutation step would be degenerate"

    out = PLAYER / "output.txt"
    with out.open("w", encoding="utf-8") as fh:
        fh.write(f"ct = {ciphertext.hex()}\n")
        fh.write(f"# Hint: PIN starts with {pin[0]}\n")

    with (ADMIN / "SECRETS.txt").open("w", encoding="utf-8") as fh:
        fh.write(f"pin = {pin}\n")
        fh.write(f"flag = {FLAG}\n")
        fh.write(f"secret =\n{CERTIFICATE}")

    print(f"[+] PIN: {pin}  |  blocks: {blocks}  |  flag: {FLAG}")
    print(f"[+] wrote {out}")


if __name__ == "__main__":
    main()
