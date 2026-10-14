import sys,time
from fpylll import IntegerMatrix, LLL, BKZ
ns={}; exec(open("params.txt").read(),ns)
n=ns['n']; w=ns['w']; cts=ns['ciphertexts']; K=1<<64
def rec(s,method,block=30):
    B=IntegerMatrix(n+1,n+1)
    for i in range(n): B[i,i]=2; B[i,n]=w[i]*K
    for j in range(n): B[n,j]=1
    B[n,n]=s*K
    LLL.reduction(B)
    if method=='BKZ': BKZ.reduction(B,BKZ.Param(block_size=block))
    for r in range(n+1):
        row=[B[r,j] for j in range(n+1)]
        if row[n]==0 and all(abs(x)==1 for x in row[:n]):
            for sg in(1,-1):
                bb=[(sg*row[j]+1)//2 for j in range(n)]
                if all(x in(0,1) for x in bb) and sum(w[i]*bb[i] for i in range(n))==s: return bb
    return None
# first show LLL alone fails on block 0
print("LLL alone on block0:", "solved" if rec(cts[0],'LLL') else "FAILS (as intended)")
t=time.time(); allb=[]
for idx,s in enumerate(cts):
    bb=rec(s,'BKZ',30)
    if bb is None: print(f"block {idx} FAILED with BKZ30"); sys.exit(1)
    allb+=bb
by=bytearray()
for i in range(0,len(allb),8): by.append(int("".join(map(str,allb[i:i+8])),2))
print(f"BKZ30 solved all {len(cts)} blocks in {time.time()-t:.0f}s")
print("FLAG:", bytes(by).rstrip(b'\x00').decode())
