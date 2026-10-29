<USER_REQUEST>
# TB331FC 主线 Linux 移植 —— 交接文档（给 Gemini）

> 本文所有数据均来自设备实测日志。README 式的总结在最后，问题定位过程在中间。请勿凭直觉推翻"已验证"章节。

---

# 一、项目与目标

把 **主线 Linux** 移植到 **联想小新 Pad 2024（TB331FC）**，最终目标是跑 **Niri 桌面环境**。

**当前状态：除触控坐标解析外，全部功能已打通。**

| 能力 | 状态 |
|---|---|
| 主线内核启动（ABL 放行） | ✅ |
| 原生 DSI 面板 1200×1920 @ **90Hz** + DSC + 背光 | ✅ |
| GPU（freedreno **FD610**，OpenGL 4.6 / GLES 3.2） | ✅ |
| **Niri 25.11 桌面，画面干净** | ✅ |
| 触控（Novatek NT36523N）：**10 点识别正常** | ✅ |
| 触控**坐标解析** | ❌ **唯一遗留问题** |
| WiFi（WCN3990 / ath10k_snoc） | ✅ |
| USB 串口控制台（COM3） | ✅ |
| 存储（UFS + SD 卡上的 ext4 镜像 loop 挂载） | ✅ |

---

# 二、硬件与关键参数

```
机型        Lenovo 小新Pad 2024 / TB331FC / 代号 p255、khaje
SoC         SM6225-AD（骁龙 685），8GB RAM / 128GB UFS
Bootloader  ABL（LinuxLoader.efi）
面板        INX p255_inx，1200×1920，DSC 压缩，背光 DCS 0x51（最大 3767）
触控        Novatek NT36523N，SPI（spi0.1），mode 0，10 MHz
            IRQ TLMM gpio80（sysfs 592），reset TLMM gpio86
WiFi        WCN3990（ath10k_snoc）→ wlan0
```

**面板时序（当前 90Hz，与厂商一致）**

```
hdisplay 1200, hfp 96, hbp 96, hpw 4    → htotal 1396
vdisplay 1920, vfp 56, vbp 248, vpw 2   → vtotal 2226
clock 279675 kHz → 90 Hz
实际读取：disp_cc_mdss_pclk0_clk = 119402784（DSC 压缩后的 pclk）
          disp_cc_mdss_byte0_clk = 89552087
          disp_cc_mdss_mdp_clk   = 383000097  ← 必须，见 3.1
```

**DSC（与厂商 DT 完全一致）**

```
DSC 1.1，bits_per_pixel 8，bits_per_component 8，line_buf_depth 9
slice_width 600，slice_height 20，slice_count 2，slice_per_pkt 2
block_prediction_enable
```

---

# 三、已彻底解决的问题（含证据与修法）

## 3.1 DPU 核心时钟被降频 → 条纹/蓝绿网格

**证据**：`disp_cc_mdss_mdp_clk = 19200000`（19.2 MHz），`[dpu error] failed to set core clock rate 200000000`。

**原因**：`drivers/clk/qcom/dispcc-sm6225.c` 的 `ftbl_disp_cc_mdss_mdp_clk_src` 实际是：

```c
F(19200000,  P_BI_TCXO,                    1,   0, 0),
F(200000000, P_GCC_DISP_GPLL0_DIV_CLK_SRC, 1.5, 0, 0),  // 需切父时钟 → -EINVAL
F(300000000, P_GCC_DISP_GPLL0_DIV_CLK_SRC, 1,   0, 0),  // 同上
F(383000000, P_DISP_CC_PLL0_OUT_MAIN,      2,   0, 0),  // ★ 唯一可靠（PLL0/2）
F(470000000, P_DISP_CC_PLL0_OUT_MAIN,      2,   0, 0),  // 错：与 383 同分频
F(560000000, P_DISP_CC_PLL0_OUT_MAIN,      2,   0, 0),  // 错
```

