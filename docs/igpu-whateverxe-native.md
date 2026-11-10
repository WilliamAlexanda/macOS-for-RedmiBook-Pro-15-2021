# 苹果原生核显驱动（WhateverXe）在 RedmiBook Pro 15 2021 上点亮 / Native Apple iGPU driver (WhateverXe) on the RedmiBook Pro 15 2021

[中文](#中文) · [English](#english)

---

## 中文

### 结果（2026-11-10）

RedmiBook Pro 15 2021（i5-11300H，Iris Xe `8086:9A49`，80 EU），macOS Tahoe 26.7.1 (25G241)，
使用**苹果自己的 Tiger Lake 驱动**（AppleIntelTGLGraphics / Framebuffer 16.0.0，由 WhateverXe Graphics 0.4.1 提供），
不经过 Vulkan 转译：

| 项目 | 状态 |
|---|---|
| 内屏 3200×2000，HiDPI 1600×1000 @ **90Hz** | ✅ 画面正常 |
| Metal | ✅ Metal 2，VRAM 1536 MB |
| 帧缓冲 | 30-bit (ARGB2101010)；链路为固件选择的 6 bpc + 抖动 |
| 亮度调节 | ✅ 全范围（修复后占空比最高 99.8%） |
| 睡眠 / 合盖 / 显示器睡眠 | ⚠️ 未测试（测试期间关闭了睡眠：`pmset -a sleep 0 displaysleep 0 disablesleep 1`） |
| HDMI | ⚠️ 未测试 |
| 视频播放 | ⚠️ 未测试。上游有 App Store / 屏保视频导致 GPU 挂起的报告（WhateverXe #75 #81） |

官方 WhateverXe 0.8.0 在这台机器上是**黑屏**的，需要下面三组补丁。

### 问题是怎么一步步解决的

**1. 官方 0.8.0：黑屏，根源是内屏链路重新训练失败。**
DVMT 已改为 128 MB（[dvmt-insyde.md](dvmt-insyde.md)），GPU 加速引擎能起来（Metal 2），系统也能认出内屏 3200×2000，
但屏幕全黑，WindowServer 每帧都报 `No plane indices`。内核日志才是关键：

```
FB0: Complete modeset
Phase 2 of link training failed - notifying AGDC to take display offline
FB0: Hardware mode set failed, err = 0xe00002bc
FB0 is not enabled   (×177)
```

苹果驱动接管时，会把 BIOS 已经练好的 eDP 链路停掉再重新训练，这块屏重新训练过不了（Phase 2 = 通道均衡失败）。
FB0 没有启用，WindowServer 自然找不到可用的显示平面。完整对比见 [logs/whateverxe-0.8.0-stock-vs-patched.txt](logs/whateverxe-0.8.0-stock-vs-patched.txt)。

**2. 社区已有的两个补丁（WhateverXe issue #37 / #43）。**
- `-wex-tgl-edp-keep`（@KenzoPortela 把 @nickk19 的 Alder Lake 方案移植到 Tiger Lake，并采用了 @Aqpcet 的放宽条件）：
  hook `AppleIntelFramebufferController::hwRegsNeedUpdate`。如果固件的 pipe A 已经在 DDI A 上以 eDP SST 输出同样的分辨率，
  就回答"不需要更新"。这样驱动只做 partial modeset（换 plane / scaler），**不停链路、不重新训练**。
  这台机器上的判定记录：固件链路与驱动想要的时序完全相同，只有位深不同（reasons = `0x800`），所以链路被保留。
- `-wex-edp-fix-training` + `-wex-ddi-conflict-select-*`（@qqaoshi888）：在每次内屏 LightUpEDP 之前做面板电源复位和 DDI/AUX 电源域修复。
  在这台机器上它装好了，但没有触发（没有 `TGLPanelCycle` 记录），因为 keep 让驱动不再走完整的点亮流程。
  保留它是为将来的睡眠唤醒准备，目前作用未经验证。

两者都能干净地打到 0.8.0 源码上。补丁用到的 10 个苹果驱动函数，地址和入口字节都在 Tahoe 版
`AppleIntelTGLGraphicsFramebuffer`（WhateverXe Graphics 0.4.1）上核对过，全部吻合。

**3. 屏幕亮了但花屏、错位：位深不一致（本仓库补丁 03 修复）。**
keep 生效后，屏幕第一次被原生驱动点亮，但画面是花的。读驱动的寄存器写入记录发现：

| 寄存器 | 固件（BIOS） | 苹果驱动写入 |
|---|---|---|
| `TRANS_DDI_FUNC_CTL_A` | `0x8A230006`：DDI A，DP SST，**6 bpc**，×4 通道 | 想要 `0x8A030006`（8 bpc），但链路被保留，实际不变 |
| `PIPE_MISC_A` (0x70030) | `0x01000050`：**6 bpc**，开抖动 | `0x01800010`：**8 bpc** |
| `TRANS_MSA_MISC_A` (0x60410) | — | `0x00000021`：告诉屏幕"8 bpc" |

固件把这块屏的链路练成 6 bpc。驱动只做 partial modeset，链路位深没变，pipe 却按 8 bpc 输出，结果像素格式和链路对不上。
修复方法：链路被保留时，把 `PIPE_MISC` 的 bpc 字段强制成链路的位深（6 bpc 时打开抖动），
同时把 `TRANS_MSA_MISC` 的位深也改成一致。只改 `PIPE_MISC` 时画面仍然是花的，两个都改之后画面正常。

**4. 最大亮度偏低：背光 PWM 周期不一致（本仓库补丁 03 修复）。**
日志里有 `EFI using a different backlight frequency`。硬件保留固件的 PWM 周期 `0xC8254 = 96000`，
而驱动按它自己的周期 17777 来计算占空比，所以滑块拉满时实际占空比只有 17741 / 96000 ≈ 18.5%。
修复方法：驱动写 `0xC8258`（占空比）时，按"硬件周期 ÷ 驱动周期"等比例放大。修复后拉满时为 95805 / 96000 = 99.8%。

### 安装步骤

> ⚠️ 实验性质。动手前备份 EFI，并准备好能启动的 U 盘。随时可以换回 zep245 配置（[igpu-zep245.md](igpu-zep245.md)）。

1. **DVMT 改成 128 MB**：见 [dvmt-insyde.md](dvmt-insyde.md)（`scripts/set-dvmt.sh`）。
2. 如果装过 zep245 驱动，把 `/Library/Extensions` 里的 `NMXGPU.kext`、`NMXAccel.kext`、`NVRMAGDC.kext` 移出去。
3. 安装 [WhateverXe Graphics 0.4.1](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.1)。安装器会自动选择 Tahoe 版本并重建 AuxKC。
4. 放进 `EFI/OC/Kexts`：
   - Lilu；
   - [AMFIPass 1.4.1 **Mod**](https://github.com/b00t0x/WhateverXe-Graphics/blob/main/extras/AMFIPass-v1.4.1-Mod-RELEASE.zip)，不要再同时加载原版 AMFIPass；
   - 打过补丁的 `WhateverXe.kext`：直接用 [`patches/whateverxe-0.8.0/WhateverXe-0.8.0-redmibook-RELEASE.zip`](../patches/whateverxe-0.8.0/)，
     或者运行 `patches/whateverxe-0.8.0/build.sh` 从源码编译（需要 Xcode 命令行工具）。
5. 生成配置：`python3 -I scripts/make_wex_config.py EFI/OC/config.plist EFI/OC/config-whateverxe.plist`，
   也可以直接用仓库里的 `EFI/OC/config-whateverxe.plist`。然后填入你自己的序列号。要点：
   - WhateverGreen 关闭；
   - `UEFI > Output > Resolution = Max`，必须让固件把内屏练在原生 3200×2000，keep 才能沿用这条链路；
   - boot-args 加上 `-allow3d -disablegfxfirmware -wex-tgl-edp-keep -wex-edp-fix-training`。
6. 重启。验证方法：
   - `system_profiler SPDisplaysDataType` 应显示 `Metal 2` 和 `3200 x 2000`；
   - `ioreg -l -w0 | grep -E '"TGLEDPKept"|"TGLBacklightRescale"'` 应显示 `TGLEDPKept` ≥ 1，并且有 `TGLBacklightRescale` 记录。

### 补丁文件（`patches/whateverxe-0.8.0/`）

基于 WhateverXe `0.8.0`（`db438fd`），按顺序叠加：

| 文件 | 来源 |
|---|---|
| `01-edp-fix-training-ddi-conflict.patch` | @qqaoshi888，WhateverXe #43（`fix_code(0.8.0).zip`） |
| `02-tgl-edp-keep-softsleep.patch` | @KenzoPortela，WhateverXe #37（`wex-tgl-edp-keep-softsleep-v2.patch`） |
| `03-redmibook-bpc-backlight.patch` | 本仓库：位深一致性 + 背光周期缩放 |
| `all-in-one.patch` | 以上三者合并 |

WhateverXe 采用 BSD-3-Clause 许可（见 `LICENSE-WhateverXe.txt`）。编译时使用 MacKernelSDK `05094e5` 和 Lilu 1.7.2，与上游 CI 相同。

---

## English

### Result (2026-11-10)

RedmiBook Pro 15 2021 (i5-11300H, Iris Xe `8086:9A49`, 80 EU), macOS Tahoe 26.7.1 (25G241), running **Apple's own Tiger Lake
drivers** (AppleIntelTGLGraphics / Framebuffer 16.0.0 from WhateverXe Graphics 0.4.1), with no Vulkan translation:

| Item | State |
|---|---|
| Internal panel 3200×2000, HiDPI 1600×1000 @ **90 Hz** | ✅ correct image |
| Metal | ✅ Metal 2, VRAM 1536 MB |
| Framebuffer | 30-bit (ARGB2101010); the link stays at the firmware's 6 bpc + dithering |
| Brightness | ✅ full range (duty up to 99.8% after the fix) |
| Sleep / lid / display sleep | ⚠️ not tested (sleep disabled during testing) |
| HDMI | ⚠️ not tested |
| Video playback | ⚠️ not tested; upstream reports GPU hangs from App Store / screensaver video (WhateverXe #75, #81) |

Stock WhateverXe 0.8.0 gives a **black screen** on this machine. It takes the three patch sets below.

### How it was solved

**1. Stock 0.8.0: black screen, caused by eDP link retraining failing.** With DVMT at 128 MB the accelerator starts (Metal 2)
and the panel is listed, but the screen is black and WindowServer logs `No plane indices` every frame. The kernel log shows
the cause:
`FB0: Complete modeset` → `Phase 2 of link training failed` → `Hardware mode set failed, err = 0xe00002bc` → `FB0 is not enabled` (×177).
Apple's framebuffer stops the eDP link the firmware already trained and retrains it, and this panel fails channel
equalization. See [logs/whateverxe-0.8.0-stock-vs-patched.txt](logs/whateverxe-0.8.0-stock-vs-patched.txt).

**2. Two existing community patches (WhateverXe #37, #43).**
- `-wex-tgl-edp-keep`: @KenzoPortela's Tiger Lake port of @nickk19's `-wex-edp-keep`, with @Aqpcet's relaxations. It hooks
  `hwRegsNeedUpdate` and answers "no update" when pipe A already drives the requested mode over a live eDP SST link on
  DDI A. The donor then does only a partial mode set and never retrains. Here the timings match exactly and only the depth
  differs (reasons `0x800`), so the link is kept.
- `-wex-edp-fix-training` + `-wex-ddi-conflict-select-*` (@qqaoshi888): panel power cycle and DDI/AUX power-domain repair
  before each internal LightUpEDP. It is installed here but never fired (no `TGLPanelCycle` record), because with keep the
  donor no longer runs a full light-up. It stays in for future wake work; its effect is unverified.

Both apply cleanly on 0.8.0. All 10 donor entry points they hook match by offset and prologue on the Tahoe
`AppleIntelTGLGraphicsFramebuffer` shipped in WhateverXe Graphics 0.4.1.

**3. Panel lit but garbled and shifted: depth mismatch on the kept link (patch 03).**

| Register | Firmware | Donor writes |
|---|---|---|
| `TRANS_DDI_FUNC_CTL_A` | `0x8A230006`: DDI A, DP SST, **6 bpc**, x4 | wants `0x8A030006` (8 bpc); the kept link is unchanged |
| `PIPE_MISC_A` (0x70030) | `0x01000050`: **6 bpc**, dithering on | `0x01800010`: **8 bpc** |
| `TRANS_MSA_MISC_A` (0x60410) | — | `0x00000021`: tells the sink 8 bpc |

The firmware trains this panel at 6 bpc. The partial mode set leaves the link depth alone but switches the pipe to 8 bpc,
so the pixel format no longer matches the link. Fix: while a link is kept, force the `PIPE_MISC` bpc field to the link's
depth (with dithering at 6 bpc), and set the `TRANS_MSA_MISC` depth to match. Fixing `PIPE_MISC` alone still left a
garbled image; fixing both gives a correct image.

**4. Maximum brightness too low: PWM period mismatch (patch 03).** The log says `EFI using a different backlight frequency`.
The hardware keeps the firmware period (`0xC8254 = 96000`), while the donor computes duty against its own period (17777).
Full brightness was 17741 / 96000 ≈ 18.5%. Fix: scale every `0xC8258` duty write by `hw period / donor period`.
Full brightness is now 95805 / 96000 = 99.8%.

### Install

> ⚠️ Experimental. Back up your EFI and keep a bootable USB stick. You can always go back to the zep245 config
> ([igpu-zep245.md](igpu-zep245.md)).

1. Set **DVMT to 128 MB**: see [dvmt-insyde.md](dvmt-insyde.md).
2. If the zep245 driver is installed, move `NMXGPU.kext`, `NMXAccel.kext` and `NVRMAGDC.kext` out of `/Library/Extensions`.
3. Install [WhateverXe Graphics 0.4.1](https://github.com/b00t0x/WhateverXe-Graphics/releases/tag/v0.4.1). It picks the Tahoe
   payload and rebuilds the AuxKC.
4. Put these in `EFI/OC/Kexts`:
   - Lilu;
   - [AMFIPass 1.4.1 **Mod**](https://github.com/b00t0x/WhateverXe-Graphics/blob/main/extras/AMFIPass-v1.4.1-Mod-RELEASE.zip), and not the
     upstream AMFIPass as well;
   - the patched `WhateverXe.kext`: [`patches/whateverxe-0.8.0/WhateverXe-0.8.0-redmibook-RELEASE.zip`](../patches/whateverxe-0.8.0/),
     or build it with `patches/whateverxe-0.8.0/build.sh`.
5. Use `EFI/OC/config-whateverxe.plist` (or regenerate it with `scripts/make_wex_config.py`) and add your own serials. Key points:
   - WhateverGreen off;
   - `UEFI > Output > Resolution = Max`, so the firmware trains the panel at native 3200×2000 and keep can reuse that link;
   - boot-args `-allow3d -disablegfxfirmware -wex-tgl-edp-keep -wex-edp-fix-training`.
6. Reboot and check:
   - `system_profiler SPDisplaysDataType` shows `Metal 2` and `3200 x 2000`;
   - `ioreg -l -w0 | grep -E '"TGLEDPKept"|"TGLBacklightRescale"'` shows `TGLEDPKept` ≥ 1 and a `TGLBacklightRescale` record.

### Patches (`patches/whateverxe-0.8.0/`)

On top of WhateverXe `0.8.0` (`db438fd`), in order:

| File | Source |
|---|---|
| `01-edp-fix-training-ddi-conflict.patch` | @qqaoshi888, WhateverXe #43 |
| `02-tgl-edp-keep-softsleep.patch` | @KenzoPortela, WhateverXe #37 (v2) |
| `03-redmibook-bpc-backlight.patch` | this repo: depth consistency + backlight period scaling |
| `all-in-one.patch` | all three combined |

WhateverXe is BSD-3-Clause (`LICENSE-WhateverXe.txt`). Built with MacKernelSDK `05094e5` and Lilu 1.7.2, as in upstream CI.
