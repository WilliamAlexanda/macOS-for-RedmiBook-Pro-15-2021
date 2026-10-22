#!/usr/bin/env python3
"""Build Redmi (i5-11300H, Tiger Lake) OpenCore configs from the XPS 13 Plus project's config-install.plist.

Usage: python3 -I scripts/make_config.py <serial> <mlb> <uuid> <rom-hex>
Writes EFI/OC/config.plist (install config) and EFI/OC/config-accel.plist (Iris Xe acceleration, use after install).
"""
import copy
import os
import plistlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "refs/Hackintosh-XPS13Plus-IrisXe-Tahoe/EFI/OC/config-install.plist"
OUT = ROOT / "EFI/OC"

serial, mlb, uuid, rom = sys.argv[1:5]
ALCID = os.environ.get("ALCID", "38")  # speaker on 0x14 (69/99 put it on 0x1b)

p = plistlib.load(open(SRC, "rb"))

# ACPI: every XPS table and rename is Dell-specific. The Redmi's SSDTs come from SSDTTime (run on the laptop itself).
ssdt = plistlib.load(open(ROOT / "ssdttime/patches_OC.plist", "rb"))["ACPI"]
p["ACPI"]["Patch"] = ssdt["Patch"]
p["ACPI"]["Delete"] = []
p["ACPI"]["Add"] = ssdt["Add"]

# Kexts: drop Dell / Raptor Lake specific ones, add AppleALC + ECEnabler.
drop = ("SMCDellSensors", "SMCLightSensor", "SMCSuperIO", "CpuTopologyRebuild", "NootedGreen")
tmpl = p["Kernel"]["Add"]
kexts = [k for k in tmpl if not k["BundlePath"].startswith(drop) and k["BundlePath"] != "itlwm.kext"]
base = next(k for k in tmpl if k["BundlePath"] == "Lilu.kext")


def entry(name, enabled=True):
    e = copy.deepcopy(base)
    e.update(BundlePath=f"{name}.kext", ExecutablePath=f"Contents/MacOS/{name}", Comment=name, Enabled=enabled)
    return e


lilu = next(i for i, k in enumerate(kexts) if k["BundlePath"] == "Lilu.kext")
vsmc = next(i for i, k in enumerate(kexts) if k["BundlePath"] == "VirtualSMC.kext")
kexts.insert(vsmc + 1, entry("ECEnabler"))
kexts.insert(lilu + 1, entry("AppleALC"))
# Tahoe dropped AppleHDA; SimpleHDA re-injects it (Lilu -> AppleALC -> SimpleHDA).
shda = entry("SimpleHDA")
shda.update(MinKernel="25.0.0", MaxKernel="25.99.99")
kexts.insert(lilu + 2, shda)
if not any(k["BundlePath"] == "AirportItlwm.kext" for k in kexts):
    kexts.append(entry("AirportItlwm", enabled=False))
# macOS is installed: use AirportItlwm (native Wi-Fi menu) instead of itlwm (needs HeliPort).
for k in kexts:
    if k["BundlePath"] in ("itlwm.kext", "AirportItlwm.kext"):
        k["Enabled"] = k["BundlePath"] == "AirportItlwm.kext"
p["Kernel"]["Add"] = kexts

# Redmi firmware runtime services touch the SPI flash MMIO (0xFF000000+); devirtualising it panics the kernel at ~1s.
p["Booter"]["Quirks"]["DevirtualiseMmio"] = False
p["Booter"]["MmioWhitelist"] = []
# 3200x2000 panel: 1x console font so a whole panic log fits on one screen.
p["UEFI"]["Output"]["UIScale"] = 1
# No acceleration, so no HiDPI modes. The Insyde GOP offers 3200x2000, 1920x1200 and 4:3 modes only
# (OpenCore debug log); 1920x1200 keeps 16:10 and the panel fitter scales it to native for free.
p["UEFI"]["Output"]["Resolution"] = os.environ.get("SAFERES", "1920x1200")

# VT-d is often left on in Redmi BIOS (no option to turn it off).
p["Kernel"]["Quirks"]["DisableIoMapper"] = True
# Tiger Lake hangs at EXITBS:START without it (XCPM touches MSRs the CPU does not have).
p["Kernel"]["Quirks"]["AppleXcpmExtraMsrs"] = True
# Spoof Ice Lake-U (0x706E5): native in Tahoe and matches MacBookPro16,2.
p["Kernel"]["Emulate"]["Cpuid1Data"] = bytes.fromhex("E5060700000000000000000000000000")
p["Kernel"]["Emulate"]["Cpuid1Mask"] = bytes.fromhex("FFFFFFFF000000000000000000000000")

