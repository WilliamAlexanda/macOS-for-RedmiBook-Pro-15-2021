#!/usr/bin/env python3
"""Teach VoodooI2C / VoodooGPIO about the RedmiBook Pro 15 2021's Tiger Lake I2C and GPIO controllers.

VoodooI2C 2.9.1 has no Tiger Lake PCI personality (I2C 8086:A0E8-A0EB), and VoodooGPIO's TigerLakeLP
class only matches INTC1055, while this firmware names the same TGL-LP GPIO block INT34C5
(Linux pinctrl-tigerlake uses one pin table for both). Idempotent.

Usage: python3 -I scripts/patch_kexts.py
"""
import copy
import plistlib
from pathlib import Path

KEXTS = Path(__file__).resolve().parent.parent / "EFI/OC/Kexts"

i2c = KEXTS / "VoodooI2C.kext/Contents/Info.plist"
p = plistlib.load(open(i2c, "rb"))
pers = p["IOKitPersonalities"]
if "VoodooI2CPCITigerLakeController" not in pers:
    tgl = copy.deepcopy(pers["VoodooI2CPCIIceLakeController"])
    tgl["IOPCIMatch"] = "0xa0e88086&0xFFFCFFFF"
    pers["VoodooI2CPCITigerLakeController"] = tgl
    plistlib.dump(p, open(i2c, "wb"))
    print("VoodooI2C: added Tiger Lake I2C personality")

gpio = KEXTS / "VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext/Contents/Info.plist"
p = plistlib.load(open(gpio, "rb"))
names = p["IOKitPersonalities"]["VoodooGPIOTigerLakeLP"]["IONameMatch"]
if "INT34C5" not in names:
    names.append("INT34C5")
    plistlib.dump(p, open(gpio, "wb"))
    print("VoodooGPIO: TigerLakeLP now matches INT34C5")
