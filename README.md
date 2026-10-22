# macOS Tahoe on RedmiBook Pro 15 2021 (Intel i5-11300H)

在 **RedmiBook Pro 15 2021（Intel 版，i5-11300H / Iris Xe 9A49）** 上用 OpenCore 安装 **macOS Tahoe 26.7.1 (25G241)** 的完整记录，与 Windows 双系统共存。

> ⚠️ 黑苹果有风险。本仓库的 `config.plist` 已清空序列号（SystemSerialNumber / MLB / SystemUUID / ROM），使用前请用 GenSMBIOS 或 `macserial -m MacBookPro16,2` 生成你自己的一套。

## 硬件

| 部件 | 型号 | 状态 |
|---|---|---|
| CPU | i5-11300H（Tiger Lake-H35，model 0x8C） | ✅ 伪装成 Ice Lake-U（`Cpuid1Data E5060700`） |
| 核显 | Iris Xe `8086:9A49` | ⚠️ **无加速**（`-igfxvesa`，见下文「核显」） |
| 屏幕 | 天马 TL156MDMP01，3200×2000，90/60Hz | ✅ 以 1920×1200 GOP 模式运行 |
| 硬盘 | Intel 660p 1TB（SSDPEKNW010T8） | ✅ |
| 网卡 | Intel AX201 | ✅ AirportItlwm（原生 Wi-Fi 菜单） |
| 蓝牙 | Intel 8087:0026 | ✅ IntelBluetoothFirmware |
| 声卡 | Realtek ALC256（控制器 A0C8 处于 SST/DSP 模式） | ✅ 扬声器 / 耳机：SimpleHDA + `alcid=38` |
| 内置麦克风 | DMIC 接在 Intel 智音技术 DSP 上 | ❌ |
| 触摸板 | I2C HID `GXT7863`，I2C1 (A0E9)，GPIO `INT34C5` | ✅ VoodooI2C（需补丁，见下文） |
| 键盘 | PS/2 | ✅ VoodooPS2 |
| 摄像头 | XiaoMi USB 2.0 Webcam（UVC） | ✅ 免驱 |
| 指纹 | Goodix 27c6:581a | ❌ |
| 睡眠 | — | ❌ 不建议使用 |

BIOS：Insyde H2O，版本 `RMATG5B0P0D0D`，DVMT 固定 60MB（GMS 0xFE），BIOS 中不可见。

## 目录

