# TB331FC 主线 Linux 移植 —— 完整文档（含"迁移到内置存储"方案）

> 面向目标：**把 Linux 彻底装进内置 UFS，脱离 SD 卡**，并长期维护。
> 所有数据均来自设备实测。硬件：联想小新 Pad 2024 / TB331FC / p255 / SM6225-AD（骁龙 685）。
> 内核：`6.14.0-rc5-next-20250306`（源自 TB128FU 的 linux-next 分支）。

---

# 第一部分：当前状态总览

| 能力 | 状态 | 备注 |
|---|---|---|
| 主线内核启动（ABL 放行） | ✅ | 需 `dtc -@` 生成 120 个 `__symbols__` |
| 面板 1200×1920 **@90Hz** + DSC | ✅ | 必须 90Hz，60Hz 会花屏 |
| 背光调节（KTZ8866） | ✅ | I2C0 @0x11，GPIO27 |
| 触控（Novatek NT36523N，10 点） | ✅ | 固件下载成功，`PID=6072` |
| GPU（freedreno FD610，GL 4.6/GLES 3.2） | ✅ | UBWC 已禁用以避开花屏 |
| Niri / GNOME 桌面 | ✅ | 画面干净 |
| WiFi（WCN3990） | ✅ | `ath10k_snoc` |
| USB 串口控制台（COM3） | ✅ | CDC-ACM gadget |
| 根文件系统 | ✅ | **目前在 SD 卡上的 ext4 镜像（loop 挂载）** ← 待迁移 |
| 内置存储（UFS） | ✅ 可识别 | 分区表见第三部分，**尚未使用** |

---

# 第二部分：硬件与关键参数（速查）

```
SoC        SM6225-AD（骁龙 685）/ 代号 p255、khaje
内存/存储  8 GB RAM / 128 GB UFS（实际可用 ~115 GiB）
Bootloader ABL（LinuxLoader.efi），支持 fastboot
GPU        Adreno 610（a610）
WiFi       WCN3990（ath10k_snoc）
```

## 2.1 面板（INX p255_inx）

```
分辨率     1200 × 1920（原生竖屏扫描方向）
时序       1396 × 2226 @ 90 Hz，clock = 279675 kHz
           hfp 96 / hbp 96 / hpw 4；vfp 56 / vbp 248 / vpw 2
实测时钟   disp_cc_mdss_pclk0_clk  = 119402784
           disp_cc_mdss_byte0_clk  =  89552087
           disp_cc_mdss_mdp_clk    = 383000097   ← 见 4.1
DSC        v1.1，8bpp / 8bpc，slice 600×20，slice_count 2，slice_per_pkt 2
           必须在 0x11 之前下发标准 PPS，否则花屏
背光       外部 KTZ8866（I2C0 @0x11，使能 GPIO27）
初始化     回放厂商 309 条 DSI 命令（build/p255_inx_init.h）
```

## 2.2 触控（Novatek NT36523N）

```
总线       spi0.1（SE0 CS1），mode 0，10 MHz
IRQ/reset  TLMM gpio80 / gpio86
固件       novatek_ts_fw.bin（196608 B，需放在 rootfs 的 /lib/firmware）
固件布局   ILM 0x200→SRAM 0x0 (0x1985F)；DLM 0x21400→SRAM 0x1F400 (0xCB37)
           crc: 0x18=0xF4FD5D35(ILM)，0x1C=0x49618174(DLM)；0x20=0x03 表示 cascade
正确标志   dmesg 出现 fw_ver=0x0F / fw_type=0x01 / PID=6072
```

## 2.3 背光（KTZ8866）—— 重要认知

```
芯片       Kinetic KTZ8866（6 通道 LED 驱动 + LCD 偏压）
位置       i2c@4a84000（QUPv3 SE0）地址 0x11
使能脚     TLMM GPIO 27
主线驱动   drivers/video/backlight/ktz8866.c  ← 内核已自带
配置项     CONFIG_BACKLIGHT_KTZ8866=y
绑定       compatible = "kinetic,ktz8866"
           vddpos-supply / vddneg-supply / enable-gpios  ← 三者必需
节点名     /sys/class/backlight/ktz8866-backlight  量程 0..2047
```

