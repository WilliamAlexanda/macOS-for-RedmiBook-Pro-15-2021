# 校园网 / 企业级 Wi-Fi（WPA2-Enterprise, 802.1X）/ Campus & enterprise Wi-Fi

[中文](#中文) · [English](#english)

---

## 中文

### 现象

家用 Wi-Fi、手机热点都能连，但 **ShanghaiTech（WPA2 企业级，PEAP，学号 + 密码）一直连不上**：转圈一会儿后提示"离得近一点或运行诊断"。

### 原因：AirportItlwm 2.4.0（`738d4c6`）的 802.1X 时序 bug

企业级网络的认证由 macOS 的 `eapolclient` 完成，它在关联成功后马上向驱动查询 BSSID。旧版驱动只有在 net80211 进入 `S_RUN` 状态后才返回 BSSID，于是出现：

```
eapolclient  APPLE80211_IOC_BSSID return 0xe0822403
eapolclient  Disassociated
kernel       populateJoinStatus: assoc status 0x22 retVal 0x3f1   (10 s join timeout)
eapolclient  en0 STOP
```

`eapolclient` 以为链路已经断开，EAP 报文（学号、密码）一个都没发出去，10 秒后系统判定加入失败。
家用 Wi-Fi 和热点是 WPA2-PSK，握手在驱动内部完成，不走 `eapolclient`，所以不受影响。

同款网卡（AX201）、同一驱动版本的用户报告过同样的问题：[laobamac/itlwm#31](https://github.com/laobamac/itlwm/issues/31)。
修复在 [laobamac/itlwm#35](https://github.com/laobamac/itlwm/pull/35)，截至 2026-11-10 还没有合并进上游。

### 修复（2026-11-10 已验证）

换用 [wfx1024/itlwm `fix/enterprise-eapol`](https://github.com/wfx1024/itlwm/tree/fix/enterprise-eapol) 的构建。它是上游 laobamac/itlwm `7204c69` 加上 #35 的修改，4 个文件共 14 行，见 [patches/itlwm/enterprise-eapol-8021x.patch](../patches/itlwm/enterprise-eapol-8021x.patch)：

- `getBSSID()` 从 `S_ASSOC` 起就返回 BSSID（Skywalk 接口和 ioctl 两处）；
- `enqueuePacket()` 从 `S_ASSOC` 起就允许发送，EAPOL 帧不再被丢弃；
- 对 802.1X 类型的 AKM，关联成功后立即把链路置为 up。

具体构建与安装：

| | |
|---|---|
| 来源 | wfx1024/itlwm GitHub Actions run 41782505063，artifact `AirportItlwm-Tahoe-Release`（提交 `4240f66`）。下载需要登录 GitHub，有效期到 2027-02-02 |
| 文件 | `AirportItlwm-Tahoe-v2.4.0-RELEASE-alpha-4240f66.zip` |
| SHA-256（`Contents/MacOS/AirportItlwm`） | `beccc746aff1f5da5e21095e8c5134fd223ed17b73a3c571f065db38a8254f0d` |
| 安装 | 替换 `EFI/OC/Kexts/AirportItlwm.kext` 后重启。`Info.plist` 与旧版相同，`config.plist` 不用改 |
| 确认 | 系统信息 → Wi-Fi → 固件版本显示 `itlwm: 2.4.0_4240f66` |

本机实测：
- ShanghaiTech（WPA2 企业级，PEAP）连接成功，日志为 `en0 EAP-PEAP: successfully authenticated`，联网正常；
- 关联在 5 秒内完成，没有再出现 10 秒超时；
- 家用 WPA2-PSK 和手机热点照常可用。

首次连接 ShanghaiTech 时：用户名填学号，密码填统一认证密码。弹出"验证证书"时点 **继续**，再输入一次电脑登录密码。

**回退**：旧驱动备份在本机 `~/itlwm-backup/AirportItlwm-738d4c6.kext`，放回 `EFI/OC/Kexts/` 后重启即可。
上游合并 #35 并发布新版后，建议换回 laobamac 的正式构建。

---

## English

**Symptom:** home WPA2-PSK networks and phone hotspots work, but the campus network (ShanghaiTech: WPA2-Enterprise, PEAP) fails with "move closer or run diagnostics".

**Cause:** an 802.1X timing bug in AirportItlwm 2.4.0 (`738d4c6`). Right after association, `eapolclient` asks the driver for the BSSID. The old build only answers once net80211 reaches `S_RUN`, so it returns `0xe0822403`. `eapolclient` then logs `Disassociated` and never sends the EAP response, and the join times out after 10 s (`assoc status 0x22 retVal 0x3f1`). PSK networks are unaffected, because their handshake runs inside the driver. Same report: [laobamac/itlwm#31](https://github.com/laobamac/itlwm/issues/31).

**Fix (verified 2026-11-10):** the [wfx1024/itlwm `fix/enterprise-eapol`](https://github.com/wfx1024/itlwm/tree/fix/enterprise-eapol) build. It is upstream `7204c69` plus [laobamac/itlwm#35](https://github.com/laobamac/itlwm/pull/35) (14 lines, [patch](../patches/itlwm/enterprise-eapol-8021x.patch)):
- `getBSSID()` answers from `S_ASSOC` on;
- `enqueuePacket()` accepts frames from `S_ASSOC` on;
- the link goes up at association for 802.1X AKMs.

Build details:
- Built by GitHub Actions run 41782505063 (artifact `AirportItlwm-Tahoe-Release`, commit `4240f66`).
- Binary SHA-256 `beccc746aff1f5da5e21095e8c5134fd223ed17b73a3c571f065db38a8254f0d`.
- To install, replace `EFI/OC/Kexts/AirportItlwm.kext`; `config.plist` needs no change.
- Check: System Information shows `itlwm: 2.4.0_4240f66`.

Result on this machine:
- ShanghaiTech authenticates (`EAP-PEAP: successfully authenticated`), and internet works;
- association completes in under 5 s;
- PSK networks still work.

Switch back to laobamac's official build once #35 is merged.
