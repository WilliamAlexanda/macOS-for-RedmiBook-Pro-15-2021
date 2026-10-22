# Iris Xe acceleration with WhateverXe on RedmiBook Pro 15 2021 — investigation report

Written so it can be forwarded to the WhateverXe author as a bug report.

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

1. Find the DVMT variable offset in the Insyde Setup IFR (dump the BIOS → UEFITool → IFRExtractor), set it to 96/128 MB with `setup_var`, then retest #4.
2. Report to WhateverXe with this file.