> ⚠ **这块平板的面板 DCS 背光（0x51）是无效的**。Android 日志：
> `[ktz8866_leds] bkl_probe: probe success` + `[drm:sde_backlight_setup] Failed to register backlight cdev: -19`。
> 向面板发 DCS 0x51 不但不会改变亮度，还会与 90Hz DSC 视频流抢总线 → `dsi_err_worker status=5` → **右半屏全白**。

---

# 第三部分：迁移到内置存储（重点）

## 3.1 实测分区表

```
块设备                 大小        说明
sda (UFS)          120676352 KB   ≈ 115.1 GiB   主存储，14 个分区
  ├ sda1 … sda9     小分区        system/boot 相关，**勿动**
  ├ sda10          12582912 KB   = 12.0 GiB（super / 动态分区宿主）
  ├ sda11..sda13   小分区        **勿动**
  └ sda14         107667788 KB   = 102.7 GiB（userdata）← **Linux 目标分区**
sde (4 GiB)            66 个分区  A/B 槽：boot_a/b、vendor_boot_a/b、dtbo_a/b、super…
                                  **只使用 boot_b / vendor_boot_b，a 槽永不写入**
mmcblk0 (SD)         7634944 KB   = 7.3 GiB   当前根文件系统镜像所在
  └ mmcblk0p1        7633920 KB   FAT32，含 alpine-rootfs.img
loop0                3891200 KB   = 3.7 GiB   当前挂载为 /（ext4，已用 1.3 GiB）
```

**结论**：`userdata` 有 **102.7 GiB** 完全够用；A/B 槽机制让我们可以"B 槽 Linux、A 槽 Android"共存。

## 3.2 三种方案对比

| 方案 | 做法 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|
| **A. 直接占用 userdata** | `mkfs.ext4 /dev/sda14` 作为根 | 最简单、性能最好、102 GiB | **Android 数据被清空**（A 槽仍能启动，会重建 data） | 不再需要 Android |
| **B. 缩小 userdata + 新分区** | 用 `parted`/`sgdisk` 缩小 sda14，新建 `linux_root` | 保留 Android 数据，双系统独立 | 需改 GPT，操作风险高，ABL/Android 可能不认新布局 | 想长期双系统 |
| **C. 镜像文件放进 userdata** | 复制现有 `alpine-rootfs.img` 到 sda14（Android 数据保留或另建目录），loop 挂载 | **零分区风险**，当天可用，性能远好于 SD | 仍是 loop 文件，不是"真分区" | 过渡方案（推荐先做） |

**推荐路线**：
1. 先做 **C**（把 rootfs 从 SD 搬到 UFS 上的一个镜像文件）—— 立刻摆脱 SD，风险最低；
2. 稳定后执行 **A**（或 B），得到真正的分区根。

## 3.3 方案 C 具体步骤（在运行中的 SD 系统里执行）

```sh
# 1. 把 UFS 的 userdata 分区挂上（Android 若是 f2fs，需要内核支持或干脆格式化）
#    若决定清空 Android 数据，直接：
mkfs.ext4 -L ufsdata /dev/sda14
mkdir -p /mnt/ufs && mount /dev/sda14 /mnt/ufs

# 2. 复制现有根镜像过去（约 3.7 GiB）
cp /run/media/pluto/SD/alpine-rootfs.img /mnt/ufs/

# 3. 修改 initramfs 的 init：把镜像路径从 SD 改为 /dev/sda14
#    （见 3.5 的 init 片段）

# 4. 重新打包 initramfs 并刷 vendor_boot_b，然后重启并拔掉 SD
```

## 3.4 方案 A 具体步骤（真分区根，推荐最终形态）

