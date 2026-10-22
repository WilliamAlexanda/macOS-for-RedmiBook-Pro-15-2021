# EFI 组成（二进制文件请自行下载）

仓库里只放 `OC/config.plist`（序列号已清空）和本机生成的 `OC/ACPI/*.aml`。其余文件都能公开下载，按下表放进对应目录。

## OpenCore 1.0.8 — https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8 （RELEASE，X64）
- `EFI/BOOT/BOOTx64.efi`、`EFI/OC/OpenCore.efi`
- `EFI/OC/Drivers/`：`OpenHfsPlus.efi`、`OpenRuntime.efi`、`ResetNvramEntry.efi`
- `EFI/OC/Tools/`：`OpenShell.efi`

## EFI/OC/Kexts/

| Kext | 版本 | 来源 |
|---|---|---|
| Lilu | 1.7.3 | acidanthera/Lilu（1.7.2 正式版亦可） |
| VirtualSMC、SMCBatteryManager、SMCProcessor | 1.3.9 | acidanthera/VirtualSMC |
| WhateverGreen | 1.7.2 | acidanthera/WhateverGreen |
| AppleALC | 1.9.8 | acidanthera/AppleALC |
| SimpleHDA | 1.0.0 | laobamac/SimpleHDA（Tahoe RELEASE） |
| ECEnabler | 1.0.6 | 1Revenger1/ECEnabler |
| VoodooPS2Controller | 2.3.8 | acidanthera/VoodooPS2 |
| VoodooI2C、VoodooI2CHID | 2.9.1 | VoodooI2C/VoodooI2C — **需打补丁**，见下 |
| AirportItlwm（Tahoe 版） | 2.4.0 | laobamac/itlwm 的 Tahoe 构建（与 JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe 中 EFI 相同） |
| IntelBluetoothFirmware、IntelBTPatcher | 2.5.1 | OpenIntelWireless/IntelBluetoothFirmware |
| BlueToolFixup | 2.7.3 | acidanthera/BrcmPatchRAM |
| BrightnessKeys | 1.0.4 | acidanthera/BrightnessKeys |
| NVMeFix | 1.1.4 | acidanthera/NVMeFix |
| RestrictEvents | 1.1.7 | acidanthera/RestrictEvents |
| USBToolBox、UTBDefault | 1.2.0 / 1.0 | USBToolBox/kext |
| XHCI-unsupported | 0.9.2 | RehabMan/OS-X-USB-Inject-All |

## VoodooI2C 补丁
用 `../scripts/patch_kexts.py`，或者直接用 `Kexts-patched/VoodooI2C/` 里改好的两个 Info.plist 覆盖：
- `VoodooI2C.kext/Contents/Info.plist`
- `VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext/Contents/Info.plist`
