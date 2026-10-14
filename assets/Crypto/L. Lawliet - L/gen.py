# L. Lawliet HARD: subset-sum density ~0.76 (BKZ required), comments stripped
import random
FLAG=b"KubSTU{y0u_n33d_70_6e_4_re41_d373ct1ve_7o_5o1v3_7h15}"
n=64; Wbits=84              # density = 64/84 = 0.762
random.seed(1337)
padded=FLAG+b"\x00"*((-len(FLAG))%8)
nblocks=len(padded)//8
w=[random.randrange(2**(Wbits-1),2**Wbits) for _ in range(n)]
cts=[]
for i in range(nblocks):
    blk=int.from_bytes(padded[i*8:(i+1)*8],'big')
    bits=[(blk>>(63-j))&1 for j in range(64)]
    cts.append(sum(w[k]*bits[k] for k in range(64)))
with open("params.txt","w") as f:
    f.write(f"n = {n}\n\nw = [\n")
    for x in w: f.write(f"    {x},\n")
    f.write("]\n\nciphertexts = [\n")
    for c in cts: f.write(f"    {c},\n")
    f.write("]\n")
print(f"generated: n={n}, density={n/Wbits:.3f}, blocks={nblocks}")
