# unpack_xiaomi_bios.py <RMATG5B0P0xxx.exe> <outdir>
# Xiaomi's BIOS updater is an Insyde H2OFFT 7z SFX whose archive bytes are rotated left by 1 bit.
# This undoes the rotation and extracts the archive with bsdtar; the BIOS image is isflash_release.bin.
# Nothing is executed.
import subprocess,sys,os
exe,out=sys.argv[1],sys.argv[2]
d=open(exe,'rb').read()
cfg=d.find(b';!@InstallEnd@!')
if cfg<0: sys.exit('no 7z SFX config found')
start=d.find(b'\n',cfg)+1
ror=bytes(((b>>1)|((b&1)<<7)) for b in range(256))
arc=d[start:].translate(ror)
if arc[:6]!=b'7z\xbc\xaf\x27\x1c': sys.exit('decoded data is not a 7z archive')
os.makedirs(out,exist_ok=True)
p=os.path.join(out,'payload.7z'); open(p,'wb').write(arc)
subprocess.run(['bsdtar','-xf',p,'-C',out],check=True)
print('extracted to',out)