DT 的 DPU `opp-table` 里若有 200 MHz 档，`dpu_core_perf` 一选中就失败，**且失败后时钟跌到最低档 19.2 MHz → 带宽不足 → 条纹**。

**修法（只改 DTB）**：DPU `opp-table`（**phandle 0x72**）只保留一档：

```dts
opp-383000000 {
    opp-hz = <0x00 0x16d41dc0>;   /* 383000000；不是 0x16E36000(384M)！ */
    required-opps = <0x3a>;
};
```

**验证**：`disp_cc_mdss_mdp_clk = 383000097`，`failed to set core clock` 0 次。

## 3.2 SPI 走 PIO 抢 DPU 带宽 → "哪里有内容哪里就条纹"

**证据**：把触控驱动 unbind（无 SPI 访问）→ 条纹立刻消失；rebind → 回来。

**原因**：DT 里曾为让 SPI 控制器 probe 成功而删掉 `spi@4a80000` 的 `dmas`，导致 SPI 走 CPU PIO → 大量 AHB/互连访问 → DPU 取像素饥饿。

**修法**：恢复原厂 DTB 值（可从 `build/ref.dts` 查证）：

```dts
dmas = <0x46 0x00 0x00 0x01 0x46 0x01 0x00 0x01>;
dma-names = "tx", "rx";
```

## 3.3 UBWC 压缩缓冲导致花屏（niri 专用路径）

niri 曾用 `DRM_FORMAT_MOD_QCOM_COMPRESSED`（debugfs 抓到的 `modifier=0x500000000000001`），而 sm6225 从 sm6115 继承的 UBWC 参数不正确。

**修法**（`drivers/gpu/drm/msm/msm_mdss.c`）：给 sm6225 单独一份 mdss data，**不宣告 UBWC**（不设 `ubwc_enc_version`/`ubwc_dec_version`），`qcom,sm6225-mdss` 指向它。之后 niri 的 framebuffer 变为 `modifier=0x0`（线性），与能正常工作的控制台一致。

> 注意：`FD_MESA_DEBUG=noubwc` **无效** —— modifier 由合成器按 DRM 平面能力选，不归 Mesa 管。

## 3.4 ★ 触控固件从未真正写入（这是触控能用的前提）

**症状**：

```
ilm: bin crc = 0xF4FD5D35, golden = 0xF4FD5D35, result = 0xF4FD5D35   ✓
dlm: bin crc = 0x49618174, golden = 0x49618174, result = 0x2AD78BD2   ✗ 每次不同
nvt_read_pid: PID=84D3 / 1D64 / 0000（乱码）   + "FW info is broken"
```

`bin crc == golden` 但 `result`（芯片读回）不同 ⇒ **数据没落地**。

**真正的两个原因（重要，别再误判成"块太大"）**：

1. **`cascade_2nd_header_info` 被强制改成 0**（一次"经典路径"实验留下的）。必须恢复成从固件文件读：
   ```c
   cascade_2nd_header_info = (fwdata[0x20] & 0x02) >> 1;   /* 本固件 = 1 */
   ```
   否则固件解析错（`bin crc ≠ golden`、`PID=0000`）。
2. **下载时机太"吵"**：原来在 probe+2500ms（≈13s）执行，此时显示正在扫描、触控中断也在服务，SPI 传输被打断。现改为在**面板 sleep 窗口 + 触控 IRQ 关闭**时执行（见 3.5）。

**`NVT_TRANSFER_LEN` 与块大小无关**：厂商原始 `(63*1024)` **可以正常工作**（实测 `Update firmware success! <311895 us>`），当前已恢复厂商默认值。历史上改成 4KB/8KB 只是"碰巧"在吵的环境下也能过，属于掩盖而非根因。

**正确后的日志（与 Android 完全一致）**：

```
nvt_update_firmware: Update firmware success! <311895 us>
nvt_get_fw_info:     fw_ver=0x0F, fw_type=0x01, x_num=32, y_num=48
nvt_read_pid:        PID=6072
```

