# TB331FC 主线 Linux —— 显示回归问题说明（交给新会话的完整背景）

## 一、项目与硬件

- 设备：Lenovo 小新 Pad 2024（**TB331FC**），SoC **SM6225-AD / 骁龙 685**，8GB RAM / 128GB UFS
- 面板：**INX p255_inx**，**1200×1920**，DSC 压缩面板，背光走 DCS（0x51）
- 触控：**Novatek NT36523**（SPI）
- WiFi：WCN3990（已打通：rmtfs + pd-mapper + tqftpserv + ath10k_snoc）
- 内核源码树：`~/kbuild/linux-next-tb128fu-hx83102-panel-port`（WSL Ubuntu 24.04）
  内核版本 `6.14.0-rc5-next-20250306`，源自 TB128FU 的 linux-next 分支
- 交叉编译：`make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j10 Image`
- 打包/刷写：`mkv4.py --mode boot --kernel <Image> --out <img>`，刷到 **slot B**（A 槽保持原厂 Android，绝不写入）
- 调试通道：USB CDC-ACM gadget → Windows 上 **COM3**，用 `tools/tty.ps1`（命令经环境变量 `TTYCMD` 传入）直接操作机身 shell

---

## 二、曾经完全可用的状态（基线，务必保留）

2026-10-22 产出的镜像对，**显示完全正常**：

```
boot_b         ← D:\TB331FCLinux\build\boot_pps.img        (36 MB, 10-22 22:31)
vendor_boot_b  ← D:\TB331FCLinux\build\vb_panel3.img       (2.6 MB, 10-22 22:29)
```

这对镜像的显示配置：

```
面板驱动  panel-himax-hx83102.c，compatible = "lenovo,p255-inx"
模式      1200x1920 @ 60Hz，htotal 1396 / vtotal 2226，.clock = 186473
DSC       开启，v1.1，8bpp/8bpc，slice 600x20，slice_count 2，slice_per_pkt 1
初始化    忠实回放原厂 DTB 里 309 条 DSI 命令，但在 0x11(sleep out) 之前停下，
          先发标准 DSC PPS（drm_dsc_pps_payload_pack + mipi_dsi_picture_parameter_set
          + mipi_dsi_compression_mode_ext），再发 0x11 / 0x29
DPU OPP   DT 里 6 档：19200000 / 200000000 / 300000000 / 383000000 / 470000000 / 560000000
DTB       打开 mdss 与 dispcc，cmdline 不带 nomodeset
```

**这条基线今天复测过：刷回去显示正常、无条纹。**
（注意：刷回基线会同时把 initramfs 换回 10-22 的 busybox 版，不会进 Alpine）

---

## 三、回归症状

经过 4 天开发（打通 WiFi + 触控 + Alpine + Niri）后，显示坏掉：

1. 最初：**条纹花屏，与内核日志混杂**（日志滚动时条纹区域变化）
2. 把 DPU OPP 表修复成 6 档后：变成 **蓝绿网格条纹**（网格状，不再是行条纹）
3. 串口/内核日志同样有条纹 → 是系统级显示问题，不是应用渲染问题

---

## 四、这 4 天做过的改动（全部列在此）

### 4.1 内核（3 个文件 + .config）

| 文件 | 改动 |
|---|---|
| `drivers/input/touchscreen/nt36523_ts.c` | INT 电平监视、5ms 轮询（加了又删）、厂商 WDT 逻辑（6 字节 + >10 次）、被拒包打印、**新增并 EXPORT `nvt_ts_panel_event(bool on)`**、日志降噪 |
| `drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c` | 新增一段"钳位到 DT 里最高 OPP"的代码（见下） |
| `drivers/gpu/drm/panel/panel-himax-hx83102.c` | **仅两行调用**：`hx83102_enable()` 末尾 `nvt_ts_panel_event(true)`；`hx83102_disable()` 开头 `nvt_ts_panel_event(false)`（weak 符号）。DSC/PPS/初始化序列/时序均未改动 |
| `.config` | 打开 `ATH10K_DEBUG` / `ATH10K_DEBUGFS`（查 WiFi 用） |

`dpu_core_perf.c` 里新增的 clamp 原文：

```c
/*
 * TB331FC: clamp to the highest OPP present in the DT.  The
 * display pipeline shows stripes at 470 MHz, and 384 MHz is the
 * operating point described by the OPP table.
 */
{
    unsigned long max_opp_rate = ULONG_MAX;
    struct dev_pm_opp *max_opp;

    max_opp = dev_pm_opp_find_freq_floor(&kms->pdev->dev, &max_opp_rate);
    if (!IS_ERR(max_opp)) {
        clk_rate = min_t(u64, clk_rate, dev_pm_opp_get_freq(max_opp));
        dev_pm_opp_put(max_opp);
    }
}
```

`nvt_ts_panel_event` 的实现（会 schedule 一个 work）：

```c
static DECLARE_WORK(nvt_panel_work, nvt_panel_on_work);

void nvt_ts_panel_event(bool on)
{
    if (!ts)
        return;
    if (on)
        schedule_work(&nvt_panel_work);
}
EXPORT_SYMBOL_GPL(nvt_ts_panel_event);
```

### 4.2 DTB（在 `D:\TB331FCLinux\build\CANONICAL.dts` 上直接改，非源码编译）

1. aliases 路径 `/soc@0/` → `/soc/`
2. 蓝牙：加 `vddrf-supply` / `vddch0-supply`；l16 → 1800000、l17 → 1304000
3. `serial@4a8c000`：加 `pinctrl-0 = <0x57>`（qup3 四线）
4. glink-edge：加 IPCRTR 通道
5. **`spi@4a80000`：删掉 `dmas` 和 `dma-names`**（为触控）
6. DPU 的 `opp-table` 被缩减成**只剩一个 `opp-384000000`**（曾加过 470 档，因"画面更差"又删掉）

