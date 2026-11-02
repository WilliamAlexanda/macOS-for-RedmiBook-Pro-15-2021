# EFI 组成 / EFI components

**中文**：仓库里只放了 `OC/config.plist`（基础配置）、`OC/config-igpu-accel.plist`（核显加速配置）和本机生成的 `OC/ACPI/*.aml`，序列号都已清空。其余文件都能公开下载，按下表放进对应目录。

**English**: this repo only contains `OC/config.plist` (base config), `OC/config-igpu-accel.plist` (iGPU-accelerated config) and the machine's own `OC/ACPI/*.aml`, with serials blanked. Everything else is publicly downloadable; put it where the tables below say.

## OpenCore 1.0.8 — https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8 (RELEASE, X64)
- `EFI/BOOT/BOOTx64.efi`, `EFI/OC/OpenCore.efi`
- `EFI/OC/Drivers/`: `OpenHfsPlus.efi`, `OpenRuntime.efi`, `ResetNvramEntry.efi`
- `EFI/OC/Tools/`: `OpenShell.efi`

## EFI/OC/Kexts/

| Kext | 版本 Version | 来源 Source | 备注 Notes |
|---|---|---|---|
| Lilu | 1.7.3 | acidanthera/Lilu (1.7.2 release also works) | |
| **AMFIPass** | **1.4.1** | dortania/OpenCore-Legacy-Patcher `payloads/Kexts/Acidanthera/AMFIPass-v1.4.1-RELEASE.zip` (SHA-256 `07b266145906db41f4b13a7938fbb173ea28888cc1fa65f84417f8820adc961e`) | 仅加速配置用 / accelerated config only |
| VirtualSMC, SMCBatteryManager, SMCProcessor | 1.3.9 | acidanthera/VirtualSMC | |
| WhateverGreen | 1.7.2 | acidanthera/WhateverGreen | 仅基础配置用 / base config only |
| AppleALC | 1.9.8 | acidanthera/AppleALC | `alcid=38` |
| SimpleHDA | 1.0.0 | laobamac/SimpleHDA (Tahoe RELEASE) | 把 AppleHDA 带回 Tahoe / restores AppleHDA on Tahoe |
| ECEnabler | 1.0.6 | 1Revenger1/ECEnabler | |
| VoodooPS2Controller | 2.3.8 | acidanthera/VoodooPS2 | |
| VoodooI2C, VoodooI2CHID | 2.9.1 | VoodooI2C/VoodooI2C | **需打补丁 / needs the patch below** |
| AirportItlwm (Tahoe) | 2.4.0 | laobamac/itlwm Tahoe build (same as the EFI in JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe) | |
| IntelBluetoothFirmware, IntelBTPatcher | 2.5.1 | OpenIntelWireless/IntelBluetoothFirmware | |
| BlueToolFixup | 2.7.3 | acidanthera/BrcmPatchRAM | |
| BrightnessKeys | 1.0.4 | acidanthera/BrightnessKeys | |
| NVMeFix | 1.1.4 | acidanthera/NVMeFix | |
| RestrictEvents | 1.1.7 | acidanthera/RestrictEvents | |
| USBToolBox, UTBDefault | 1.2.0 / 1.0 | USBToolBox/kext | |
| XHCI-unsupported | 0.9.2 | RehabMan/OS-X-USB-Inject-All | |

## 核显驱动（装在 macOS 里，不放进 EFI） / iGPU driver (installed in macOS, not in the EFI)

[zep245/IrisXe-macos-driver](https://github.com/zep245/IrisXe-macos-driver): v1.0.3 `nmxgpu-macos-15.zip` + v1.0.0 `nmx-vulkan-macos-15-intel.zip`. 步骤见 / steps in [../docs/igpu-zep245.md](../docs/igpu-zep245.md).

## VoodooI2C 补丁 / VoodooI2C patch

用 `../scripts/patch_kexts.py`，或者直接用 `Kexts-patched/VoodooI2C/` 里改好的两个 Info.plist 覆盖 / Run `../scripts/patch_kexts.py`, or overwrite these two files with the copies in `Kexts-patched/VoodooI2C/`:
- `VoodooI2C.kext/Contents/Info.plist`
- `VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext/Contents/Info.plist`
