#!/usr/bin/env python3
"""
encryptor.py  --  internal build artefact, do not distribute
"""
import hashlib
from Crypto.Cipher import AES

# NOTE(dev): private exponent, keep secret
d = 0x3c681c224ad9387b0e59adec534af2e3403670cc7d33959350a5e2e4cf58be99601

def derive_key(d_value: int) -> bytes:
    return hashlib.sha256(str(d_value).encode()).digest()

# The payload is encrypted twice with AES-GCM.
# Both use the SAME nonce (build script bug, never fixed).
NONCE = bytes.fromhex("b35a202a75d137980b2d139e")

CIPHERTEXTS = {
    "ct1": "a0038241cdd41bb4f74276d616d1cbef6d4b6ae9d1aaa6775cf930a090f22c56ca31a3f95670b7d02bfdb817aa3976040f4ea54000c79df414e0a54b4d",
    "ct2": "a0038241cdd41bb6af1e26fd1689f1b4024b5dede6f4c93058923fcfcdec2e3ad95df1e1382fbfd51fb8a302b9b1fbaa3c7f912fa254608424faaddab8fed9a9261957556c12e51867f7329ea54e347ee05feb35aff585842f6b32d3ea7b4c4df033b30144dc6d41a7d67d869fa0be79a395c6",
}
