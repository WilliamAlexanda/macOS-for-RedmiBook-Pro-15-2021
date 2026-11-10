# macOS Tahoe on RedmiBook Pro 15 2021 (Intel i5-11300H)

**中文** | [English](#english)

在 **RedmiBook Pro 15 2021（Intel 版，i5-11300H / Iris Xe 9A49）** 上用 OpenCore 运行 **macOS Tahoe 26.7.1 (25G241)** 的完整记录，与 Windows 双系统共存。**核显 Metal 加速已跑通**（3200×2000 @ 90Hz），并且**苹果原生核显驱动也已点亮**（WhateverXe + 补丁，2026-11-10）。

> ⚠️ 黑苹果有风险。仓库里的 `config.plist` / `config-igpu-accel.plist` / `config-whateverxe.plist` 都已清空序列号（SystemSerialNumber / MLB / SystemUUID / ROM），使用前请用 GenSMBIOS 或 `macserial -m MacBookPro16,2` 生成你自己的一套。

## 硬件与状态

| 部件 | 型号 | 状态 |
|---|---|---|
| CPU | i5-11300H（Tiger Lake-H35，model 0x8C） | ✅ 伪装成 Ice Lake-U（`Cpuid1Data E5060700`） |
| 核显 | Iris Xe `8086:9A49` | ✅ **苹果原生驱动**（实验）：WhateverXe 0.8.0 + 本仓库补丁，见 [docs/igpu-whateverxe-native.md](docs/igpu-whateverxe-native.md)<br>✅ **Metal 加速**（稳定）：[zep245/IrisXe-macos-driver](https://github.com/zep245/IrisXe-macos-driver)（i915 移植），见 [docs/igpu-zep245.md](docs/igpu-zep245.md) |
| 屏幕 | 天马 TL156MDMP01，3200×2000，90/60Hz | ✅ 加速后原生 3200×2000 @ 90Hz；未加速时用 1920×1200 GOP |
| 硬盘 | Intel 660p 1TB（SSDPEKNW010T8） | ✅ |
| 网卡 | Intel AX201 | ✅ AirportItlwm（原生 Wi-Fi 菜单）；企业级 Wi-Fi（802.1X）需换用修复版，见 [docs/wifi-8021x.md](docs/wifi-8021x.md) |
| 蓝牙 | Intel 8087:0026 | ✅ IntelBluetoothFirmware |
| 声卡 | Realtek ALC256（控制器 A0C8 处于 SST/DSP 模式） | ✅ 扬声器 / 耳机：SimpleHDA + `alcid=38` |
| 内置麦克风 | DMIC 接在 Intel 智音技术 DSP 上 | ❌ |
| 触摸板 | I2C HID `GXT7863`，I2C1 (A0E9)，GPIO `INT34C5` | ✅ VoodooI2C（需补丁，见下文） |
| 键盘 | PS/2 | ✅ VoodooPS2 |
| 摄像头 | XiaoMi USB 2.0 Webcam（UVC） | ✅ 免驱 |
| 指纹 | Goodix 27c6:581a | ❌ |
| 睡眠 | — | ❌ 不建议使用 |

BIOS：Insyde H2O `RMATG5B0P0D0D`。DVMT 出厂固定为 60MB（GMS 0xFE），BIOS 里看不到这个选项，但**可以在 macOS 里改成 128MB**，见 [docs/dvmt-insyde.md](docs/dvmt-insyde.md)。i915 移植驱动的显存从系统内存分配，不改也能用；苹果原版驱动（WhateverXe）则必须改。

## 目录

| 路径 | 内容 |
|---|---|
| `EFI/OC/config.plist` | **基础配置**：WhateverGreen + `-igfxvesa`，无核显加速，1920×1200。适合安装和救援 |
| `EFI/OC/config-igpu-accel.plist` | **日常配置**：zep245 驱动 + Metal 加速（需按 [docs/igpu-zep245.md](docs/igpu-zep245.md) 装好驱动） |
| `EFI/OC/config-whateverxe.plist` | **原生驱动配置（实验）**：WhateverXe + 苹果 Tiger Lake 驱动（见 [docs/igpu-whateverxe-native.md](docs/igpu-whateverxe-native.md)） |
| `EFI/COMPONENTS.md` | OpenCore 与各 kext 的版本和下载地址（二进制文件不在仓库里） |
| `acpi/` | SSDTTime 为本机生成的 SSDT + `patches_OC.plist` |
| `scripts/make_config.py` | 生成基础 `config.plist`（底板来自 [XPS 13 Plus 项目](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe)） |
| `scripts/make_nmx_config.py` | 由基础配置生成核显加速配置 |
| `scripts/make_wex_config.py` | 由基础配置生成原生驱动（WhateverXe）配置 |
| `patches/whateverxe-0.8.0/` | WhateverXe 0.8.0 补丁（eDP 链路保留、位深一致、背光周期）、预编译 kext、编译脚本 |
| `scripts/patch_kexts.py` | 给 VoodooI2C / VoodooGPIO 加 Tiger Lake 支持 |
| `scripts/deploy-redmi.sh`、`scripts/try-alcid.sh` | 通过网线远程部署 EFI、切换 AppleALC layout |
| `docs/igpu-zep245.md` | **核显加速教程**（中英双语） |
| `docs/dvmt-insyde.md`、`scripts/set-dvmt.sh`、`scripts/bios/` | **修改隐藏的 DVMT 显存**（60MB → 128MB），以及解包小米 BIOS、查找设置项位置的工具 |
| `docs/igpu-whateverxe-native.md` | **苹果原生核显驱动点亮记录与教程**（中英双语）：黑屏 → 链路保留 → 花屏（位深）→ 亮度（PWM 周期） |
| `docs/wifi-8021x.md`、`patches/itlwm/` | **企业级 Wi-Fi（802.1X）修复**：AirportItlwm 的 BSSID 时序 bug 及修复版驱动 |
| `docs/igpu-whateverxe.md` | WhateverXe 早期调查记录（60MB 冻结、128MB 黑屏） |
| `windows-tools/collect-hwinfo.ps1` | 在 Windows 下收集硬件信息 |

## 关键配置要点（踩过的坑）

1. **卡在 `EXITBS:START`**：Tiger Lake 必须打开 `Kernel → Quirks → AppleXcpmExtraMsrs`。CPU 伪装成 Ice Lake-U（`E5060700 00000000 00000000 00000000`，Mask `FFFFFFFF 00000000 00000000 00000000`），和机型 MacBookPro16,2 对应。
2. **开机约 1 秒内核崩溃**（`Fault CR2: 0xff654c0f`，调用栈里没有 kext，`No mapping exists for frame pointer`）：原因是固件运行时服务要访问 SPI Flash 的 MMIO（0xFF000000 段），而 `DevirtualiseMmio` 把这段映射去掉了。**关闭 `Booter → Quirks → DevirtualiseMmio`**，同时清空从 XPS 配置带来的 `MmioWhitelist`。
3. **触摸板**：VoodooI2C 2.9.1 没有 Tiger Lake I2C 控制器（`8086:A0E8–A0EB`）的匹配项；VoodooGPIO 的 TigerLakeLP 只认 `INTC1055`，而本机是 `INT34C5`。用 `scripts/patch_kexts.py` 补上这两项即可。如果某次开机触摸板消失（`TPD0._STA` 取决于 BIOS 写入的 `TPDT`），**完全关机后再开机**就能恢复。
4. **Wi-Fi**：装好系统后用 `AirportItlwm`（Tahoe 版 2.4.0）。要连 eduroam 等企业级 Wi-Fi，需换用带 802.1X 修复的构建（`2.4.0_4240f66`），见 [docs/wifi-8021x.md](docs/wifi-8021x.md)。
5. **声音**：Tahoe 删除了 AppleHDA，要用 **SimpleHDA** 注入（加载顺序 Lilu → AppleALC → SimpleHDA）。本机扬声器接在 **0x14** 引脚（69 / 99 这两个 layout 用的是 0x1B，所以没声音），选 **`alcid=38`**。
6. **核显加速**：见 [docs/igpu-zep245.md](docs/igpu-zep245.md)。最容易踩的坑：作者的安装工具**漏装 Mesa 的 Vulkan 驱动**，WindowServer 会报 `Failed to create MetalDevice` 然后反复崩溃；另外**必须开启 AMFIPass 并加上 AMFI 启动参数**。
7. **安装 U 盘**：`createinstallmedia` 必须在「终端」App 里运行，从其他进程以 root 身份运行也会被 TCC 拦截，写不进外置卷。
8. **双系统**：把 `EFI/OC` 放进 Windows 的 100MB ESP（不要动 `EFI/Boot` 和 `EFI/Microsoft`），然后在 Windows 里用 `bcdedit /copy {bootmgr} /d "OpenCore"` → `bcdedit /set {id} path \EFI\OC\OpenCore.efi` → `bcdedit /set {fwbootmgr} displayorder {id} /addfirst` 添加启动项。
9. **救援**：如果加速配置启动出问题，在 OpenCore 菜单里选中 Macintosh HD，按 **Shift + 回车**进入安全模式，或者把 EFI 换回基础 `config.plist`。

## 安装流程摘要

1. 在 Windows 下运行 `windows-tools/collect-hwinfo.ps1` 和 SSDTTime（依次选 P → FakeEC Laptop → USBX → PluginType → RTCAWAC → PNLF(_UID 19) → XOSI）。
2. BIOS 里关闭 Secure Boot。VT-d 关不掉，所以配置里开了 `DisableIoMapper`。
3. 在 Windows 里压缩出一块空间，新建一个 exFAT 分区；安装 macOS 时只把这个分区抹成 APFS。
4. 用 `softwareupdate --fetch-full-installer --full-installer-version 26.7.1` 下载安装器，再用 `createinstallmedia` 做 U 盘，把 `EFI/` 放进 U 盘的 ESP。
5. 安装 macOS → 把 `EFI/OC` 拷进内置硬盘的 ESP → 用 bcdedit 添加启动项。
6. 用基础配置确认声音、Wi-Fi、触摸板都正常后，再按 [docs/igpu-zep245.md](docs/igpu-zep245.md) 开启核显加速。

## 致谢

OpenCore / Lilu / WhateverGreen / AppleALC / VirtualSMC / VoodooPS2（acidanthera）、VoodooI2C、OpenIntelWireless、laobamac（AirportItlwm-Tahoe、SimpleHDA）、wfx1024（AirportItlwm 802.1X 修复）、**zep245 与 NullMoth Systems（Iris Xe i915 驱动）**、dhinakg（AMFIPass）、b00t0x（WhateverXe）、KenzoPortela / nickk19 / Aqpcet（eDP 链路保留补丁）、qqaoshi888（eDP 训练修复补丁）、watchthelight（XeGfx）、JulioNectar（XPS 13 Plus Tahoe 项目）、corpnewt（SSDTTime）、USBToolBox。

---

<a id="english"></a>

## English

A complete record of running **macOS Tahoe 26.7.1 (25G241)** with OpenCore on the **RedmiBook Pro 15 2021 (Intel, i5-11300H / Iris Xe 9A49)**, dual-booting with Windows. **Iris Xe Metal acceleration works** (3200x2000 @ 90 Hz), and **Apple's native iGPU driver now lights the panel too** (WhateverXe + patches, 2026-11-10).

> ⚠️ Use at your own risk. Serials (SystemSerialNumber / MLB / SystemUUID / ROM) are blanked in `config.plist`, `config-igpu-accel.plist` and `config-whateverxe.plist`. Generate your own with GenSMBIOS or `macserial -m MacBookPro16,2`.

### Hardware and status

| Part | Model | Status |
|---|---|---|
| CPU | i5-11300H (Tiger Lake-H35, model 0x8C) | ✅ spoofed as Ice Lake-U (`Cpuid1Data E5060700`) |
| iGPU | Iris Xe `8086:9A49` | ✅ **Apple's native driver** (experimental): WhateverXe 0.8.0 + patches from this repo, see [docs/igpu-whateverxe-native.md](docs/igpu-whateverxe-native.md)<br>✅ **Metal acceleration** (stable) with [zep245/IrisXe-macos-driver](https://github.com/zep245/IrisXe-macos-driver) (i915 port), see [docs/igpu-zep245.md](docs/igpu-zep245.md) |
| Panel | Tianma TL156MDMP01, 3200x2000, 90/60 Hz | ✅ native 3200x2000 @ 90 Hz when accelerated; 1920x1200 GOP otherwise |
| SSD | Intel 660p 1 TB | ✅ |
| Wi-Fi / BT | Intel AX201 / 8087:0026 | ✅ AirportItlwm / IntelBluetoothFirmware; enterprise Wi-Fi (802.1X, e.g. eduroam) needs the fixed build, see [docs/wifi-8021x.md](docs/wifi-8021x.md) |
| Audio | Realtek ALC256 (A0C8 controller in SST/DSP mode) | ✅ speakers / headphones via SimpleHDA + `alcid=38` |
| Internal mic | DMIC on the Intel SST DSP | ❌ |
| Touchpad | I2C HID `GXT7863` on I2C1 (A0E9), GPIO `INT34C5` | ✅ VoodooI2C (patched, see below) |
| Keyboard | PS/2 | ✅ VoodooPS2 |
| Camera | XiaoMi USB 2.0 Webcam (UVC) | ✅ |
| Fingerprint | Goodix 27c6:581a | ❌ |
| Sleep | — | ❌ not recommended |

BIOS: Insyde H2O `RMATG5B0P0D0D`. DVMT ships fixed at 60 MB (GMS 0xFE) and is hidden in setup, but it **can be set to 128 MB from macOS**: see [docs/dvmt-insyde.md](docs/dvmt-insyde.md). The i915 port allocates GPU memory from system RAM and works without it; Apple's driver (WhateverXe) needs it.

### Layout

| Path | Contents |
|---|---|
| `EFI/OC/config.plist` | **Base config**: WhateverGreen + `-igfxvesa`, no acceleration, 1920x1200. For installing and recovery |
| `EFI/OC/config-igpu-accel.plist` | **Daily config**: zep245 driver + Metal acceleration (install the driver first, see [docs/igpu-zep245.md](docs/igpu-zep245.md)) |
| `EFI/OC/config-whateverxe.plist` | **Native driver config (experimental)**: WhateverXe + Apple's Tiger Lake drivers (see [docs/igpu-whateverxe-native.md](docs/igpu-whateverxe-native.md)) |
| `EFI/COMPONENTS.md` | OpenCore / kext versions and download links (binaries are not in this repo) |
| `acpi/` | SSDTs generated by SSDTTime for this machine + `patches_OC.plist` |
| `scripts/make_config.py` | Builds the base `config.plist` (template from the [XPS 13 Plus project](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe)) |
| `scripts/make_nmx_config.py` | Derives the accelerated config from the base config |
| `scripts/patch_kexts.py` | Adds Tiger Lake support to VoodooI2C / VoodooGPIO |
| `scripts/deploy-redmi.sh`, `scripts/try-alcid.sh` | Remote EFI deploy and AppleALC layout testing over Ethernet |
| `docs/igpu-zep245.md` | **iGPU acceleration guide** (English / Chinese) |
| `docs/dvmt-insyde.md`, `scripts/set-dvmt.sh`, `scripts/bios/` | **Change the hidden DVMT setting** (60 MB → 128 MB), plus tools to unpack the Xiaomi BIOS and locate setup options |
| `docs/igpu-whateverxe-native.md` | **Native Apple iGPU driver: how it was lit up, and install guide** (English / Chinese): black screen → keep the link → garbled image (bpc) → brightness (PWM period) |
| `docs/wifi-8021x.md`, `patches/itlwm/` | **Enterprise Wi-Fi (802.1X) fix**: the AirportItlwm BSSID timing bug and the fixed driver build |
| `patches/whateverxe-0.8.0/`, `scripts/make_wex_config.py` | WhateverXe 0.8.0 patches, prebuilt kext, build script, config generator |
| `docs/igpu-whateverxe.md` | Earlier WhateverXe investigation (freeze at 60 MB, black screen at 128 MB) |
| `windows-tools/collect-hwinfo.ps1` | Hardware inventory from Windows |

### Key fixes

1. **Hang at `EXITBS:START`**: enable `Kernel → Quirks → AppleXcpmExtraMsrs` (needed on Tiger Lake). CPUID spoof to Ice Lake-U (`E5060700 00000000 00000000 00000000`, mask `FFFFFFFF 00000000 00000000 00000000`), which matches MacBookPro16,2.
2. **Kernel panic about 1 s after boot** (`Fault CR2: 0xff654c0f`, no kexts in the backtrace): firmware runtime services touch the SPI flash MMIO at 0xFF000000, and `DevirtualiseMmio` unmaps it. **Turn `Booter → Quirks → DevirtualiseMmio` off** and clear the `MmioWhitelist` that came with the XPS config.
3. **Touchpad**: VoodooI2C 2.9.1 has no personality for the Tiger Lake I2C controllers (`8086:A0E8–A0EB`), and VoodooGPIO's TigerLakeLP matches only `INTC1055`, while this firmware uses `INT34C5`. `scripts/patch_kexts.py` adds both. If the touchpad vanishes after many forced power-offs (`TPD0._STA` depends on the `TPDT` value the BIOS probes), do a full shutdown and power on again.
4. **Wi-Fi**: use `AirportItlwm` (Tahoe build 2.4.0) once macOS is installed. For WPA2-Enterprise / 802.1X networks (e.g. eduroam), use the build with the 802.1X fix (`2.4.0_4240f66`), see [docs/wifi-8021x.md](docs/wifi-8021x.md).
5. **Audio**: Tahoe removed AppleHDA; inject it with **SimpleHDA** (order Lilu → AppleALC → SimpleHDA). The speakers are on pin **0x14**; layouts 69 / 99 use 0x1B and stay silent. Use **`alcid=38`**.
6. **iGPU acceleration**: see [docs/igpu-zep245.md](docs/igpu-zep245.md). The main trap: the driver's installer **does not install the Mesa ANV Vulkan driver**, and WindowServer then aborts in a loop with `Failed to create MetalDevice`. **AMFIPass plus the AMFI boot-args** are also required.
7. **Installer USB**: run `createinstallmedia` from Terminal.app. Run from another process, even as root, TCC blocks writes to external volumes.
8. **Dual boot**: put `EFI/OC` into the 100 MB Windows ESP, leaving `EFI/Boot` and `EFI/Microsoft` alone. Then in Windows run `bcdedit /copy {bootmgr} /d "OpenCore"` → `bcdedit /set {id} path \EFI\OC\OpenCore.efi` → `bcdedit /set {fwbootmgr} displayorder {id} /addfirst`.
9. **Recovery**: if the accelerated config misbehaves, select Macintosh HD in OpenCore and press **Shift + Enter** for safe mode, or put the base `config.plist` back.

### Install summary

1. In Windows, run `windows-tools/collect-hwinfo.ps1` and SSDTTime (P → FakeEC Laptop → USBX → PluginType → RTCAWAC → PNLF (_UID 19) → XOSI).
2. BIOS: turn Secure Boot off. VT-d cannot be turned off, so the config sets `DisableIoMapper`.
3. Shrink the Windows partition and create an exFAT partition; during install, erase only that partition as APFS.
4. `softwareupdate --fetch-full-installer --full-installer-version 26.7.1`, then `createinstallmedia`, and put `EFI/` on the USB ESP.
5. Install macOS → copy `EFI/OC` to the internal ESP → add the bcdedit boot entry.
6. Check audio, Wi-Fi and touchpad on the base config, then enable acceleration with [docs/igpu-zep245.md](docs/igpu-zep245.md).

### Credits

OpenCore / Lilu / WhateverGreen / AppleALC / VirtualSMC / VoodooPS2 (acidanthera), VoodooI2C, OpenIntelWireless, laobamac (AirportItlwm-Tahoe, SimpleHDA), wfx1024 (AirportItlwm 802.1X fix), **zep245 and NullMoth Systems (Iris Xe i915 driver)**, dhinakg (AMFIPass), b00t0x (WhateverXe), KenzoPortela / nickk19 / Aqpcet (eDP keep patch), qqaoshi888 (eDP training fix), watchthelight (XeGfx), JulioNectar (XPS 13 Plus Tahoe project), corpnewt (SSDTTime), USBToolBox.