```sh
# 1. 格式化（会清空 Android 数据）
mkfs.ext4 -L alpine /dev/sda14

# 2. 挂载并整根复制（排除运行时目录）
mkdir -p /mnt/newroot
mount /dev/sda14 /mnt/newroot
apk add rsync            # 若没有
rsync -aHAX --numeric-ids \
      --exclude={/proc/*,/sys/*,/dev/*,/run/*,/tmp/*,/mnt/*,/media/*} \
      / /mnt/newroot/

# 3. 检查 /etc/fstab（Alpine 默认可能为空，建议显式写）
cat > /mnt/newroot/etc/fstab <<'EOF'
LABEL=alpine  /       ext4  rw,noatime  0 1
EOF

# 4. 确保固件在位
ls /mnt/newroot/lib/firmware/novatek_ts_fw.bin

# 5. 更新 initramfs 的 init（见 3.5），刷 vendor_boot_b，重启（可拔 SD）
```

## 3.5 initramfs 的 init 改造（关键）

当前的 init 逻辑：

```
挂 /proc /sys /dev → 早期建 USB gadget → 挂 vfat /dev/mmcblk0p1 →
losetup alpine-rootfs.img → mount ext4 → 迁移挂载点 → busybox switch_root
```

改造为 UFS 根（**不再依赖 SD**）：

```sh
# 等 UFS 分区出现（内核 SCSI/UFS 驱动是内建的，sda14 会直接出现）
i=0
while [ ! -b /dev/sda14 ] && [ $i -lt 100 ]; do
    sleep 0.1; i=$((i+1))
done

mkdir -p /newroot
if ! /bin/busybox mount -t ext4 -o rw,noatime /dev/sda14 /newroot; then
    # 回退：尝试 SD 上的镜像（保留旧路径作为 fallback）
    ...
fi

# 可选：把 SD 挂到 /newroot/run/media/SD 方便访问
mount -t vfat /dev/mmcblk0p1 /newroot/run/media/SD 2>/dev/null

# 迁移内核文件系统
for d in proc sys dev; do
    /bin/busybox mount --move /$d /newroot/$d
done
[ -d /sys/kernel/config ] && /bin/busybox mount --move /sys/kernel/config /newroot/sys/kernel/config

exec /bin/busybox switch_root /newroot /sbin/init
```

**必须确认的内核配置**（UFS 能作为根）：

```
CONFIG_SCSI=y
CONFIG_BLK_DEV_SD=y
CONFIG_SCSI_UFSHCD=y
CONFIG_SCSI_UFS_QCOM=y          ← sm6225 UFS 控制器
CONFIG_SCSI_UFS_BSG / _CRYPTO   可选
CONFIG_EXT4_FS=y               （或放 initramfs 里）
```

> 实测确认：运行中的系统能列出 `sda` 的 14 个分区，说明 UFS 驱动已可用。
> 唯一风险是它是否**内建**（`=y`）而不是模块——模块的话必须在 initramfs 里带上。

## 3.6 双系统切换

```sh
# 回 Android（A 槽）
fastboot --set-active=a && fastboot reboot

# 回 Linux（B 槽）
fastboot --set-active=b && fastboot reboot
```

**A 槽永远不要写**。所有刷写只针对 `boot_b` / `vendor_boot_b`。

## 3.7 风险与回退

| 风险 | 缓解 |
|---|---|
| 格式化 sda14 清空 Android 数据 | 先把重要数据拷出；A 槽仍能启动并自动重建 data |
| 误写 GPT 导致无法启动 | **绝不使用 `parted` 修改已有的 sda1–sda13**；若要改 GPT，先 `sgdisk --backup` 备份到 SD |
| 新根起不来 | 保留 SD 卡作为 fallback：init 里先试 sda14，失败则回退到原来的 SD 镜像路径 |
| 刷错槽 | 每次刷机前 `fastboot getvar current-slot` 确认 |

---

# 第四部分：所有已解决的问题（含根因与修法）