> `PID` 是从**事件缓冲区**读的，所以 PID 乱码是"无固件"的**症状**，不是寻址错误。

## 3.5 显示与触控固件下载的时序（采用主线 NT36523 参考实现）

参考实现（Jianhua Lu / sm8150-mainline、sm8250-mainline elish、`novatek-nvt-ts as panel follower` 补丁）的关键点：**`0x29`（display on）在 `enable()` 里、触控固件下载之后才发**，这样下载时面板还在 sleep，不会干扰任何正在显示的内容。

我们的实现（三处改动）：

1. `lenovo_p255_inx_init()`：DSC 面板走到 `0x11` 之前 + 发 PPS 后 **return**，不再发 `0x11`/`0x29`
2. `hx83102_enable()`：等 `nvt_fw_ready` → 调 `nvt_ts_panel_event(true)`（同步下载，面板仍 sleep）→ 发 `0x11` + 120ms + `0x29` → 最后开背光
3. `nt36523_ts.c`：**删除** probe 里 2500ms 的延迟下载工作；probe 结束时置 `nvt_fw_ready = true`

**结果**：内核日志/fbcon 阶段条纹完全消失。

## 3.6 ★ 面板必须跑 90Hz（最后一击）

**证据链**：

1. 用 `niri msg action screenshot-screen` 截图 → **合成的帧完全干净** ⇒ 损坏发生在扫描输出侧，与 GPU/合成无关
2. 用户用 CPU 软件渲染也是同样条纹 ⇒ 排除 GPU 缓存一致性
3. 对比厂商 overlay DT（`build/ov0.dts`）：**这个面板节点只有 `framerate = 0x5a`（90Hz）一种配置**

**原因**：DSC 的 `slice_height = 20` 是按 90Hz 帧结构设计的；跑 60Hz 时面板 DSC 解码器在高频内容（文字）上失步 → **"哪里有内容哪里就条纹"**，纯色区域正常。

**修法**：`.clock = 186473`（60Hz）→ **`279675`（90Hz）**。

**结果**：显示完美，条纹彻底消失。

---

# 四、当前唯一遗留问题：触控坐标解析错误

## 4.1 现象

- **触控功能正常**：单指到 10 指全部识别（驱动 `cnt` 从 1 报到 10；evtest 看到 `ABS_MT_SLOT` 0..9）
- **坐标错误**：niri 里点击位置不对，光标被甩到画面外

## 4.2 实测数据

设备注册范围：

```
ABS_MT_POSITION_X: Min 0, Max 1199   ✓ 与面板宽度一致
ABS_MT_POSITION_Y: Min 0, Max 1999   ⚠ 面板高度是 1920（固件 abs_y_max=2000）
```

一次"点四个角"的标定记录（`evtest` 输出）：

```
ABS_MT_POSITION_X value -10370      ← 负坐标！
ABS_MT_POSITION_Y value -16980
ABS_MT_POSITION_X value -10416
...（成串出现，期间夹着正常值 820 / 1520 / 1760 / 1778 / 300）
```

统计：**15 次 X 事件里 12 次越界（含负数）**，8 次 Y 越界。

## 4.3 根因

驱动解析代码（`drivers/input/touchscreen/nt36523_ts.c`，约 1130 行）：

```c
position = 1 + 6 * i;                     /* 每点 6 字节 */
input_id = (uint8_t)(point_data[position + 0] >> 3);
status   = point_data[position + 0] & 0x07;
if (status == 0x01 || status == 0x02) {
    input_x = (uint32_t)((point_data[position + 1] << 8) | point_data[position + 2]);  /* 大端 16 位 */
    input_y = (uint32_t)((point_data[position + 3] << 8) | point_data[position + 4]);
    input_w = (uint32_t)(point_data[position + 5]);
    ...
    touchscreen_report_pos(ts->input_dev, &ts->props_ts, input_x, input_y, true);
```

