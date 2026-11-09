# -*- coding: utf-8 -*-
# A00610_PmxImporter 계획 실측용 (2026-11-09). PMX 구조 덤프 - 시스템 파이썬.
#   python A00610_PmxImporter_probe_dump.py <a.pmx> [b.pmx ...] > dump.txt
import struct, sys, collections, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
class R:
    def __init__(s, b): s.b=b; s.p=0
    def r(s, fmt):
        v=struct.unpack_from("<"+fmt, s.b, s.p); s.p+=struct.calcsize("<"+fmt); return v if len(v)>1 else v[0]
    def raw(s,n): v=s.b[s.p:s.p+n]; s.p+=n; return v
def dump(path):
    rd=R(open(path,"rb").read())
    assert rd.raw(4)==b"PMX "
    ver=rd.r("f"); n=rd.r("B"); g=[rd.r("B") for _ in range(n)]
    enc, addUV, vis, tis, mis, bis, mois, ris = g
    def txt():
        L=rd.r("i"); b=rd.raw(L); return b.decode("utf-16-le" if enc==0 else "utf-8")
    idx={1:"b",2:"h",4:"i"}; uidx={1:"B",2:"H",4:"i"}
    vi=lambda: rd.r(uidx[vis]); ti=lambda: rd.r(idx[tis]); mi=lambda: rd.r(idx[mis]); bi=lambda: rd.r(idx[bis]); moi=lambda: rd.r(idx[mois]); ri=lambda: rd.r(idx[ris])
    print("=== ", path); print("ver",ver,"enc","utf16" if enc==0 else "utf8","addUV",addUV,"idx sizes v/t/m/b/morph/rb",vis,tis,mis,bis,mois,ris)
    name=txt(); ename=txt(); c=txt(); ec=txt(); print("name",name,"|",ename); print("comment:",c[:300].replace("\r\n"," / "))
    nv=rd.r("i"); wt=collections.Counter(); edge=[]
    for _ in range(nv):
        rd.raw(32+16*addUV); t=rd.r("B"); wt[["BDEF1","BDEF2","BDEF4","SDEF","QDEF"][t]]+=1
        if t==0: bi()
        elif t==1: bi();bi();rd.r("f")
        elif t in (2,4): [bi() for _ in range(4)]; rd.r("4f")
        elif t==3: bi();bi();rd.r("f"); rd.r("9f")
        edge.append(rd.r("f"))
    print("vertices",nv,dict(wt))
    nf=rd.r("i"); [vi() for _ in range(nf)]; print("faces(tri)",nf//3)
    nt=rd.r("i"); tex=[txt() for _ in range(nt)]; print("textures",nt); [print("  [%d] %s"%(i,t)) for i,t in enumerate(tex)]
    nm=rd.r("i"); print("materials",nm)
    for i in range(nm):
        n=txt(); en=txt(); diff=rd.r("4f"); spec=rd.r("3f"); sp=rd.r("f"); amb=rd.r("3f"); flag=rd.r("B"); ec=rd.r("4f"); es=rd.r("f")
        t=ti(); s=ti(); sm=rd.r("B"); ts=rd.r("B"); toon= rd.r("B") if ts==1 else ti(); memo=txt(); fc=rd.r("i")
        f=lambda k: tex[k] if 0<=k<len(tex) else "-"
        print("  [%d] %s | %s diff=%s amb=%s spec=%s/%g flag=%s edge=%s/%g tex=%s sphere=%s(mode %d) toon=%s faces=%d memo=%s"%(i,n,en,tuple(round(x,3) for x in diff),tuple(round(x,2) for x in amb),tuple(round(x,2) for x in spec),sp,bin(flag),tuple(round(x,2) for x in ec),es,f(t),f(s),sm,("shared%d"%toon) if ts else f(toon),fc//3,memo[:40].replace("\n"," ")))
    nb=rd.r("i"); print("bones",nb); flags=collections.Counter(); bones=[]
    for i in range(nb):
        n=txt(); en=txt(); pos=rd.r("3f"); par=bi(); lay=rd.r("i"); fl=rd.r("H")
        if fl&1: bi()
        else: rd.r("3f")
        if fl&0x300: bi(); rd.r("f")
        if fl&0x400: rd.r("3f")
        if fl&0x800: rd.r("3f"); rd.r("3f")
        if fl&0x2000: rd.r("i")
        ik=None
        if fl&0x20:
            tgt=bi(); loop=rd.r("i"); lim=rd.r("f"); nl=rd.r("i"); links=[]
            for _ in range(nl):
                b=bi(); h=rd.r("B"); 
                if h: rd.r("3f"); rd.r("3f")
                links.append(b)
            ik=(tgt,loop,links)
        for k,v in [(0x20,"IK"),(0x100,"addRot"),(0x200,"addMove"),(0x400,"fixedAxis"),(0x800,"localAxis"),(0x2000,"extParent"),(0x10,"operable")]:
            if fl&k: flags[v]+=1
        if not fl&0x8: flags["invisible"]+=1
        bones.append((n,en,par,pos,fl,ik,lay))
    print(" bone flag counts",dict(flags))
    for i,(n,en,par,pos,fl,ik,lay) in enumerate(bones[:400]):
        print("  b%d %s|%s par=%d pos=%s layer=%d fl=%s%s"%(i,n,en,par,tuple(round(x,3) for x in pos),lay,hex(fl),(" IK tgt=%d links=%s"%(ik[0],ik[2])) if ik else ""))
    nmo=rd.r("i"); mt=collections.Counter(); panel=collections.Counter(); names=[]
    for i in range(nmo):
        n=txt(); en=txt(); pn=rd.r("B"); t=rd.r("B"); c=rd.r("i")
        tname=["group","vertex","bone","uv","uv1","uv2","uv3","uv4","material","flip","impulse"][t]; mt[tname]+=1; panel[pn]+=1; names.append((n,en,tname,pn,c))
        for _ in range(c):
            if t in (0,9): moi(); rd.r("f")
            elif t==1: vi(); rd.r("3f")
            elif t==2: bi(); rd.r("3f"); rd.r("4f")
            elif 3<=t<=7: vi(); rd.r("4f")
            elif t==8: mi(); rd.r("B"); rd.raw(4*28)
            elif t==10: ri(); rd.r("B"); rd.r("6f")
    print("morphs",nmo,dict(mt),"panel",dict(panel))
    for n,en,t,pn,c in names: print("   %s|%s %s panel%d n=%d"%(n,en,t,pn,c))
    nd=rd.r("i")
    for _ in range(nd):
        txt();txt();rd.r("B"); c=rd.r("i")
        for _ in range(c):
            k=rd.r("B"); bi() if k==0 else moi()
    print("display frames",nd)
    nr=rd.r("i"); modes=collections.Counter()
    for _ in range(nr):
        txt();txt();bi();rd.r("B");rd.r("H");rd.r("B");rd.r("3f");rd.r("3f");rd.r("3f");rd.r("5f"); modes[rd.r("B")]+=1
    print("rigid bodies",nr,"modes",dict(modes))
    nj=rd.r("i"); print("joints",nj, "remain bytes", len(rd.b)-rd.p)
for p in sys.argv[1:]: dump(p)