## 4.1 DPU 核心时钟被降到 19.2 MHz → 条纹

`dispcc-sm6225.c` 的真实频率表只有 **383 MHz 可靠**（PLL0/2）：

```c
F(19200000,  TCXO, 1, 0, 0)
F(200000000, GCC_DISP_GPLL0_DIV, 1.5, 0, 0)   // 需切父时钟 → -EINVAL
F(300000000, GCC_DISP_GPLL0_DIV, 1,   0, 0)   // 同上
F(383000000, PLL0_OUT_MAIN,      2,   0, 0)   // ★ 唯一可靠
F(470000000, PLL0_OUT_MAIN,      2,   0, 0)   // 错：与 383 同分频
F(560000000, PLL0_OUT_MAIN,      2,   0, 0)   // 错
```

**修法**：DPU 的 `opp-table`（phandle **0x72**）只保留
```dts
opp-383000000 { opp-hz = <0x00 0x16d41dc0>; required-opps = <0x3a>; };
```
⚠ `383000000 = 0x16D41DC0`（不是 `0x16E36000`/384M）。

## 4.2 SPI 走 PIO 抢 DPU 带宽 → "有内容才花屏"

删掉 `spi@4a80000` 的 `dmas` 会让触控 SPI 退回 CPU PIO，饿死 DPU 取像素。
**修法**（恢复原厂值）：
```dts
dmas = <0x46 0x00 0x00 0x01 0x46 0x01 0x00 0x01>;
dma-names = "tx", "rx";
```

## 4.3 UBWC 导致 niri 花屏

sm6225 从 sm6115 继承的 UBWC 参数不正确。
**修法**（`drivers/gpu/drm/msm/msm_mdss.c`）：为 sm6225 提供不含 UBWC 版本的 `msm_mdss_data`，`qcom,sm6225-mdss` 指向它。之后 framebuffer 变为 `modifier=0x0`。

## 4.4 面板必须 90 Hz

DSC 的 `slice_height=20` 按 90Hz 帧结构设计；跑 60Hz 时高频内容（文字）解码失步 → 花屏。
**修法**：`.clock = 279675`（1396×2226×90）。

## 4.5 DSC 必须在 0x11 之前下发 PPS

只回放厂商 309 条命令不够，还要：
```c
drm_dsc_pps_payload_pack(&pps, &ctx->dsc);
mipi_dsi_picture_parameter_set_multi(&dsi_ctx, &pps);
mipi_dsi_compression_mode_ext_multi(&dsi_ctx, true, MIPI_DSI_COMPRESSION_DSC, 0);
```
参考实现：`panel-raydium-rm692e5.c`。

## 4.6 触控固件下载（两个必要条件）

1. `cascade_2nd_header_info` **必须从固件文件读**：
   `cascade_2nd_header_info = (fwdata[0x20] & 0x02) >> 1;`（本固件 = 1）
   强制为 0 → `bin crc ≠ golden`、`PID=0000`
2. 下载必须在**安静窗口**：面板 sleep + 触控 IRQ 关闭时执行
   （在显示扫描期间下载会导致 DLM 读回 CRC 每次不同）

`NVT_TRANSFER_LEN` 用厂商原值 `(63*1024)` 即可，**无需分块**。

## 4.7 面板/触控时序（参考主线 NT36523 做法）

```
prepare()   初始化寄存器 + PPS，**不发 0x11 / 0x29**
enable()    等触控就绪 → 下载固件（此刻面板仍 sleep）→ 发 0x11 → 120ms → 0x29 → 开背光
```
这样固件下载不会干扰任何显示内容。

## 4.8 背光是 KTZ8866，不是 DCS 0x51

见第二部分 2.3。修法：
1. DTB 增加 `backlight@11`（`kinetic,ktz8866`）到 `i2c@4a84000`
2. `CONFIG_BACKLIGHT_KTZ8866=y`
3. 面板 desc 的 `.has_dcs_backlight = false`