⚠ **两个放大问题的因素**：

1. 报文布局（header 位域 `id=>>3` / `status=&0x07`、坐标大端、步长 6）是**按某版固件写的**，与设备上实际固件 `fw_ver = 0x0F` 的布局可能不一致 → 大部分点解析成垃圾
2. DT 的触控节点带 **`touchscreen-inverted-x` / `touchscreen-inverted-y`**（从厂商节点原样搬来），`touchscreen_report_pos()` 里会算 `x = max_x - x`，垃圾值下溢 → 变成巨大的负数

## 4.4 建议修法（按优先级）

### 方案 A（推荐，彻底）：反推实际报文布局

1. 在驱动里临时加一行，把**每个被接受报文**的前 40 字节 dump 出来（`print_hex_dump` 或 `%*ph`）
2. 让用户点**已知位置**（如画面左上角、右下角、正中心），每个位置停 1 秒
3. 对比字节变化 → 定出真正的 `id/status` 位置、X/Y 的两个字节及其大小端
4. 按实际布局改解析

驱动里已有一个可参考的 dump 格式（在拒包路径上）：

```c
NVT_LOG("pkt rejected, raw: %*ph\n", 10, point_data + 1);
```

### 方案 B（临时可用）：范围校验 + 关闭 inversion

- 在 `status` 判断之后加范围检查，`input_x > 1200 || input_y > 1920` 就跳过该点
- 同时**删掉 DT 里的 `touchscreen-inverted-x` / `touchscreen-inverted-y`**（先确认是否需要反转，面板是 `orientation = 180`）

代价：触摸会丢点、不跟手 —— 只适合先让 GUI 能用。

### 顺带要修的

- `abs_y_max` 实际为 **2000**，面板高度 **1920** → 纵向会被压缩约 4%。应在驱动 probe 里覆盖成 1920（或改 DT）。

---

# 五、已排除的方向（避免重复劳动）

| 猜过 | 结论 |
|---|---|
| 固件下载必然干扰显示 | ❌ 厂商在显示亮着时下载（169 ms）毫无影响 |
| 触控把显示寄存器当触控寄存器用 | ❌ 固件目标区 0x01F400~0x02BF37 与触控 EVENT_BUF(0x2FD00)/寄存器(0x3F1xx) **不相交** |
| 显示寄存器编程错误 | ❌ 不写固件时显示完美 |
| mem_map 选错（NT36523N vs NT36523） | ❌ 两者仅 `EVENT_BUF_ADDR` 差 0x100，固件地址相同 |
| 强制走非 cascade 固件路径 | ❌ 更糟（PID=0000、golden CRC 对不上） |
| 只在 enable 后发 4 条 restore 命令 | ❌ 不足以恢复触控 |
| 面板 probe 里 `msleep` 等触控就绪 | ❌ 把触控 probe 堵到 28.9s，等待必然超时 |
| 面板 probe 里 `-EPROBE_DEFER` | ❌ 面板与触控互相卡死，都不 probe |
| 在 `prepare()`（DSI 初始化之前）下载固件 | ❌ 触控仍失效 |
| `FD_MESA_DEBUG=noubwc` | ❌ 不影响合成器选的 modifier |
| 降 SPI 频率到 5MHz | ❌ 更糟（PID=0000、中断风暴） |
| `novatek,spi-rd-fast-addr` | ❌ 厂商明确不支持，必须删 |
| 分块 63KB→4KB | ❌ 非必需（是"吵的环境"掩盖） |

---

# 六、原厂基准数据（Android A 槽取证）

```bash
fastboot --set-active=a && fastboot reboot     # 约 50s 到 adb
adb shell "dmesg | grep -iE 'nvt|novatek'"
adb pull /vendor/firmware/ D:\TB331FCLinux\firmware\vendor-firmware\
```

