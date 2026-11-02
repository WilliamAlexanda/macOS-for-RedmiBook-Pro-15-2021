# 修改隐藏的 DVMT 预分配显存 / Changing the hidden DVMT Pre-Allocated setting

[中文](#中文) | [English](#english)

---

## 中文

RedmiBook Pro 15 2021 的 Insyde BIOS 把 DVMT 预分配显存固定在 **60MB**（GMS `0xFE`），设置界面里没有这个选项。但这个选项并没有被删掉，它的值还存在 UEFI 变量里，可以直接修改。

**什么时候需要改**
- 用 [zep245 i915 驱动](igpu-zep245.md)：**不需要改**。它的显存从系统内存分配，60MB 也能用。
- 用苹果原版 TGL 驱动（WhateverXe）：60MB 会导致开启加速时整机冻结，必须改成 96MB 或 128MB。具体测试结果见 [igpu-whateverxe.md](igpu-whateverxe.md)。

### 设置项的位置

| 选项 | 所在变量 | 偏移 | 取值 |
|---|---|---|---|
| DVMT Pre-Allocated | `SaSetup`<br>GUID `72C5E28C-7783-43A1-8767-FAD73FCCAFA4`<br>大小 `0x430` | **`0x84`** | `0xFE` = 60M（出厂值）<br>`0x02` = 64M<br>`0x03` = 96M<br>`0x04` = 128M<br>`0x05` = 160M |
| DVMT Total Gfx Mem | 同上 | `0x85` | `1` = 128M，`2` = 256M（出厂值），`3` = MAX |
| GTT Size | 同上 | `0x3B` | `3` = 8MB（出厂值） |
| Aperture Size | 同上 | `0x3C` | `1` = 256MB（出厂值） |

已验证的 BIOS 版本：机器上的 `RMATG5B0P0D0D`，以及官网下载的 `RMATG5B0P0F0F`。两个版本的偏移完全相同，机器上读到的出厂值也都和上表一致。

### 在 macOS 里修改（推荐）

这台机器的 BIOS 允许 macOS 直接写 `SaSetup`，不需要额外的 UEFI 工具：

```sh
sudo ./scripts/set-dvmt.sh show     # 查看当前值
sudo ./scripts/set-dvmt.sh 128      # 改成 128M，然后重启
```

这个脚本有几道安全检查：
- 先检查变量大小是不是 `0x430`、当前值是否合理，不对就停下；
- 把原始变量备份到 `/var/root/`；
- 确认**只有 0x84 这一个字节**会改变才写入；
- 写入后读回核对。

重启后可以这样确认：i915 驱动的开机日志会显示 `stolen memory ... 128 MiB`，WhateverXe 的 DEBUG 日志会显示新的 GMS 值。

**恢复默认**：进入 BIOS 按 **F9**（Load Defaults）并保存，或者运行 `sudo ./scripts/set-dvmt.sh restore /var/root/SaSetup-backup-*.bin`。

⚠️ 注意：
- 进 BIOS 恢复默认值、刷新 BIOS 之后，这个值会变回 60M，需要重新设置。
- 在 OpenCore 里执行 Reset NVRAM 也**可能**把它清掉。

### 其他 BIOS 版本：自己找偏移

不同版本的偏移可能不一样，建议先核对。整个过程**不需要运行**小米的更新程序：

1. 从小米官网下载对应版本的 BIOS 更新包，比如 `RMATG5B0P0F0F.exe`。
2. 解包：`python3 scripts/bios/unpack_xiaomi_bios.py RMATG5B0P0F0F.exe out`
   - 这个更新程序是 Insyde H2OFFT 的 7z 自解压包，里面的压缩包每个字节都循环左移了 1 位；脚本会把它还原再解压。
   - 解出来的 BIOS 镜像叫 `out/isflash_release.bin`。
3. 拆出固件里的模块：`python3 scripts/bios/fvwalk.py out/isflash_release.bin out/mods`
4. 解析 Setup 菜单：`python3 scripts/bios/ifr.py out/mods/fe3542fe_*_10.bin DVMT`
   - `FE3542FE` 是 Insyde 的 SetupUtility 模块。
   - 输出里会有每个选项所在的变量、偏移和可选值。
5. 用 `set-dvmt.sh show` 读出机器上当前的值。确认这个偏移上的值是 `0xFE` 后，再修改。

---

## English

The RedmiBook Pro 15 2021 Insyde BIOS fixes DVMT Pre-Allocated at **60 MB** (GMS `0xFE`) and hides the option from setup. The option still exists, and its value lives in a UEFI variable that can be changed directly.

**Do you need this?**
- With the [zep245 i915 driver](igpu-zep245.md): **no**. It allocates GPU memory from system RAM, so 60 MB works.
- With Apple's TGL driver (WhateverXe): yes. At 60 MB the machine hard-freezes as soon as the accelerator starts, so set 96 MB or 128 MB. See [igpu-whateverxe.md](igpu-whateverxe.md).

### Where the setting is

| Setting | Variable | Offset | Values |
|---|---|---|---|
| DVMT Pre-Allocated | `SaSetup`<br>GUID `72C5E28C-7783-43A1-8767-FAD73FCCAFA4`<br>size `0x430` | **`0x84`** | `0xFE` = 60M (factory)<br>`0x02` = 64M<br>`0x03` = 96M<br>`0x04` = 128M<br>`0x05` = 160M |
| DVMT Total Gfx Mem | same | `0x85` | `1` = 128M, `2` = 256M (factory), `3` = MAX |
| GTT Size | same | `0x3B` | `3` = 8MB (factory) |
| Aperture Size | same | `0x3C` | `1` = 256MB (factory) |

Verified BIOS versions: `RMATG5B0P0D0D`, on the machine, and `RMATG5B0P0F0F`, downloaded from Xiaomi. The offsets are identical in both, and the factory values read from the machine match the table.

### Changing it from macOS (recommended)

This BIOS lets macOS write `SaSetup` directly, so no UEFI shell tool is needed:

```sh
sudo ./scripts/set-dvmt.sh show     # current value
sudo ./scripts/set-dvmt.sh 128      # set 128M, then reboot
```

The script runs several safety checks:
- It stops unless the variable is `0x430` bytes and the current value is plausible.
- It backs up the original variable to `/var/root/`.
- It only writes if **byte 0x84 alone** would change.
- It reads the variable back after writing.

To confirm after a reboot: the i915 driver logs `stolen memory ... 128 MiB`, and the WhateverXe DEBUG build logs the new GMS value.

**Undo**: in BIOS setup, press **F9** (Load Defaults) and save. Or run `sudo ./scripts/set-dvmt.sh restore /var/root/SaSetup-backup-*.bin`.

⚠️ Caveats:
- Loading BIOS defaults or flashing a BIOS update brings the value back to 60M, so you have to set it again.
- OpenCore's Reset NVRAM **may** clear it as well.

### Other BIOS versions: find the offset yourself

The offset can change between versions, so check it first. None of this runs Xiaomi's updater:

1. Download the matching BIOS update from Xiaomi, for example `RMATG5B0P0F0F.exe`.
2. Unpack it: `python3 scripts/bios/unpack_xiaomi_bios.py RMATG5B0P0F0F.exe out`
   - The updater is an Insyde H2OFFT 7z SFX, and every byte of its archive is rotated left by 1 bit. The script undoes the rotation and extracts the archive.
   - The BIOS image is `out/isflash_release.bin`.
3. Extract the firmware modules: `python3 scripts/bios/fvwalk.py out/isflash_release.bin out/mods`
4. Parse the Setup forms: `python3 scripts/bios/ifr.py out/mods/fe3542fe_*_10.bin DVMT`
   - `FE3542FE` is Insyde's SetupUtility module.
   - The output gives each question's variable, offset and option values.
5. Read the machine's current value with `set-dvmt.sh show`. Only change it once that offset reads `0xFE`.
