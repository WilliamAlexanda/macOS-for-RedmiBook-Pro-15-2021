#!/usr/bin/env python3
"""Derive the native-driver OpenCore config (WhateverXe + Apple's Tiger Lake drivers) from the base config.

Needs: DVMT 128 MB (docs/dvmt-insyde.md), WhateverXe Graphics 0.4.1 installed in macOS, and the patched
WhateverXe.kext from patches/whateverxe-0.8.0 plus AMFIPassMod.kext (WhateverXe Graphics release) in EFI/OC/Kexts.
Usage: python3 -I make_wex_config.py <in config.plist> <out config.plist>
"""
import plistlib
import sys
from pathlib import Path

c = plistlib.load(open(sys.argv[1], "rb"))
add = c["Kernel"]["Add"]
for k in add:
    if k["BundlePath"] == "WhateverGreen.kext":
        k["Enabled"] = False  # WhateverXe replaces WhateverGreen on this iGPU
add[:] = [k for k in add if k["BundlePath"] not in ("AMFIPass.kext", "AMFIPassMod.kext", "WhateverXe.kext")]
lilu = next(i for i, k in enumerate(add) if k["BundlePath"] == "Lilu.kext")
base = dict(add[lilu], MaxKernel="", MinKernel="", Arch="Any", PlistPath="Contents/Info.plist", Enabled=True)
add.insert(lilu + 1, dict(base, BundlePath="AMFIPassMod.kext", Comment="AMFIPass 1.4.1 Mod (WhateverXe-Graphics)",
                          ExecutablePath="Contents/MacOS/AMFIPass"))
add.insert(lilu + 2, dict(base, BundlePath="WhateverXe.kext",
                          Comment="WhateverXe 0.8.0 + eDP keep / bpc / backlight patches (RedmiBook)",
                          ExecutablePath="Contents/MacOS/WhateverXe"))
c["DeviceProperties"]["Add"].pop("PciRoot(0x0)/Pci(0x2,0x0)", None)
c["UEFI"]["Output"]["Resolution"] = "Max"  # the firmware must train the panel at native 3200x2000; the driver keeps that link
ours = "keepsyms=1 debug=0x100 -v -vi2c-force-polling alcid=38 alcverbs=1"
wex = "-allow3d -disablegfxfirmware -wex-tgl-edp-keep -wex-edp-fix-training -wex-edp-no-extcap"
c["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"] = f"{ours} {wex}"
out = Path(sys.argv[2])
plistlib.dump(c, open(out, "wb"))
print(out)