```
驱动模块      nvt36523_spi.ko
面板名        [nt36523n video mode dsi inx panel]
SPI           mode=0, max_speed_hz=10000000
trim 流程     先试 0x1fb104（全 0xFF 失败）→ 再试 0x03f004（成功）
              然后 "set reg chip_ver_trim_addr=0x03f004,
                          swrst_sif_addr=0x03f0fe, crc_err_flag_addr=0x03f135"
固件下载      Update firmware success! <169032 us>
固件信息      fw_ver=0x0F, fw_type=0x01, PID=0x6072
```

**固件文件 `novatek_ts_fw.bin`（196608 字节）解析**（可用 `tools/parse_nvt_fw.py` 复现）：

```
ILM: BIN 0x000200 → SRAM 0x000000, size 0x1985F
DLM: BIN 0x021400 → SRAM 0x01F400, size 0xCB37   (0x01F400~0x02BF37)
crc: 0x18 = 0xF4FD5D35 (ILM), 0x1C = 0x49618174 (DLM)
flags: 0x20 = 0x03 → cascade_2nd_header_info = 1
尾部 0x2FFF0 三个附加分区全 0（末 3 字节 "NVT" 魔数）
```

**厂商面板节点参数（`build/ov0.dts`，关键是只有 90Hz）**：

```
panel-type        dsi_video_mode
panel-orientation 180
framerate         0x5a = 90 Hz
width/height      0x4b0 / 0x780 = 1200 / 1920
DSC               bpp 8, bpc 8, slice 600x20, slice-per-pkt 2, version 0x11, scr-version 0
```

---

# 七、启动架构与当前镜像

```
ABL → boot_b(kernel Image) → vendor_boot_b
       ├─ vendor_ramdisk = initramfs（init + busybox + gadget.sh + switchroot.sh + 固件）
       ├─ dtb            = CANONICAL_383_dma.dtb（在 0x30f000）
       └─ cmdline        = console=ttyGS0 keep_bootcon ignore_loglevel clk_ignore_unused
                           pd_ignore_unused rdinit=/init earlycon=qcom_geni,0x4a90000
                           androidboot.hardware=qcom panic=10
       ↓
   init: 挂 proc/sys/dev/tmp → 早期建 USB CDC-ACM gadget → 挂 FAT32 SD(mmblk0p1)
       → losetup alpine-rootfs.img → mount ext4 → 迁移 /proc /sys /dev /sys/kernel/config
       → busybox switch_root /newroot /sbin/init
       ↓
   Alpine OpenRC → getty on ttyGS0（root 空密码）→ niri 在 tty1 自启
```

**根文件系统**：Alpine 3.24 装在 **SD 卡 FAT32 分区上的 `alpine-rootfs.img`**（2 GB ext4，用 `mke2fs -d` 生成）。不用重分区，Windows 可直接替换。

| 分区 | 当前镜像 | 说明 |
|---|---|---|
| `boot_b` | `build\boot_63k.img` | **当前运行**：90Hz + 63KB 分块 + follower 时序 + IRQ 静默 + cascade 正确 |
| `vendor_boot_b` | `build\vb_spidma.img` | 单档 383MHz OPP + SPI DMA + 仅 ACM gadget |

其他镜像：`boot_nofw.img`（不下载固件，显示干净、无触控，可作诊断基线）、`boot_follow.img`、`boot_90hz.img`。

---

# 八、代码改动清单

