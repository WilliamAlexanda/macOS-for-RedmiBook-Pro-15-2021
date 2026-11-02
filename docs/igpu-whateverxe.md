# Iris Xe acceleration with WhateverXe on RedmiBook Pro 15 2021 — investigation report

> **已被取代 / Superseded**：核显加速已改用 [zep245/IrisXe-macos-driver](https://github.com/zep245/IrisXe-macos-driver) 实现，见 [igpu-zep245.md](igpu-zep245.md)。The working route is now the zep245 driver; see [igpu-zep245.md](igpu-zep245.md).
>
> **中文摘要**：
> - **60MB 时**（WhateverXe 0.4.0）：只开显示（`-wex-noaccel`）能点亮 3200×2000 内屏，一旦启动 GPU 加速引擎整机就冻结。另一位同型号用户换成 WhateverXe 0.6.1、在 Sequoia 上测试，结果相同。
> - **2026-11-02 改成 128MB 后**（WhateverXe 0.6.1 + Graphics 0.3.2，改法见 [dvmt-insyde.md](dvmt-insyde.md)）：
>   - **冻结消失了**，证明之前就是显存不够；苹果原版加速引擎能正常启动，Metal 2 可用。
>   - 但**屏幕全黑**：WindowServer 每一帧都报 `No plane indices`，画面送不到屏幕上。90Hz 和 60Hz 都一样。
>   - 已经报告给 WhateverXe 作者。见下方 [Retest with DVMT 128 MB](#retest-with-dvmt-128-mb-2026-11-02)。

Written so it can be forwarded to the WhateverXe author as a bug report.

## Retest with DVMT 128 MB (2026-11-02)

DVMT Pre-Allocated was raised to 128 MB through the hidden BIOS setting ([dvmt-insyde.md](dvmt-insyde.md)). The i915 driver confirms it: `Got Intel graphics stolen memory base 0x47800000, size 0x8000000`.

Setup:
- WhateverXe 0.6.1, RELEASE and DEBUG builds;
- WhateverXe-Graphics 0.3.2;
- AMFIPass 1.4.1 **Mod**, and `csr-active-config 130A0000`, which includes 0x803;
- boot-args `-allow3d -disablegfxfirmware`;
- no iGPU DeviceProperties, so automatic selection is used, and no `-igfxdvmt` / `framebuffer-stolenmem`;
- WhateverGreen disabled, and the zep245 NMX kexts removed from the AuxKC.

| # | Change | Result |
|---|---|---|
| 8 | `-wex-noaccel` | Boots. `AppleIntelFramebuffer@0` active, 3200×2000 @ 631.8 MHz (90 Hz). Screen black (expected without accelerator) |
| 9 | Accelerator enabled | **No freeze.** `IntelAccelerator` starts with MetalPluginName `AppleIntelTGLGraphicsMTLDriver`, `TGL GT2 LP`, 80 EU, host scheduler. System Information shows Metal 2. **Screen stays completely black (backlight off), and the brightness keys do nothing** |
| 10 | + EDID override (`AAPL00,override-no-connect`) with only the 60 Hz DTD | Mode set at 419.33 MHz (60 Hz), same black screen |
| 11 | DEBUG WEX + DEBUG Lilu, `-wexdbg -liludbg -wex-display-trace IGLogLevel=4` | Every WEX stage reports success (framebuffer start returned 1, accel stages 1–6 result 1). Same black screen |

What WindowServer does:
- It finds the panel: `Display 0x6e055800 ... isBuiltIn=YES`, mode 3200×2000. It creates its framebuffers and logs `Metal compositor activated`.
- From then on, every frame logs `[ERROR] - Attempting to get capabilities when none exist` and `[WARN] - No plane indices`, about 90 times per second, which matches the refresh rate.
- `screencapture` fails with `could not create image from display`, and `system_profiler` lists no display.
- `IOAccelDisplayPipeCapabilities = {DisplayPipeSupported=Yes, TransactionsSupported=Yes}` is published on both the accelerator and the framebuffer.
- `TGLBacklightPWM` reports PWM enabled at a duty of about 5% (0x128A / 0x17700), yet the panel shows no backlight at all.

So with enough DVMT, the kernel side comes up completely. The remaining failure is CoreDisplay's display-pipe commit path finding no planes for this eDP panel. The panel is far above the 1366×768 eDP that WEX lists as tested.

Logs (filtered, no identifiers):
- [whateverxe-0.6.1-dvmt128-debug-kernel.txt](logs/whateverxe-0.6.1-dvmt128-debug-kernel.txt)
- [whateverxe-0.6.1-dvmt128-windowserver.txt](logs/whateverxe-0.6.1-dvmt128-windowserver.txt)

The machine is back on the zep245 i915 driver for daily use.

## System

| Item | Value |
|---|---|
| Laptop | RedmiBook Pro 15 2021 (TIMI), Insyde H2O BIOS `RMATG5B0P0D0D` |
| CPU | i5-11300H, Tiger Lake-H35, CPUID model 0x8C. OpenCore spoof `Cpuid1Data E5060700` (Ice Lake-U) |
| GPU | `8086:9A49` rev 01, subsystem `1D72:2017` |
| DVMT | GMS `0xFE` = 60 MB, fixed and hidden in BIOS |
| Panel | eDP, Tianma TL156MDMP01 (EDID mfg `TMX`, product 0x1560), 3200×2000, DTD0 90 Hz @ 631.80 MHz, DTD1 60 Hz @ 419.33 MHz, 8 bpc |
| macOS | Tahoe 26.7.1 (25G241) |
| OpenCore | 1.0.8, SMBIOS MacBookPro16,2, csr-active-config `03080000` |
| Kexts | Lilu 1.7.3 (1.7.2 DEBUG for diagnostics), AMFIPass 1.4.1 Mod, WhateverXe 0.4.0 DEBUG, WhateverXe-Graphics 0.1.0 pkg; WhateverGreen disabled |
| boot-args | `-allow3d -disablegfxfirmware -wexdbg -igfxdvmt` (+ tests below) |
| iGPU properties | `framebuffer-patch-enable = 01000000`, `framebuffer-stolenmem = 0000C003` |

## Results

| # | Change | Result |
|---|---|---|
| 1 | Graphics pkg installed, **no** DVMT properties | Hard freeze when the framebuffer takes over (no ping, no logs persisted) |
| 2 | + `framebuffer-patch-enable` / `framebuffer-stolenmem` (log: `getOSData framebuffer-stolenmem has 3C00000 value`, `TGLStolenMemoryApplied = 62914560`) | Hard freeze |
| 3 | + `-wex-noaccel` | **Boots and stays up.** Framebuffer starts (`TGLFramebufferStartResult = Yes`), `AppleIntelFramebuffer@0` active, `IOFBCurrentPixelCount = 7020000`, `WhateverXeDPCDCount = 260`, EDID read. Screen is black (no accelerator, so WindowServer cannot draw) |
| 4 | Accelerator enabled again, no Lilu debug spam | Hard freeze ~30 s after boot, right after kernelmanagerd approves the AuxKC (`Validate approval for AppleIntelTGLCompat.kext in auxKC: approved`); last persisted log line at that moment |
| 5 | + `-wex-no-host-rps` + `IGLogLevel=3` | Hard freeze, no Apple driver log lines reach the console |
| 6 | SimpleHDA disabled | Hard freeze (SimpleHDA was only printing at that moment) |
| 7 | OpenCore GOP resolution 1024×768 instead of 3200×2000 | Hard freeze. Last console lines: `AppleIntelTGLCompat: revision 0.5.0 started`, `DVMT: Calculation patch readback=1`, `TGL framebuffer start route=1`, `AGDCBacklightControl: Didn't find DPMicro` |

"Hard freeze" means no response to ping and no persisted unified log or panic report. A Shift + Enter safe boot from OpenCore (which skips the AuxKC) always recovers.

## Ruled out

- **CPU spoof**: `AppleIntelTGLGraphics` / `AppleIntelTGLGraphicsFramebuffer` do not import `cpuid_info`, and WhateverXe has no CPU-model checks. NootedGreen-style `isRealTGL` checks would read raw CPUID anyway.
- **Panel / eDP link**: the display-only boot (#3) trains the link and keeps running.
- **Boot framebuffer occupying stolen memory**: #7.
- **Host RPS**: #5.

## Observations

- The Apple platform entry for `9A490000` ("Intel HD Graphics TGL CRB") sets the display pool to `0x4000000` (64 MB) and the framebuffer memory to `0x60000000`. On this machine WEX caps the pool at 60 MB.
- The freeze only happens when the TGL accelerator starts. The only untested variable is DVMT ≥ 96 MB, which the README recommends. This BIOS does not expose that setting.
- Files: `docs/logs/whateverxe-lilu-debug-noaccel-boot.txt` (Lilu DEBUG dump from a boot without the graphics pkg: `DVMT: GMS value is 0xfe; DVMT pre-allocated memory is 60 MB.`).

## Next steps

1. ~~Find the DVMT variable offset and set 96/128 MB, then retest #4.~~ Done, see [Retest with DVMT 128 MB](#retest-with-dvmt-128-mb-2026-11-02): the freeze is gone, and the screen is black with `No plane indices`.
2. Reported to WhateverXe. Waiting for a fix for the display-plane / backlight path on this panel.
