#!/usr/bin/env python3
"""
Generator — "It really isn't enough" (KubSTU CTF, Crypto, hard).
Admin-only. Produces the player files (challenge.txt, hint.txt) plus
admin artefacts (gen.log, source_reference.py).
"""
import os
import hashlib
from Crypto.Util.number import getPrime, inverse, GCD
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

REAL_FLAG = b"KubSTU{50met1me5_7h3_m057_c0mp13x_7h1ng5_turn_0ut_70_b3_51mpl3_y0u_ju57_n33d_t0_74k3_4_cl053r_lo0k}"
FAKE_FLAG = b"KubSTU{7h15_15_n07_7h3_r34l_0n3_k3ep_1o0k1ng}"

N_BITS = 1024


def gen_rsa_small_d(delta):
    """RSA modulus with d ~ N^delta (small private exponent, large e)."""
    while True:
        p = getPrime(N_BITS // 2)
        q = getPrime(N_BITS // 2)
        if p == q:
            continue
        N = p * q
        phi = (p - 1) * (q - 1)
        d = getPrime(int(N_BITS * delta))
        if GCD(d, phi) != 1:
            continue
        e = inverse(d, phi)
        if e.bit_length() < N_BITS - 5:
            continue
        return N, e, d, p, q


# ---- key A: real, delta=0.26  (Wiener fails, Boneh-Durfee succeeds) ----
N, e, d_real, p, q = gen_rsa_small_d(0.26)

# ---- key B: decoy, delta=0.24  (breakable by Wiener) ----
Nd, ed, dd, pd, qd = gen_rsa_small_d(0.24)

# ---- source.py hidden behind layer 1 ----
FAKE_D = getPrime(266)          # plausible but WRONG private exponent (decoy constant)

source_code = f'''#!/usr/bin/env python3
"""
encryptor.py  --  internal build artefact, do not distribute
"""
import hashlib
from Crypto.Cipher import AES

# NOTE(dev): private exponent, keep secret
d = {hex(FAKE_D)}

def derive_key(d_value: int) -> bytes:
    return hashlib.sha256(str(d_value).encode()).digest()

# The payload is encrypted twice with AES-GCM.
# Both use the SAME nonce (build script bug, never fixed).
NONCE = bytes.fromhex("{{NONCE}}")

CIPHERTEXTS = {{
    "ct1": "{{CT1}}",
    "ct2": "{{CT2}}",
}}
'''

# ---- layer 2: AES-GCM, key = SHA256(str(d_real)) ----
key = hashlib.sha256(str(d_real).encode()).digest()
nonce = os.urandom(12)

c1 = AES.new(key, AES.MODE_GCM, nonce=nonce)
ct1, tag1 = c1.encrypt_and_digest(FAKE_FLAG)          # valid tag -> fake flag

c2 = AES.new(key, AES.MODE_GCM, nonce=nonce)
ct2, tag2 = c2.encrypt_and_digest(REAL_FLAG)          # same nonce
tag2_broken = bytes(b ^ 0xFF for b in tag2)           # tag deliberately corrupted

source_code = (source_code
               .replace("{NONCE}", nonce.hex())
               .replace("{CT1}", (ct1 + tag1).hex())
               .replace("{CT2}", (ct2 + tag2_broken).hex()))
source_bytes = source_code.encode()

# ---- layer 1: hybrid encrypt source under key A ----
rsa_pub = RSA.construct((N, e))
oaep = PKCS1_OAEP.new(rsa_pub)
src_aes_key = os.urandom(32)
src_nonce = os.urandom(12)
src_ct, src_tag = AES.new(src_aes_key, AES.MODE_GCM, nonce=src_nonce).encrypt_and_digest(source_bytes)
enc_key = oaep.encrypt(src_aes_key)

# ---- decoy blob under key B (Wiener bait) ----
decoy_pub = RSA.construct((Nd, ed))
decoy_ct = PKCS1_OAEP.new(decoy_pub).encrypt(b"Wiener really isn't enough here :)")

# ================= write player files =================
with open("challenge.txt", "w") as f:
    f.write("A = (\n")
    f.write(f"    {N},\n")
    f.write(f"    {e},\n")
    f.write(")\n\n")
    f.write("B = (\n")
    f.write(f"    {Nd},\n")
    f.write(f"    {ed},\n")
    f.write(")\n\n")
    f.write(f"enc_key   = {enc_key.hex()}\n")
    f.write(f"src_nonce = {src_nonce.hex()}\n")
    f.write(f"src_ct    = {src_ct.hex()}\n")
    f.write(f"src_tag   = {src_tag.hex()}\n\n")
    f.write(f"blob      = {decoy_ct.hex()}\n")

with open("hint.txt", "w") as f:
    f.write("Two public keys were shipped. One of them talks.\n")
    f.write("Recover the artefact, then read it very carefully.\n")

# ================= admin artefacts =================
with open("gen.log", "w") as f:
    f.write(f"[key A - REAL]\nN={N}\ne={e}\nd={d_real}\np={p}\nq={q}\n")
    f.write(f"delta_A={d_real.bit_length()/N.bit_length():.4f}\n\n")
    f.write(f"[key B - DECOY]\nN={Nd}\ne={ed}\nd={dd}\n")
    f.write(f"delta_B={dd.bit_length()/Nd.bit_length():.4f}\n\n")
    f.write(f"aes_key(sha256 str(d_real))={key.hex()}\n")
    f.write(f"nonce={nonce.hex()}\n")
    f.write(f"fake_d_in_source={hex(FAKE_D)}\n\n")
    f.write(f"REAL_FLAG={REAL_FLAG.decode()}\n")
    f.write(f"FAKE_FLAG={FAKE_FLAG.decode()}\n")

with open("source_reference.py", "wb") as f:
    f.write(source_bytes)

print("player files : challenge.txt, hint.txt")
print("admin files  : gen.log, source_reference.py")
print(f"delta_A={d_real.bit_length()/N.bit_length():.4f} (real)  "
      f"delta_B={dd.bit_length()/Nd.bit_length():.4f} (decoy)")