| 文件 | 改动 |
|---|---|
| `drivers/gpu/drm/msm/msm_mdss.c` | 新增 `sm6225_data`（不宣告 UBWC），`qcom,sm6225-mdss` 指向它 |
| `drivers/gpu/drm/panel/panel-himax-hx83102.c` | ① DSC + **在 0x11 之前发标准 PPS**（缺了必花屏）② `rails_kept_on`（`unprepare()` 不关电）③ `lenovo_p255_inx_init()` 在 0x11 前返回 ④ `enable()`：等触控就绪 → 下载固件 → 发 0x11/0x29 → 开背光 ⑤ **`.clock = 279675`（90Hz）** |
| `drivers/input/touchscreen/nt36523_ts.c` | 厂商修复补丁（INT 监视/WDT/日志）；`nvt_ts_panel_event()` 同步执行；`nvt_irq_enable()` 非 static；删除 probe 内 2500ms 下载工作；probe 末尾置 `nvt_fw_ready` |
| `drivers/input/touchscreen/nt36523_fw_update.c` | `bool nvt_fw_ready` + EXPORT；下载前后 `nvt_irq_enable(false/true)`；`cascade_2nd_header_info` 从文件读 |
| `drivers/input/touchscreen/nt36523.h` | `NVT_TRANSFER_LEN` 保持厂商默认 `(63*1024)` |
| `.config` | `TOUCHSCREEN_NT36523_SPI=y`、`SPI_QCOM_GENI=y`、`BACKLIGHT_PWM=y`、VBAT/MSDOS/EXFAT=y、USB_CONFIGFS(+ACM)=y、`ATH10K_DEBUG/DEBUGFS=y`、`QCOM_PIL_INFO`、禁 DEBUG_INFO/BTF |

**DTB 改动（`build/CANONICAL_383_dma.dts`）**：DPU OPP 单档 383M、SPI 恢复 `dmas`、`touchscreen@1`(novatek) okay / `touchscreen@0`(himax) disabled、aliases `/soc@0/`→`/soc/`、蓝牙供电、`serial@4a8c000` pinctrl、glink IPCRTR、保留 `abl-stubs`。

**编译必须 `dtc -@`**（生成 120 个 `__symbols__`，否则 ABL 约 5.3s 退回 fastboot）。

---

# 九、环境、工具与命令

```
内核源码   ~/kbuild/linux-next-tb128fu-hx83102-panel-port   (WSL Ubuntu 24.04)
           6.14.0-rc5-next-20250306，源自 TB128FU 的 linux-next 分支
编译       make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j10 Image   (~2-4 分钟)
打包       python tools\mkv4.py --mode boot --kernel <Image> --out <img>
           python tools\mkv4.py --mode vendor_boot --vendor-ramdisk <cpio> --dtb <dtb> --cmdline "<...>" --out <img>
换 DTB     python tools\repack_vb_dtb2.py <in_vb> <new.dtb> <out_vb>
校验       python tools\verify_vb2.py <vb.img>     # dtb_size 在 0x834
刷机       D:\搞机助手\fastboot.exe
串口       powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\TB331FCLinux\tools\tty.ps1
Alpine 交互 powershell.exe ... -File D:\TB331FCLinux\tools\alpine.ps1   ($env:ALPINE_CMD)
```

**常用工具**：`parse_nvt_fw.py`（解析固件头）、`make_383_dts.py`、`add_spi_dmas.py`、`strip_rndis.py`、`mk_initramfs_v16.sh`、`fetch_apks.sh`（清华镜像下 aarch64 包）、`transfer_apks2.ps1`

**关键操作**：

- 进 fastboot：**电源 + 音量下**（`reboot bootloader` 无效）
- 回 Android：`fastboot --set-active=a` + reboot
- 设备跑 Alpine 时可从串口 `reboot`，然后按住按键进 fastboot
- 读屏幕文字：`chvt 2`（niri 在 tty1）
- niri 截图：`mkdir -p /root/Pictures/Screenshots` + `niri msg action screenshot-screen`（需要 `NIRI_SOCKET=/run/user/0/niri.wayland-1.*.sock`）
- 从 Android 取 SD 卡文件：`mount -t vfat /dev/block/mmcblk1p1 /mnt/sdx` 然后 `adb pull`

---

# 十、判读速查表

