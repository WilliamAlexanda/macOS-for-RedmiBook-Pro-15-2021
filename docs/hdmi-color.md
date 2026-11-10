# HDMI 外接屏颜色错乱的修复 / Fixing broken colours on HDMI

[中文](#中文) · [English](#english)

---

## 中文

### 现象

使用苹果原生核显驱动（WhateverXe 0.8.0 + 本仓库补丁，见 [igpu-whateverxe-native.md](igpu-whateverxe-native.md)）时，
HDMI 外接屏能点亮、分辨率和刷新率都对（例：一台 PM1561P 便携屏，1920×1200 @ 60Hz），
但**颜色完全错乱**：渐变变成一圈圈色带，颜色像被"反转"或"取模"了一样，并带有很重的抖动花纹。内屏正常。

### 原因

这台显示器的 EDID 在 CTA-861 扩展块里声明了：

- HDMI VSDB（`67 03 0c 00 …`）第 6 字节 = `0x18`：**DC_30bit**（支持 10 bpc 深色）+ **DC_Y444**；
- CTA 头第 3 字节 = `0xf2`：支持 **YCbCr 4:4:4 / 4:2:2**。

macOS 看到这些声明后给它开了 30-bit 帧缓冲并按深色模式输出，
但 Tiger Lake 帧缓冲驱动的 HDMI 路径并没有把 TMDS 时钟提高到深色模式需要的 1.25 倍：
`IOFBCurrentPixelClock` = 154.13 MHz，正好是 1920×1200@60（CVT-RB）**8 bpc** 的像素时钟。
两边位深对不上，像素数据的位错开，就出现了照片里的色带和乱色（性质和内屏当初的 6/8 bpc 花屏一样）。
苹果的 Tiger Lake Mac 本身没有原生 HDMI 口，这条路径大概率从来没被测过。

### 修复：EDID 覆盖，只去掉深色和 YCbCr 声明

不改 EFI、不改驱动，只在 macOS 里给显示器加一个**显示器覆盖文件**
（`/Library/Displays/Contents/Resources/Overrides/DisplayVendorID-xxxx/DisplayProductID-yyyy`），
里面放一份修改过的 EDID：

| 位置 | 原值 | 改为 | 含义 |
|---|---|---|---|
| CTA 扩展第 3 字节 | `0xf2` | `0xc2` | 去掉 YCbCr 4:4:4 / 4:2:2 支持 |
| HDMI VSDB 第 6 字节 | `0x18` | `0x00` | 去掉 DC_48/36/30bit 和 DC_Y444 |
| HF-VSDB（如有）第 7 字节 | — | 低 3 位清零 | 去掉 4:2:0 深色 |
| 扩展块校验和 | — | 重新计算 | |

macOS 就只会走普通的 **8 bpc RGB**。分辨率、刷新率、HDR 静态元数据、音频等其它信息都保持不变。
拔插一次 HDMI 后颜色恢复正常（已验证）。

### 自动应用到所有外接屏

覆盖文件按厂商 ID / 产品 ID 匹配，只对一台显示器有效。
[`scripts/edid-fix/`](../scripts/edid-fix/) 里的小服务会对**每一台接入的外接屏**自动生成上面这样的覆盖文件：

- `edid-standard-rgb.pl`：读 `ioreg` 里每个 `AppleDisplay`（只有外接屏；内屏是 `AppleBacklightDisplay`，不处理）的 EDID，
  按上表改写，写入覆盖目录。不会改动不是它生成的覆盖文件（用 `EDIDStandardRGBAuto` 标记识别），已是最新时不重复写。
  加 `--dry-run` 只打印不写入。
- `com.redmibook.edid-standard-rgb.plist`：LaunchDaemon，每 10 秒运行一次，日志在 `/var/log/edid-standard-rgb.log`。
- `install-edid-fix.sh`：安装 / 卸载。

```bash
cd scripts/edid-fix
sudo bash install-edid-fix.sh              # 安装
sudo bash install-edid-fix.sh --uninstall  # 卸载，并删除它生成的覆盖文件
```

只依赖系统自带的 `/usr/bin/perl`，不需要装 Xcode 命令行工具。

**注意**：一台新显示器第一次接上时颜色可能还是错的（macOS 只在显示器接入时读取覆盖文件）。
等约 10 秒让服务生成覆盖文件，再拔插一次即可，之后这台显示器每次都正常。

### 回退

运行卸载命令，或直接删除对应的 `DisplayVendorID-xxxx/DisplayProductID-yyyy` 文件，然后拔插显示器。

---

## English

### Symptom

With Apple's native iGPU driver (WhateverXe 0.8.0 + this repo's patches, see
[igpu-whateverxe-native.md](igpu-whateverxe-native.md)) an HDMI monitor lights up at the right mode
(e.g. a PM1561P portable monitor, 1920×1200 @ 60 Hz), but the **colours are wrecked**: gradients turn into
contour bands with wrapped, false colours and heavy dither patterns. The internal panel is fine.

