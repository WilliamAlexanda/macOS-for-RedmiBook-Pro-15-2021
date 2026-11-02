# ifr.py <module.bin> <keyword>...: find the en-US string package and the IFR forms in a Setup module and print the OneOf
# questions whose prompt contains a keyword, with their varstore (name/GUID/size), offset and option values.
# Example: python3 ifr.py SetupUtility.bin DVMT
import sys,struct,uuid
d=open(sys.argv[1],'rb').read()
def u16(o): return struct.unpack_from('<H',d,o)[0]
# string packages
strs={}
for i in range(len(d)-0x40):
    if d[i+3]==4 and u16(i+4)>=0x34 and u16(i+4)<0x60:
        L=int.from_bytes(d[i:i+3],'little'); hs=struct.unpack_from('<I',d,i+4)[0]; so=struct.unpack_from('<I',d,i+8)[0]
        lang=d[i+0x2e:d.find(b'\0',i+0x2e)]
        if so!=hs or L>len(d)-i or not lang.startswith(b'en'): continue
        o=i+so; sid=1; tab={}
        while o<i+L:
            t=d[o]
            if t==0: break
            if t in (0x14,0x15):
                o+=1 if t==0x14 else 2
                e=o
                while d[e:e+2]!=b'\0\0': e+=2
                tab[sid]=d[o:e].decode('utf-16le','replace'); sid+=1; o=e+2
            elif t==0x20: sid+=d[o+1]; o+=2
            elif t==0x21: sid+=u16(o+1); o+=3
            elif t==0x22: o+=1+4+d[o+1]*0  # ext1
            else: break
        if len(tab)>len(strs): strs=tab; print('strpkg',hex(i),lang,len(tab),file=sys.stderr)
# form packages
stores={}
for i in range(len(d)-8):
    if d[i+3]==2 and d[i+4]==0x0e:
        L=int.from_bytes(d[i:i+3],'little')
        if L>len(d)-i or L<0x40: continue
        o=i+4
        while o<i+L:
            op=d[o]; ln=d[o+1]&0x7f
            if ln<2: break
            if op==0x24: stores[u16(o+18)]=(str(uuid.UUID(bytes_le=d[o+2:o+18])),u16(o+20),d[o+22:d.find(b'\0',o+22)].decode())
            if op==0x26: stores[u16(o+2)]=(str(uuid.UUID(bytes_le=d[o+4:o+20])),u16(o+24),d[o+26:d.find(b'\0',o+26)].decode())
            if op in (0x05,0x06,0x07):
                p=strs.get(u16(o+2),'?')
                if any(k in p for k in sys.argv[2:]):
                    vs=u16(o+8); print(f'\n[{hex(o)}] op{op:02x} "{p}" varstore={vs} {stores.get(vs)} offset={hex(u16(o+10))} flags={hex(d[o+12])}')
                    q=o+ln
                    while d[q]==0x09 or d[q] in (0x5b,0x5c,0x29,0x0a,0x2a) :
                        if d[q]==0x09:
                            ty=d[q+5]; v=int.from_bytes(d[q+6:q+6+[1,2,4,8][ty] if ty<4 else q+7],'little')
                            print(f'   {hex(v)} = {strs.get(u16(q+2),"?")}  flags={hex(d[q+4])}')
                        if d[q]==0x29 and q>o+ln+2: break
                        q+=d[q+1]&0x7f
            o+=ln
print('stores',len(stores),file=sys.stderr)