**效果**：10 次快速亮度扫描 → `dsi_err_worker` 0 次（改前 8 次就 3 次错误）。

## 4.9 USB 周期性掉线

RNDIS 在 Win11 无内置驱动 → 复合设备反复重枚举。
**修法**：initramfs 的 `gadget.sh` 只保留 ACM；移除 Alpine 侧重复的 `usbgadget` 服务。

---

# 第五部分：文件与工具清单

## 5.1 内核改动

| 文件 | 改动 |
|---|---|
| `drivers/gpu/drm/msm/msm_mdss.c` | sm6225 专用 data（无 UBWC） |
| `drivers/gpu/drm/panel/panel-himax-hx83102.c` | DSC + PPS、90Hz、follower 时序、`has_dcs_backlight=false`、背光去抖 |
| `drivers/input/touchscreen/nt36523_ts.c` | 厂商修复、面板事件 hook、WDT/ESD 恢复（`disable_irq_nosync`）、`nvt_fw_ready` |
| `drivers/input/touchscreen/nt36523_fw_update.c` | cascade 从文件读、IRQ 静默、`nvt_fw_ready` |
| `drivers/input/touchscreen/nt36523.h` | `NVT_TRANSFER_LEN (63*1024)` 保持原值 |
| `.config` | 见 5.3 |

## 5.2 DTB 改动（`build/CANONICAL_383_dma.dts`）

1. DPU OPP 单档 383 MHz
2. `spi@4a80000` 恢复 `dmas`
3. `i2c@4a84000` 增加 `backlight@11`（ktz8866）
4. 两个 `regulator-fixed`（bl_vddpos / bl_vddneg，always-on）
5. `touchscreen@1`（novatek）okay；`touchscreen@0`（himax）disabled
6. aliases `/soc@0/` → `/soc/`
7. 蓝牙供电、`serial@4a8c000` pinctrl、glink IPCRTR
8. 保留 `abl-stubs`（120 个符号）

**编译必须**：`dtc -@ -I dts -O dtb -o out.dtb in.dts`（生成 `__symbols__`）

## 5.3 关键内核配置

```
CONFIG_SCSI=y
CONFIG_BLK_DEV_SD=y
CONFIG_SCSI_UFSHCD=y
CONFIG_SCSI_UFS_QCOM=y
CONFIG_EXT4_FS=y
CONFIG_DRM_MSM=y
CONFIG_TOUCHSCREEN_NT36523_SPI=y
CONFIG_SPI_QCOM_GENI=y
CONFIG_BACKLIGHT_KTZ8866=y     ← 背光
CONFIG_ATH10K=y / ATH10K_SNOC=y
CONFIG_USB_CONFIGFS=y / CONFIG_USB_CONFIGFS_ACM=y
CONFIG_QCOM_PIL_INFO=y
# 关闭会污染性能/体积的：DEBUG_INFO, DEBUG_INFO_BTF
```

## 5.4 工具（`D:\TB331FCLinux\tools\`）

| 脚本 | 用途 |
|---|---|
| `mkv4.py` | 打包 boot / vendor_boot（Android v4 header） |
| `repack_vb_dtb2.py` | 只替换 vendor_boot 里的 DTB（末尾断言是 bug，镜像仍正确） |
| `verify_vb2.py` | 校验 vendor_boot（`dtb_size` 在 **0x834**） |
| `add_ktz8866.py` | 给 DTS 加 KTZ8866 节点 + 关闭面板 DCS 背光 |
| `build_ktz_dtb.sh` / `build_ktz_all.sh` | 编译并校验 DTB / 全量构建 |
| `parse_nvt_fw.py` | 离线解析 Novatek 固件头 |
| `alpine.ps1` / `tty.ps1` | 通过 COM3 执行命令 |
| `mk_initramfs_v16.sh` | 打包 initramfs |
| `fix_backlight2.py` 等 | 历史补丁脚本（可作参考） |

## 5.5 串口与调试

