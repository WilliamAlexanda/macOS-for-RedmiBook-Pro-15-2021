#!/usr/bin/env python3
"""Derive the zep245/IrisXe-macos-driver (NMXGPU, i915 port) OpenCore config from the working Redmi config.

Stage A = i915 display only, stage B = + accelerated WindowServer (the daily config).
Usage: python3 -I make_nmx_config.py <stage> <in config.plist> <out config.plist>
"""
import plistlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
stage = sys.argv[1].upper()
c = plistlib.load(open(sys.argv[2], "rb"))

# The driver owns the iGPU: no WhateverGreen, no VESA framebuffer (IONDRVSupport) taking display 0.
for k in c["Kernel"]["Add"]:
    if k["BundlePath"] == "WhateverGreen.kext":
        k["Enabled"] = False
c["Kernel"]["Block"] = [k for k in c["Kernel"]["Block"] if k.get("Identifier") != "com.apple.iokit.IONDRVSupport"]
c["Kernel"]["Block"].append({
    "Arch": "x86_64", "Comment": "NMXGPU: its framebuffer must be display 0", "Enabled": True,
    "Identifier": "com.apple.iokit.IONDRVSupport", "MaxKernel": "", "MinKernel": "", "Strategy": "Exclude",
})
c["DeviceProperties"]["Add"]["PciRoot(0x0)/Pci(0x2,0x0)"] = {
    "AAPL,ig-platform-id": bytes.fromhex("0000499A"),
    "device-id": bytes.fromhex("499A0000"),
    "AAPL,slot-name": "built-in",
}
# WindowServer (a platform binary) must load the ad-hoc signed Metal plugin: Lilu + AMFIPass on, plus the AMFI
# boot-args from the driver's HANDOFF.md. Without them WindowServer aborts in a loop
# ("mapping process is a platform binary, but mapped file is not").
c["Kernel"]["Add"] = [k for k in c["Kernel"]["Add"] if k["BundlePath"] != "AMFIPass.kext"]
lilu = next(i for i, k in enumerate(c["Kernel"]["Add"]) if k["BundlePath"] == "Lilu.kext")
amfipass = dict(c["Kernel"]["Add"][lilu], BundlePath="AMFIPass.kext", Comment="AMFIPass 1.4.1",
                ExecutablePath="Contents/MacOS/AMFIPass", Enabled=True)
c["Kernel"]["Add"].insert(lilu + 1, amfipass)
# Native GOP mode: i915 adopts the firmware's eDP mode.
c["UEFI"]["Output"]["Resolution"] = "Max"

ours = "keepsyms=1 debug=0x100 -v -vi2c-force-polling alcid=38 alcverbs=1"
nmx = ("nmxintel=1 nmxaccel=1 -nmintelfboff nmxcopyfwd=1 nmxmodern=1 nmxintelfb=1 -nmxnosnap"
       " amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0")
if stage == "B":
    nmx += " nmxws=1 nmxautoarm=1"
c["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"] = f"{ours} {nmx}"

out = Path(sys.argv[3])
plistlib.dump(c, open(out, "wb"))
print(out)