# The USB installer made by createinstallmedia is HFS+; PC firmware cannot read it without this driver.
p["UEFI"]["Drivers"] = [
    {"Arguments": "", "Comment": d, "Enabled": True, "HideVerbose": False, "LoadEarly": False, "Path": d}
    for d in ("OpenHfsPlus.efi", "OpenRuntime.efi", "ResetNvramEntry.efi")
]
p["Misc"]["Tools"] = [
    {"Arguments": "", "Auxiliary": True, "Comment": "OpenShell", "Enabled": True, "Flavour": "OpenShell:UEFIShell:Shell",
     "FullNvramAccess": False, "Name": "OpenShell", "Path": "OpenShell.efi", "RealPath": False, "TextMode": False}
]

nv = p["NVRAM"]["Add"]
nv["4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102"]["revcpuname"] = "11th Gen Intel(R) Core(TM) i5-11300H"
nv["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"] = f"keepsyms=1 debug=0x100 -v -vi2c-force-polling alcid={ALCID} alcverbs=1 -igfxvesa"
igpu = p["DeviceProperties"]["Add"].pop("PciRoot(0x0)/Pci(0x2,0x0)")

g = p["PlatformInfo"]["Generic"]
g.update(SystemProductName="MacBookPro16,2", SystemSerialNumber=serial, MLB=mlb, SystemUUID=uuid,
         ROM=bytes.fromhex(rom), ProcessorType=0)


# Accelerated config: WhateverXe (b00t0x) drives the genuine Tiger Lake 9A49 with Apple's 16.0.32 TGL stack
# (installed into /Library by the WhateverXe-Graphics pkg). WEX replaces WhateverGreen; AMFIPass Mod validates
# the re-signed payloads. WEX="DEBUG" picks the debug build for the first boots.
a = copy.deepcopy(p)
a["Kernel"]["Add"] = [k for k in a["Kernel"]["Add"] if k["BundlePath"] != "WhateverGreen.kext"]
a["Kernel"]["Add"][1:1] = [entry("AMFIPass"), entry("WhateverXe")]
nva = a["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
nva["csr-active-config"] = bytes.fromhex("03080000")
nva["boot-args"] = f"keepsyms=1 debug=0x100 -v -vi2c-force-polling alcid={ALCID} alcverbs=1 -allow3d -disablegfxfirmware -wexdbg -igfxdvmt"
# DVMT is fixed at 60MB on this BIOS (WEX log: GMS 0xfe). Per WEX README: -igfxdvmt plus these two properties,
# which cap the display memory pool at 60MB (0x03C00000). Without them the TGL framebuffer hangs at takeover.
a["DeviceProperties"]["Add"]["PciRoot(0x0)/Pci(0x2,0x0)"] = {
    "framebuffer-patch-enable": bytes.fromhex("01000000"),
    "framebuffer-stolenmem": bytes.fromhex("0000C003"),
}
# The GOP/boot framebuffer is handed off inside the 60MB stolen pool until the accelerator is up; a native
# 3200x2000 GOP mode (25.6MB) plus the driver's own scanout leaves the accelerator almost nothing.
# Boot the picker/console at a small mode in the accelerated config.
a["UEFI"]["Output"]["Resolution"] = os.environ.get("GOPRES", "1024x768")
# NOSHDA=1: drop SimpleHDA from the accelerated config (A/B test against the TGL accelerator start).
if os.environ.get("NOSHDA") == "1":
    for k in a["Kernel"]["Add"]:
        if k["BundlePath"] == "SimpleHDA.kext":
            k["Enabled"] = False
# DIAG=1: needs the DEBUG Lilu in EFI/OC/Kexts; keeps every plugin's debug log in the kernel message buffer.
if os.environ.get("DIAG") == "1":
    nva["boot-args"] += " liludump=90" + os.environ.get("EXTRA", "")

# MODE=accel makes the WhateverXe config the one OpenCore boots (config.plist); the no-acceleration config is
# kept beside it as config-safe.plist. Default: the safe config is config.plist.
if os.environ.get("MODE") == "accel":
    names = ("config-safe.plist", "config.plist")
else:
    names = ("config.plist", "config-accel.plist")
    (OUT / "config-safe.plist").unlink(missing_ok=True)
plistlib.dump(p, open(OUT / names[0], "wb"))
plistlib.dump(a, open(OUT / names[1], "wb"))
print("wrote", *(OUT / n for n in names))
