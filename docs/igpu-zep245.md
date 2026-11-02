# Iris Xe Metal acceleration on RedmiBook Pro 15 2021 (Tahoe 26.7.1)

**中文** | [English](#english)

用 [zep245/IrisXe-macos-driver](https://github.com/zep245/IrisXe-macos-driver) 给 i5-11300H 的 Iris Xe（`8086:9A49`）开启 Metal 加速。这是基于 NullMoth 的 Linux i915 移植驱动，加上 Mesa ANV（Vulkan）和一个 Metal→Vulkan 插件。2026-11-02 在本机实测成功。

| 结果 | |
|---|---|
| 系统信息 | Intel Iris Xe Graphics，Metal：支持，VRAM（动态）1536 MB |
| 屏幕 | **3200×2000 @ 90.00Hz**（原生分辨率与刷新率） |
| 加速桌面 | 已开启（`debug.nvaccelfb = 1`；1 分钟内显示提交成功 2202 次、失败 0 次） |
| 60MB DVMT | 不受影响：屏幕缓冲区从系统内存分配 |

> ⚠️ 这是实验性的内核驱动。需要关闭部分 SIP、`SecureBootModel Disabled`，还要用 AMFI 参数放宽代码签名检查，系统安全性会降低。**动手前先备份 EFI**，并确认会用 Shift + 回车进安全模式。

## 1. 需要的文件

| 来源 | 文件 | 用途 |
|---|---|---|
| zep245 Release **v1.0.3** | `nmxgpu-macos-15.zip` | NMXGPU.kext、`tahoe/NMXAccel.kext`、NVRMAGDC.kext、Metal 插件（安静版）、着色器翻译器、自动加速辅助程序、`IrisXe Manager.app` |
| zep245 Release **v1.0.0** | `nmx-vulkan-macos-15-intel.zip` | **完整 Metal 插件**（带 `air-runtime/`）+ **Mesa ANV Vulkan 驱动**（`out/nmx-metal/nvmtl/`）。后续版本的发布页只链接到需要登录的 Actions 产物，所以要从这里拿 |
| dortania OCLP | `AMFIPass-v1.4.1-RELEASE.zip`（SHA-256 `07b26614…dc961e`） | 放进 `EFI/OC/Kexts`，让 WindowServer 能加载未签名的 Metal 插件 |

GPU 固件（`tgl_dmc_ver2_12`、`tgl_guc_70.1.1`、`tgl_huc_7.9.3`）已经编进 NMXGPU.kext，不需要另外下载。

## 2. 安装驱动（在红米的 macOS 上）

```sh
# 解压两个包，比如放到 ~/nmx/nmxgpu-macos-15 和 ~/nmx/mesa
M="$HOME/nmx/nmxgpu-macos-15/out/IrisXe Manager.app/Contents/Resources/irisxe-manager.sh"
sudo bash "$M" install "$HOME/nmx/nmxgpu-macos-15" gpu accel agdc "fullplugin@$HOME/nmx/mesa" plugin xlate autoarm
```

### ⚠️ 2.1 补装 Vulkan 驱动（安装工具漏装的部分）

`fullplugin` 只拷贝了 `NVMTLDriver.bundle`，**没有拷贝同一个包里的 ANV Vulkan 驱动**。不补装的话，WindowServer 会反复崩溃（见第 6 节）。已报告给作者：[zep245/IrisXe-macos-driver#3](https://github.com/zep245/IrisXe-macos-driver/issues/3)。

```sh
S=$HOME/nmx/mesa/out/nmx-metal/nvmtl; G=/Library/GPUBundles/nvmtl
for f in libvulkan_intel.dylib libvulkan.1.dylib libvulkan.dylib libdrm.2.dylib libSPIRV-Tools.dylib intel_icd.json; do
  sudo cp "$S/$f" "$G/$f.new" && sudo mv -f "$G/$f.new" "$G/$f"; done
sudo chown -R root:wheel $G; sudo chmod -R go-w,a+rX $G
```
（不要覆盖 `libnvmtl_translate.dylib`，那个是 v1.0.3 的新版本。）

### 2.2 驱动未获批准时

如果安装工具提示 `not approved to load`，就手动把三个驱动编进 AuxKC：
```sh
sudo kmutil create -n aux --volume-root / --allow-missing-kdk --kernel /System/Library/Kernels/kernel \
  -B /System/Library/KernelCollections/BootKernelExtensions.kc -S /System/Library/KernelCollections/SystemKernelExtensions.kc \
  --repository /Library/Extensions -A /Library/KernelCollections/AuxiliaryKernelExtensions.kc.new -z
sudo kmutil inspect -a x86_64 -A /Library/KernelCollections/AuxiliaryKernelExtensions.kc.new | grep nullmoth   # 应该能看到 3 个
sudo mv -f /Library/KernelCollections/AuxiliaryKernelExtensions.kc.new /Library/KernelCollections/AuxiliaryKernelExtensions.kc
```
（先备份旧的 `AuxiliaryKernelExtensions.kc`。本机的 SIP 是 `0x0A13`。）

## 3. OpenCore 改动

可以直接用 [`EFI/OC/config-igpu-accel.plist`](../EFI/OC/config-igpu-accel.plist)（记得填上你自己的序列号），也可以运行 `python3 -I scripts/make_nmx_config.py B EFI/OC/config.plist out.plist`，从基础配置生成。改动如下：

| 位置 | 改动 |
|---|---|
| Kernel → Add | **关闭 WhateverGreen**；**在 Lilu 后面开启 AMFIPass.kext** |
| Kernel → Block | `com.apple.iokit.IONDRVSupport`，Strategy `Exclude`（让驱动的帧缓冲成为 0 号显示器） |
| DeviceProperties → `PciRoot(0x0)/Pci(0x2,0x0)` | `AAPL,ig-platform-id` = `0000499A`，`device-id` = `499A0000`，`AAPL,slot-name` = `built-in` |
| UEFI → Output → Resolution | `Max`（原生 3200×2000，交给 i915 接管） |
| boot-args（追加） | `nmxintel=1 nmxaccel=1 -nmintelfboff nmxcopyfwd=1 nmxmodern=1 nmxintelfb=1 -nmxnosnap amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0 nmxws=1 nmxautoarm=1`（同时去掉 `-igfxvesa`） |

建议**分两步测试**：先不加 `nmxws=1 nmxautoarm=1`（阶段 A：只让 i915 接管屏幕），确认屏幕正常，再加上它们（阶段 B：开启加速桌面）。

## 4. 开机后的正常表现

- 苹果标志会一直保持到加速桌面准备好；登录前可能黑屏几秒（辅助程序在用加速模式重启 WindowServer）。
- 检查：`bash "$M" status` 应该显示 `accel|ON`、`locks|none`、`plugin|QUIET ... shader reader present`。
- 日志：`/var/log/nmx-autoarm.log` 里有 `DONE: armed WindowServer ... up for 60 s`。

## 5. 恢复

- 在 OpenCore 菜单里选中 Macintosh HD，按 **Shift + 回车**进安全模式（安全模式不加载 `/Library/Extensions` 里的驱动）。
- 或者把 EFI 里的配置换回基础 `config.plist`。没有 `nmxintel=1` 时，NMXGPU 会主动放弃接管显卡。
- 加速失败一次后，辅助程序会上锁，下次开机不再开启加速；清除保护锁：`sudo bash "$M" repair`。
- 完全卸载：删除 `/Library/Extensions/{NMXGPU,NMXAccel,NVRMAGDC}.kext`、`/Library/GPUBundles/{NVMTLDriver.bundle,nvmtl}`，运行 `install-autoarm.sh --remove`，然后重建 AuxKC。

## 6. 排查记录（这些坑的来龙去脉）

| 现象 | 原因 | 解决 |
|---|---|---|
| WindowServer 崩溃循环，日志写着 `mapping process is a platform binary, but mapped file is not` | AMFI 不允许平台二进制加载未签名的插件 | 开启 AMFIPass，并加上 `amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0` |
| 还是崩溃循环：`Assertion failed: (Failed to create MetalDevice (non-null)), function Display ... Display.cpp:3228`，表面上像 `Setting offline display 0x00000000` / mode 0 | 反汇编 CoreDisplay 后找到这个断言；换上详细日志版插件后看到：`vk: dlopen(/Library/GPUBundles/nvmtl/libvulkan_intel.dylib) ... no such file` → `NVK did not come up ... refusing to be the Metal device` | 补装 ANV Vulkan 驱动（第 2.1 节） |
| 加速一旦打开，就没法在运行中关掉 | `debug.nvaccelfb` 写 0 不生效 | 换回基础配置后重启 |

诊断技巧：把 `out/debug/NVMTLDriver.bundle/Contents/MacOS/NVMTLDriver` 换进已安装的插件，用 `sudo log show --last boot --predicate 'eventMessage CONTAINS "NVMTL"'` 查看；驱动自己的日志用 `eventMessage contains "NullMoth"`。

## 7. 已知问题（作者列出的，在 Tahoe 上）

- Tahoe 比 Sequoia 慢、更热（Liquid Glass 的 GPU 负担较重）。打开「辅助功能 → 显示 → 降低透明度」会明显改善。
- 不在白名单 `/Library/GPUBundles/nvmtl-allow.txt` 里的 App 拿不到 GPU。
- 外接显示器只支持镜像。

---

<a id="english"></a>

## English

Metal acceleration for the i5-11300H's Iris Xe (`8086:9A49`) with [zep245/IrisXe-macos-driver](https://github.com/zep245/IrisXe-macos-driver), a NullMoth-based port of Linux i915 with Mesa ANV (Vulkan) and a Metal-on-Vulkan plugin. Confirmed working on this machine on 2026-11-02.

| Result | |
|---|---|
| System Information | Intel Iris Xe Graphics, Metal: Supported, VRAM (dynamic) 1536 MB |
| Panel | **3200x2000 @ 90.00 Hz** (native resolution and refresh rate) |
| Accelerated desktop | on (`debug.nvaccelfb = 1`; 2202 display submissions OK and 0 failed within a minute) |
| 60 MB DVMT | not an issue: scanout buffers come from system memory |

> ⚠️ Experimental kernel driver. It needs reduced SIP, `SecureBootModel Disabled` and the AMFI relaxations below, which lower system security. **Back up your EFI first**, and know how to safe-boot with Shift + Enter.

### 1. Files

| Source | File | Purpose |
|---|---|---|
| zep245 release **v1.0.3** | `nmxgpu-macos-15.zip` | NMXGPU.kext, `tahoe/NMXAccel.kext`, NVRMAGDC.kext, quiet Metal plugin, shader translator, autoarm helper, `IrisXe Manager.app` |
| zep245 release **v1.0.0** | `nmx-vulkan-macos-15-intel.zip` | **full Metal plugin** (with `air-runtime/`) + **Mesa ANV Vulkan driver** (`out/nmx-metal/nvmtl/`). Later releases only link to Actions artifacts, which need a GitHub login |
| dortania OCLP | `AMFIPass-v1.4.1-RELEASE.zip` (SHA-256 `07b26614…dc961e`) | goes in `EFI/OC/Kexts`; lets WindowServer load the unsigned Metal plugin |

The GPU firmware (`tgl_dmc_ver2_12`, `tgl_guc_70.1.1`, `tgl_huc_7.9.3`) is embedded in NMXGPU.kext.

### 2. Install the driver (on macOS on the Redmi)

```sh
M="$HOME/nmx/nmxgpu-macos-15/out/IrisXe Manager.app/Contents/Resources/irisxe-manager.sh"
sudo bash "$M" install "$HOME/nmx/nmxgpu-macos-15" gpu accel agdc "fullplugin@$HOME/nmx/mesa" plugin xlate autoarm
```

#### ⚠️ 2.1 Install the Vulkan driver the installer leaves out

`fullplugin` copies only `NVMTLDriver.bundle`, **not the ANV Vulkan driver next to it**. Without that driver WindowServer aborts in a loop (section 6). Reported upstream as [zep245/IrisXe-macos-driver#3](https://github.com/zep245/IrisXe-macos-driver/issues/3).

```sh
S=$HOME/nmx/mesa/out/nmx-metal/nvmtl; G=/Library/GPUBundles/nvmtl
for f in libvulkan_intel.dylib libvulkan.1.dylib libvulkan.dylib libdrm.2.dylib libSPIRV-Tools.dylib intel_icd.json; do
  sudo cp "$S/$f" "$G/$f.new" && sudo mv -f "$G/$f.new" "$G/$f"; done
sudo chown -R root:wheel $G; sudo chmod -R go-w,a+rX $G
```
(Keep the newer `libnvmtl_translate.dylib` from v1.0.3.)

#### 2.2 If the kexts are "not approved to load"

Rebuild the AuxKC directly (back up the old one first; SIP here is `0x0A13`):
```sh
sudo kmutil create -n aux --volume-root / --allow-missing-kdk --kernel /System/Library/Kernels/kernel \
  -B /System/Library/KernelCollections/BootKernelExtensions.kc -S /System/Library/KernelCollections/SystemKernelExtensions.kc \
  --repository /Library/Extensions -A /Library/KernelCollections/AuxiliaryKernelExtensions.kc.new -z
sudo mv -f /Library/KernelCollections/AuxiliaryKernelExtensions.kc.new /Library/KernelCollections/AuxiliaryKernelExtensions.kc
```

### 3. OpenCore changes

Use [`EFI/OC/config-igpu-accel.plist`](../EFI/OC/config-igpu-accel.plist) (add your own serials), or generate it with `python3 -I scripts/make_nmx_config.py B EFI/OC/config.plist out.plist`.

| Where | Change |
|---|---|
| Kernel → Add | **WhateverGreen off**; **AMFIPass.kext on, right after Lilu** |
| Kernel → Block | `com.apple.iokit.IONDRVSupport`, Strategy `Exclude` (the driver's framebuffer must be display 0) |
| DeviceProperties → `PciRoot(0x0)/Pci(0x2,0x0)` | `AAPL,ig-platform-id` = `0000499A`, `device-id` = `499A0000`, `AAPL,slot-name` = `built-in` |
| UEFI → Output → Resolution | `Max` (native 3200x2000, which i915 takes over) |
| boot-args (append) | `nmxintel=1 nmxaccel=1 -nmintelfboff nmxcopyfwd=1 nmxmodern=1 nmxintelfb=1 -nmxnosnap amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0 nmxws=1 nmxautoarm=1` (and drop `-igfxvesa`) |

Test in two stages: first without `nmxws=1 nmxautoarm=1` (stage A: i915 drives the panel only), then with them (stage B: accelerated desktop).

### 4. What a good boot looks like

- The Apple logo stays until the accelerated desktop is ready. There may be a few seconds of black before the login window while the helper restarts WindowServer in accelerated mode.
- `bash "$M" status` shows `accel|ON`, `locks|none`, `plugin|QUIET ... shader reader present`.
- `/var/log/nmx-autoarm.log` ends with `DONE: armed WindowServer ... up for 60 s`.

### 5. Recovery

- In OpenCore, select Macintosh HD and press **Shift + Enter** for safe mode (it skips `/Library/Extensions`).
- Or put the base `config.plist` back. Without `nmxintel=1`, NMXGPU declines the GPU.
- After a failed arm, the helper locks acceleration for the next boot; clear the lock with `sudo bash "$M" repair`.
- Full removal: delete `/Library/Extensions/{NMXGPU,NMXAccel,NVRMAGDC}.kext` and `/Library/GPUBundles/{NVMTLDriver.bundle,nvmtl}`, run `install-autoarm.sh --remove`, then rebuild the AuxKC.

### 6. Debugging notes

| Symptom | Cause | Fix |
|---|---|---|
| WindowServer abort loop, `mapping process is a platform binary, but mapped file is not` | AMFI refuses the unsigned plugin in a platform binary | AMFIPass + `amfi_get_out_of_my_way=0x1 amfi=0x80 ipc_control_port_options=0` |
| Still an abort loop: `Assertion failed: (Failed to create MetalDevice (non-null)), function Display ... Display.cpp:3228`; the logs look like `Setting offline display 0x00000000` / mode 0 | Found the assert by disassembling CoreDisplay. The verbose plugin then showed `vk: dlopen(/Library/GPUBundles/nvmtl/libvulkan_intel.dylib) ... no such file` → `NVK did not come up ... refusing to be the Metal device` | Install the ANV Vulkan driver (section 2.1) |
| Acceleration cannot be turned off at run time | Writing 0 to `debug.nvaccelfb` has no effect | Switch back to the base config and reboot |

Tip: put `out/debug/NVMTLDriver.bundle/Contents/MacOS/NVMTLDriver` into the installed plugin and read `sudo log show --last boot --predicate 'eventMessage CONTAINS "NVMTL"'`. Driver logs: `eventMessage contains "NullMoth"`.

### 7. Known issues (upstream, Tahoe)

- Tahoe is slower and warmer than Sequoia (Liquid Glass costs more GPU work). Accessibility → Display → **Reduce transparency** helps a lot.
- Apps that are not in `/Library/GPUBundles/nvmtl-allow.txt` get no GPU device.
- External displays: mirroring only.