---

## 五、今天做的二分定位（已验证结论）

| 组合 | 结果 |
|---|---|
| 基线内核 `boot_pps` + 基线 DTB `vb_panel3` | ✅ **显示正常** |
| 基线内核 `boot_pps` + 你的 DTB（我修好 OPP 成 6 档，`vb_oppfix2.img`） | ✅ **显示正常** → **DTB 无罪** |
| 你的内核 `boot_quiet` + 你的 DTB（单档 384） | ❌ 条纹；dmesg 见下 |
| 你的内核 `boot_quiet` + 你的 DTB（OPP 修成 6 档） | ❌ **蓝绿网格条纹** |
| 你的内核（**回退 clamp**）+ 你的 DTB（OPP 6 档），`boot_noclamp.img` | ⏳ **刚刷入，结果未确认** |

关键日志（单档 384 时）：

```
dev_pm_opp_set_rate: failed to find OPP for freq 470000000 (-34)   # -34 = -ERANGE
[drm:dpu_core_perf_crtc_update:424] [dpu error]failed to set core clock rate 384000000
```

**已查明**：dispcc 的 MDP 时钟频率表是
`19.2M / 200M / 300M / 383M / 470M / 560M`（**383 而不是 384**），
所以 `clk_set_rate(384MHz)` 必然失败，DPU 核心时钟根本没被设上。

**结论**：DTB 已确认无罪；问题在**你的内核**（clamp 或面板驱动的两个 hook，或 .config）。

---

## 六、当前设备状态

- slot B 上：`boot_b = boot_noclamp.img`（你的内核，仅回退 clamp）
              `vendor_boot_b = vb_oppfix2.img`（你的 DTB，OPP 修为 6 档）
- 串口 COM3 可用；曾出现过一次 `未知 USB 设备(设备描述符请求失败)`（gadget 枚举失败），
  断电重启后恢复 —— 怀疑与 RNDIS + ACM 复合 gadget 配置有关

---

## 七、待验证的假设（按优先级）

1. **clamp 是元凶** —— 已构建 `boot_noclamp.img`，待确认结果。
   注意：在 6 档 OPP 下这段 clamp 理论上是 no-op（`min(clk_rate, 560MHz)`），
   所以如果结果仍是条纹，说明不是它。
2. **面板驱动的 `nvt_ts_panel_event` hook 扰动 TDDI** —— 触控重初始化（`nvt_panel_on_work`
   走 `nvt_restore_cmd_func()` 等 SPI 动作）可能在面板刚 enable 后复位了这颗 TDDI，
   导致显示侧被打乱。验证方法：临时删掉那两个 hook 再编一版。
3. **`.config` 的 ATH10K_DEBUG/DEBUGFS** —— 只影响 ath10k 结构体，理论上与显示无关；
   但如果内核用 `vmlinux` 布局变化影响了 CMA/DMA 分配，也可能间接相关。
4. **DPU 在 470MHz 下本身会有条纹** —— 用户自己观察到"加 470 档后画面更差"。
   若如此，需要在 DTB 里把 470/560 档去掉，只保留 383 档，
   并让 `dpu_core_perf` 在找不到 OPP 时**优雅降级**而不是报错返回。

---

## 八、有用的命令与环境

```powershell
# 串口执行命令（COM3）
$env:TTYCMD = 'dmesg | grep -iE "opp|core clock" | tail -6'
$env:TTYWAIT = '5000'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\TB331FCLinux\tools\tty.ps1

# 刷机（设备进 fastboot：电源+音量下）
& 'D:\搞机助手\fastboot.exe' --set-active=b
& 'D:\搞机助手\fastboot.exe' flash boot_b <img>
& 'D:\搞机助手\fastboot.exe' flash vendor_boot_b <img>
& 'D:\搞机助手\fastboot.exe' reboot

# 把新 DTB 换进已有 vendor_boot（保留 initramfs/cmdline）
python tools\repack_vb_dtb2.py <in_vb.img> <new.dtb> <out_vb.img>
```

关键工具（都在 `D:\TB331FCLinux\tools\`）：

| 工具 | 用途 |
|---|---|
| `mkv4.py` | 打包 v4 boot / init_boot / vendor_boot |
| `repack_vb_dtb2.py` | 只替换 vendor_boot 里的 DTB（页对齐正确，保留其它段） |
| `bootinfo.py` | 解析 boot/vendor_boot 头（**注意：它算 vendor_boot 里 dtb 偏移会算错，实测 DTB 在 `0x30f000`） |
| `fix_dpu_opp_table.py` | 把 CANONICAL.dts 的 DPU OPP 表恢复成 6 档 |
| `revert_dpu_clamp.py` | 回退 dpu_core_perf.c 里的 clamp |
| `tty.ps1` | 串口执行命令 |

---

## 九、请帮我做的事

1. 判断"你的内核 vs 基线内核"到底差在哪导致条纹，给出**最小改动**方案
   （既要保住 WiFi + 触控，又要显示干净）
2. 重点看：`nvt_ts_panel_event` 这个 hook 是否会在面板 enable 后扰动 TDDI；
   如果会，怎么在保留触控的前提下避免
3. DPU 时钟的正确配置方式：OPP 表该放哪几档？`dpu_core_perf` 找不到 OPP 时
   应该降级还是报错？是否需要 `required-opps` 指向 power-domain corner？
4. 顺带看一下：RNDIS + ACM 复合 gadget 是否该拆成两个，避免串口再次消失
