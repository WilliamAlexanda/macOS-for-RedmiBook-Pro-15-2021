# fvwalk.py <bios.bin> <outdir>: walk UEFI firmware volumes, LZMA-decompress GUID-defined sections and write PE32/TE/RAW sections out.
# Minimal; Tiano-compressed sections are only counted. Used to find the Setup (SetupUtility) module.
import sys,struct,lzma,uuid,os,re
LZMA='ee4e5898-3914-4259-9d6e-dc7bd79403cf'
out=sys.argv[2]; os.makedirs(out,exist_ok=True)
cnt=[0]; stats={}
def g(b,o): return str(uuid.UUID(bytes_le=bytes(b[o:o+16])))
def sections(b,depth,owner):
    o=0
    while o+4<=len(b):
        sz=int.from_bytes(b[o:o+3],'little'); t=b[o+3]; h=4
        if sz==0xffffff: sz=struct.unpack_from('<I',b,o+4)[0]; h=8
        if sz<h: break
        body=b[o+h:o+sz]
        if t==0x02:
            gd=g(body,0); doff=struct.unpack_from('<H',body,16)[0]-h
            data=body[doff:]
            if gd==LZMA:
                try: sections(lzma.LZMADecompressor(lzma.FORMAT_ALONE).decompress(data),depth+1,owner)
                except Exception as e: stats['lzmaerr']=stats.get('lzmaerr',0)+1
            else:
                try: sections(data,depth+1,owner)
                except Exception: pass
        elif t==0x01:
            stats['tiano']=stats.get('tiano',0)+1
        elif t==0x17:
            fvs(body,depth+1)
        elif t in (0x10,0x19,0x11):
            cnt[0]+=1; open(f'{out}/{owner}_{cnt[0]}_{t:02x}.bin','wb').write(body)
        o=(o+sz+3)&~3
def fvs(b,depth):
    for m in re.finditer(b'_FVH',b):
        s=m.start()-40
        if s<0: continue
        fl=struct.unpack_from('<Q',b,s+32)[0]; hl=struct.unpack_from('<H',b,s+48)[0]
        if fl>len(b)-s or hl<0x38: continue
        fv=b[s:s+fl]; o=hl
        while o+24<=len(fv):
            if fv[o:o+24]==b'\xff'*24: break
            name=g(fv,o); ft=fv[o+18]; sz=int.from_bytes(fv[o+20:o+23],'little'); att=fv[o+19]
            hh=24
            if att&1 and sz==0: sz=struct.unpack_from('<Q',fv,o+24)[0]; hh=32
            if sz<24: break
            if ft not in (0xf0,0x01):
                try: sections(fv[o+hh:o+sz],depth,name[:8])
                except Exception: pass
            o=(o+sz+7)&~7
fvs(open(sys.argv[1],'rb').read(),0)
print(cnt[0],stats)