```powershell
# 执行一条命令
$env:ALPINE_CMD = 'uname -r'
$env:ALPINEWAIT = '8000'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\TB331FCLinux\tools\alpine.ps1
```

---

# 第六部分：判读速查表

| 日志 / 观测 | 含义 |
|---|---|
| `DSC enabled: 600x20 slices, 8 bpp` | 面板初始化完成 |
| `disp_cc_mdss_mdp_clk = 383000097` | DPU 时钟正常 |
| `disp_cc_mdss_mdp_clk = 19200000` + `failed to set core clock` | OPP 表有非法档位 |
| framebuffer `modifier=0x500000000000001` | 用了 UBWC（会花屏） |
| `ktz8866-backlight` 出现在 `/sys/class/backlight/` | 背光走对芯片了 |
| `dsi_err_worker: status=5` | DSI FIFO+TIMEOUT（命令与视频流冲突） |
| `dpu error enc32 frame done timeout` | DPU 帧超时（同上） |
| `Update firmware success!` + `fw_ver=0x0F` + `PID=6072` | 触控固件正确 |
| `PID=84D3/1D64/0000` + `FW info is broken` | 固件没加载 |
| `dlm: bin crc == golden` 但 `result` 不同 | 传输被打断（时机问题） |
| `bin crc != golden` | 固件头解析错（cascade 标志） |
| 约 5.3 s 回 fastboot | ABL 拒绝镜像（缺 `__symbols__`） |

---

# 第七部分：踩坑清单

| 坑 | 教训 |
|---|---|
| `0x16E36000`(384M) vs `0x16D41DC0`(383M) | 十六进制自己算一遍 |
| `head` 截断管道会杀掉 dtc | 重定向到文件再 grep |
| `repack_vb_dtb2.py` 末尾断言报错 | 是脚本 bug，用 `verify_vb2.py` 确认镜像 |
| `switch_root: not found` | 必须写 `/bin/busybox switch_root` |
| switchroot 后 `/dev/ttyGS0` 消失 | 要 `mount --move /sys/kernel/config` |
| `mount(2)` 返回 EFAULT | init 里用 fork+exec `busybox mount` |
| 面板 probe 里阻塞/defer | 会拖死整条探测链 |
| PowerShell 内联多行脚本 | 一律写成 `.ps1`/`.sh`/`.py` 文件 |
| niri 需要真实 VT 会话 | 由 tty1 getty 用 `-l niri-session` 启动 |
| 误以为背光走 DCS 0x51 | **实际是 KTZ8866**，查 Android 的 `ktz8866_leds` 日志才真相大白 |

---

# 第八部分：后续路线图

## 近期（1–2 周）

1. **迁移到 UFS**（第三部分）：先方案 C，再方案 A
2. initramfs 去掉对 SD 的硬依赖（带 SD fallback）
3. 背光默认值与曲线校准（对照 Android 的 `bkl_brightness_set` 值）
4. 触控 `touchscreen-inverted-*` 与 `abs_y_max=2000 vs 1920` 的坐标校准复核

## 中期

5. 电源管理：s2idle / 待机、亮度联动、CPU idle
6. 扬声器/耳机（AW883xx smartpa）、麦克风
7. 摄像头（若有主线驱动）、传感器（加速度/霍尔）
8. 充电与电量计（`bkl` 之外的 PMIC 子系统）

## 长期

9. 把全部改动整理成可提交上游的补丁集（panel / touch / DT）
10. 跟进主线 `sm6225`/`khaje` 支持（sm6225-mainline 组织）
11. 性能调优：DDR 频率、GPU 频率、zram、文件系统参数

---

# 附：一句话记住

**显示=383 MHz + 90 Hz + 0x11 前发 PPS；触控=固件在安静窗口下载 + cascade 从文件读；背光=KTZ8866 不是 DCS；启动=只在 B 槽刷 boot/vendor_boot，DTB 必须 `dtc -@`。根文件系统从 SD 迁到 `sda14` 即可脱离 SD。**