### Cause

The monitor's EDID CTA-861 extension advertises:

- HDMI VSDB (`67 03 0c 00 …`) byte 6 = `0x18`: **DC_30bit** (10 bpc deep colour) + **DC_Y444**;
- CTA header byte 3 = `0xf2`: **YCbCr 4:4:4 / 4:2:2** support.

macOS gives it a 30-bit framebuffer and drives deep colour, but the Tiger Lake framebuffer's HDMI path does not
raise the TMDS clock by the 1.25× deep colour needs: `IOFBCurrentPixelClock` = 154.13 MHz, which is exactly
the **8 bpc** pixel clock for 1920×1200@60 (CVT-RB). The bit depths on the two sides disagree, the pixel bits
end up misaligned, and you get the banding and false colours (the same class of bug as the internal panel's
6/8 bpc garbling). Apple's Tiger Lake Macs have no native HDMI port, so this path was probably never exercised.

### Fix: an EDID override that drops only deep colour and YCbCr

Nothing in the EFI or the driver changes. A macOS **display override**
(`/Library/Displays/Contents/Resources/Overrides/DisplayVendorID-xxxx/DisplayProductID-yyyy`)
supplies a patched EDID:

| Where | Was | Now | Meaning |
|---|---|---|---|
| CTA extension byte 3 | `0xf2` | `0xc2` | no YCbCr 4:4:4 / 4:2:2 |
| HDMI VSDB byte 6 | `0x18` | `0x00` | no DC_48/36/30bit, no DC_Y444 |
| HF-VSDB byte 7 (if present) | — | low 3 bits cleared | no 4:2:0 deep colour |
| Extension checksum | — | recomputed | |

macOS then drives plain **8 bpc RGB**. Modes, refresh rates, HDR static metadata, audio etc. are untouched.
After one HDMI replug the colours are correct (verified).

### Applying it to every external monitor automatically

An override matches one vendor/product ID only. The small service in
[`scripts/edid-fix/`](../scripts/edid-fix/) generates such an override for **every external display** you connect:

- `edid-standard-rgb.pl` reads the EDID of each `AppleDisplay` from `ioreg` (externals only; the internal panel is
  `AppleBacklightDisplay` and is skipped), patches it as above and writes the override. It never touches overrides
  it did not create (recognised by an `EDIDStandardRGBAuto` key) and does not rewrite files that are already
  current. `--dry-run` prints without writing.
- `com.redmibook.edid-standard-rgb.plist`: a LaunchDaemon that runs it every 10 s, logging to
  `/var/log/edid-standard-rgb.log`.
- `install-edid-fix.sh`: install / uninstall.

```bash
cd scripts/edid-fix
sudo bash install-edid-fix.sh              # install
sudo bash install-edid-fix.sh --uninstall  # remove, including the overrides it generated
```

It needs only the system `/usr/bin/perl`, not the Xcode command line tools.

**Note**: the first time a new monitor is connected its colours may still be wrong, because macOS reads
overrides only when a display attaches. Wait ~10 s for the service to write the override, replug once,
and that monitor is correct from then on.

### Reverting

Run the uninstall command, or delete the matching `DisplayVendorID-xxxx/DisplayProductID-yyyy` file, then replug.