| 日志 / 观测 | 含义 |
|---|---|
| `DSC enabled: 600x20 slices, 8 bpp` | 面板初始化完成 |
| `disp_cc_mdss_mdp_clk = 383000097` | DPU 时钟正常 |
| `19200000` + `failed to set core clock` | OPP 表里有 dispcc 不支持的档位 |
| framebuffer `modifier=0x500000000000001` | 用了 UBWC |
| framebuffer `modifier=0x0` + stride 4864 | 线性，正常 |
| `Update firmware success!` + `fw_ver=0x0F` + `PID=6072` | **触控固件加载正确** |
| `PID=84D3/1D64/0000` + `FW info is broken` | 固件没加载（症状，不是寻址错） |
| `dlm: bin crc == golden` 但 `result` 不同 | 传输被打断（时机/中断交织） |
| `bin crc != golden` | 固件文件头解析错（cascade 标志被改） |
| `nvt_restore_cmd_func++` | 面板 enable 时的触控重新武装 |
| 约 5.3s 回 fastboot | ABL 拒绝镜像（`__symbols__` 缺失/DTB 非法） |
| `ABS_MT_POSITION_* value -xxxxx` | **触摸报文布局不匹配**（当前问题） |

---

# 十一、铁律与踩坑

**铁律**

1. **绝不写 A 槽**（原厂 Android，唯一回退路径）。只刷 slot B。
2. 改 DTB 后必须 `dtc -@`。
3. 改内核后先 `ls -l arch/arm64/boot/Image` 确认时间戳，再打包刷机（多次因 make 静默失败刷了不存在的文件而误判）。

**踩过的坑**

| 坑 | 教训 |
|---|---|
| `0x16E36000`(384M) vs `0x16D41DC0`(383M) | 十六进制自己算一遍 |
| `switch_root: not found` → panic | initramfs 里必须写 `/bin/busybox switch_root` |
| switchroot 后 `/dev/ttyGS0` 消失 | configfs 是 `/sys` 子挂载，要显式 `mount --move /sys/kernel/config` |
| `mount(2)` 返回 EFAULT | init 里改用 `fork+exec busybox mount` |
| Alpine 侧再建 gadget | 抢 UDC → USB 反复重枚举；gadget 只由 initramfs 建 |
| 面板 probe 里阻塞/defer | 会拖死整条探测链 |
| PowerShell 内联多行脚本 | 一律写成 `.ps1`/`.sh`/`.py` 文件 |
| `repack_vb_dtb2.py` 末尾断言 | 是 bug，镜像已正确写出；用 `verify_vb2.py` 校验 |
| niri 需要真实 VT 会话 | 必须由 tty1 的 getty 用 `-l /usr/local/bin/niri-session` 启动 |

---

# 十二、下一步（给接手的 AI 的建议顺序）

1. **修触控坐标（最高优先）**
   - 在 `nvt_ts_work_func` 的解析循环里加临时 dump（报文前 40 字节）
   - 让用户点**左上/中心/右下**三个已知点，每个停 1 秒
   - 从字节变化反推：`id/status` 位域、X/Y 的字节位置与大小端、每点步长
   - 改解析代码 → 验证 10 指 + 四点标定
2. **修 `abs_y_max`**：固件报 2000，面板 1920 → 在 probe 里覆盖成 1920
3. **确认 `touchscreen-inverted-x/y` 是否必要**（面板 `orientation=180`），必要时保留并用正确坐标测试
4. 打磨：开机时间（目前面板要等触控就绪，约 60-70s 才出图，可优化等待策略）、90Hz 下的功耗、Niri 常用配置（foot 已装、可选 waybar）
5. 最后把内核改动整理成可审计的补丁集

---

# 十三、一句话总结

**显示（1200×1920@90Hz + DSC）、GPU、Niri、WiFi、USB 串口、10 点触控全部打通；唯一剩下的是触控"坐标解析布局"与固件版本不匹配 —— 用一次报文 dump + 三点标定即可彻底解决。**现在是触摸坐标问题
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-10-26T19:35:16+08:00.
</ADDITIONAL_METADATA>