| 路径 | 内容 |
|---|---|
| `EFI/` | `config.plist` + 本机 SSDT；OpenCore 与各 kext 需按 [EFI/COMPONENTS.md](EFI/COMPONENTS.md) 自行下载 |
| `acpi/` | SSDTTime 为本机生成的 SSDT 源码 + `patches_OC.plist` |
| `scripts/make_config.py` | 生成 `config.plist` 的脚本（以 [XPS 13 Plus 项目](https://github.com/JulioNectar/Hackintosh-XPS13Plus-IrisXe-Tahoe) 的 `config-install.plist` 为底板） |
| `scripts/patch_kexts.py` | 给 VoodooI2C / VoodooGPIO 加 Tiger Lake 支持 |
| `scripts/deploy-redmi.sh` | 通过网线把 EFI 部署到红米内置 ESP（带备份与 md5 校验） |
| `scripts/try-alcid.sh` | 远程切换 AppleALC layout 并重启测试 |
| `docs/igpu-whateverxe.md` | 核显加速（WhateverXe）调查报告 |
| `windows-tools/collect-hwinfo.ps1` | 在 Windows 下收集硬件信息 |
| `tools/` | WhateverXe Graphics 卸载脚本（双击版） |

### 需要自己补的文件
- OpenCore 与全部 kext 的版本、下载地址见 [EFI/COMPONENTS.md](EFI/COMPONENTS.md)。VoodooI2C 需要打补丁（改好的 Info.plist 在 `EFI/OC/Kexts-patched/`）。
- 序列号：见顶部提示。

## 关键配置要点（踩过的坑）

1. **卡在 `EXITBS:START`**：Tiger Lake 必须打开 `Kernel → Quirks → AppleXcpmExtraMsrs`。CPU 伪装用 Ice Lake-U `E5060700 00000000 00000000 00000000` / Mask `FFFFFFFF 00000000 00000000 00000000`，与机型 MacBookPro16,2（Ice Lake）一致。
2. **开机约 1 秒内核崩溃，`Fault CR2: 0xff654c0f`，调用栈无 kext、`No mapping exists for frame pointer`**：是固件运行时服务访问 SPI Flash 的 MMIO（0xFF000000 段）被 `DevirtualiseMmio` 去映射了。**关闭 `Booter → Quirks → DevirtualiseMmio`**（并清空从 XPS 带来的 `MmioWhitelist`）。
3. **触摸板**：VoodooI2C 2.9.1（含官方版）没有 Tiger Lake I2C 控制器（`8086:A0E8–A0EB`）的 personality，VoodooGPIO 的 TigerLakeLP 只匹配 `INTC1055` 而本机是 `INT34C5`（Linux 两者共用 TGL-LP 引脚表）。`scripts/patch_kexts.py` 只改 Info.plist 补上这两项。安装阶段保留 `-vi2c-force-polling`。
   - 若某次开机触摸板消失：DSDT 中 `TPD0._STA` 取决于 BIOS 开机探测写入的 `TPDT`（1=ELAN，2=GXT）。多次强制断电后可能探测失败，**完全关机再开机**即可恢复。
4. **Wi-Fi**：装好系统后用 `AirportItlwm`（XPS 项目里的 Tahoe 版 2.4.0），不用 `itlwm`。
5. **声音**：Tahoe 删除了 AppleHDA，AppleALC 单独无效 → 用 **SimpleHDA** 注入（顺序 Lilu → AppleALC → SimpleHDA，MinKernel 25.0.0）。控制器虽处于 SST/DSP 模式（class 0x0401），AppleHDAController 仍能挂上。
   - **layout**：69 / 99（小米 Pro）把扬声器放在 0x1B，没有声音。用 `alc-verb` 实测本机扬声器在 **0x14**（只连 DAC 0x02），耳机 0x21 → **`alcid=38`**（三星 Galaxy Book TGL）。
6. **显示**：无加速时只有 GOP 模式可用，没有 HiDPI。本机 GOP 只提供 `3200×2000 / 1920×1200 / 1920×1440 / 1600×1200 / 1280×1024 / 1024×768 / 800×600 / 640×480`（OpenCore DEBUG 日志读出），16:10 里最低就是 **1920×1200**（`UEFI → Output → Resolution`）。无加速时 Tahoe 桌面壁纸显示为白色。
7. **安装 U 盘**：`createinstallmedia` 必须在「终端」App 里运行（从其他进程以 root 运行会被 TCC 拦截写外置卷）。
8. **双系统**：OpenCore 放进 Windows 的 100MB ESP（`EFI/OC`，不动 `EFI/Boot` 与 `EFI/Microsoft`），在 Windows 里用 `bcdedit /copy {bootmgr} /d "OpenCore"` → `bcdedit /set {id} path \EFI\OC\OpenCore.efi` → `bcdedit /set {fwbootmgr} displayorder {id} /addfirst` 加启动项。

## 核显

详见 [docs/igpu-whateverxe.md](docs/igpu-whateverxe.md)。结论：用 [WhateverXe 0.4.0](https://github.com/b00t0x/WhateverXe) + WhateverXe-Graphics 0.1.0，**仅显示（`-wex-noaccel`）能点亮 3200×2000 内屏，一旦启动 GPU 加速引擎整机冻结**；排除了显存参数、CPU 伪装、SimpleHDA、频率控制、GOP 分辨率等因素。待尝试：BIOS 隐藏项把 DVMT 调到 96/128MB，或等待作者更新。

## 安装流程摘要

1. Windows 下运行 `windows-tools/collect-hwinfo.ps1` 与 SSDTTime（P → FakeEC Laptop → USBX → PluginType → RTCAWAC → PNLF(_UID 19) → XOSI），生成 `acpi/` 下文件。
2. BIOS：关闭 Secure Boot。VT-d 无法关闭，配置里开了 `DisableIoMapper`。
3. 在 Windows 磁盘管理里压缩出空间，建一个 exFAT 分区（安装时在磁盘工具里只抹这个分区为 APFS）。
4. `softwareupdate --fetch-full-installer --full-installer-version 26.7.1`（或直接下 InstallAssistant.pkg），`createinstallmedia`，把 `EFI/` 放进 U 盘 ESP。
5. 安装 → 把 `EFI/OC` 拷进内置 ESP → bcdedit 添加启动项。
6. 安装后 `config.plist` 已是日常配置（AirportItlwm、SimpleHDA、alcid=38、1920×1200）。

## 致谢

OpenCore / Lilu / WhateverGreen / AppleALC / VirtualSMC / VoodooPS2（acidanthera）、VoodooI2C、OpenIntelWireless（itlwm / IntelBluetoothFirmware）、laobamac（AirportItlwm-Tahoe、SimpleHDA）、b00t0x（WhateverXe）、JulioNectar（XPS 13 Plus Tahoe 项目，提供配置底板）、corpnewt（SSDTTime）、USBToolBox。
