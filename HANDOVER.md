# 交接文档 —— TB331FC 主线 Linux 移植现状

> 给接手的人（或 AI）：这份文档列出**已完成的、已验证的、被排除的、以及下一步该怎么查**。
> 请先读完本文件再动手，能省掉大量重复排查。
> 完整细节见 `docs/PORTING-NOTES.zh-CN.md`（约 2250 行）。

---

## 1. 硬件与目标

| 项目 | 值 |
|---|---|
| 设备 | Lenovo TB331FC（小新 Pad 2024） |
| SoC | Qualcomm **SM6225-AD**（骁龙 685，`khaje`） |
| 面板 | INX `p255_inx`，1200×1920，原生 90Hz，**DSC 压缩**，DCS 背光 |
| 触控 | Novatek **NT36523**，走 **SPI**（`spi0.1`），PID `0x84D3` |
| 无线 | WCN3990 级别（WiFi=ath10k_snoc，BT=hci_qca over UART） |
| 存储 | UFS，A/B 双槽，65 分区 |

**铁律：只写 B 槽，A 槽（原厂 Android）全程不动**，随时 `fastboot --set-active=a` 回滚。

---

## 2. 已验证可用 ✅

| 功能 | 备注 |
|---|---|
| 主线内核启动 | 6.14.0-rc5-next-20250306，基线是 tb128fu 的 mainline 移植项目 |
| 显示 | 1200×1920 @60Hz，DSC，画面正确 |
| 背光 | DCS，0–3767 可调，实测有效 |
| GPU | freedreno FD610，GL 4.6 / GLES 3.2 |
| 桌面 | Niri 正常 |
| USB 串口控制台 | CDC-ACM gadget → 电脑 COM3（115200 8N1） |
| SD 卡 | 热插拔正常（`cd-gpios` 极性已修） |
| ADSP 协处理器 | `running`（见第 5.4 节技巧） |
| QRTR / IPCRTR | 本轮刚打通（见第 5.6 节） |

**根文件系统**：SD 卡上的 2GB ext4 镜像文件 `alpine-rootfs.img`，
initramfs 里 losetup 挂载后 switch_root。root 密码为空，getty 在 `ttyGS0`。

---

## 3. 三个未解决问题

### 3.1 触控：DLM 段写入后回读 CRC 永不一致

```
ilm:  bin crc = 0xF4FD5D35  golden = 0xF4FD5D35  result = 0xF4FD5D35   ✅
dlm:  bin crc = 0x49618174  golden = 0x49618174  result = 每次不同        ❌
```

**已排除**（不要重复）：
- SPI 传输可靠性：连读 20 次 PID 完全一致（`A493`/`84D3`），自检通过
- 芯片识别：trim ID `17 20 00 23 65 03` 精确命中主线 `trim_id_table[]` 的
  `{0xFF,0xFF,0xFF,0x23,0x65,0x03}` → NT36523 映射正确
- 传输块大小：`NVT_TRANSFER_LEN` 从 63KB 改到 4KB 都失败
- SPI 频率、DMA、`spi-rd-fast-addr`、4 个原厂固件变体

**最需要**：**Novatek SPI 版厂商驱动源码**，逐行对比 `nvt_write_sram()` /
`nvt_set_page()` 与 DLM 写入前后的额外命令。
⚠️ TB128FU 的厂商内核是 **I2C 版**（`nova_36525_mmi/nt36xxx*.c`），**不能直接用**。

### 3.2 WiFi：`ath10k_snoc` 静默卡在等 WLFW 服务

现象：probe 只打印一行 `Adding to iommu group 7`，之后**没有任何日志**，
无 wiphy、无接口。设备已绑定驱动、未进入 deferred 列表。

**已排除**（不要重复）：
- 固件缺失：`/lib/firmware/qcom/wlanmdsp.mbn` + `/lib/firmware/lenovo-tb128fu/bdwlan.*` 都在
- 供电：`vdd-0.8-cx-mx`→l8、`vdd-1.8-xo`→l16、`vdd-1.3-rfa`→l17、`vdd-3.3-ch0`→l23，
  与厂商 DT **完全一致**；实测电压 l8=640mV l9=1800 l16=1800 l17=1304 l23=3200，
  与 Android 实测逐项相同
- MSA 保留内存：`memory-region` 指向 `0x51900000`/1MB，与 Android **完全相同**
- ADSP：已 `running`
- QRTR：IPCRTR 通道已建立并绑定 `qcom_smd_qrtr`
- CDSP：起不来（`-22 initializing firmware`），但**对 WiFi 不是必需**

**关键差异**（重点）：
```
Android:  icnss2 probe → 用户态 qcacld 用 PIL 把 wlanmdsp.mbn 载入 MSA
          → 约 24 秒后 "QMI Server Connected" → "WLAN FW is ready"
主线   :  ath10k_qmi 先等 WLFW QMI 服务 → 再通过 QMI 推送固件
```
**顺序相反**。需要搞清楚：这颗芯片的 WLFW 服务是由
(a) 芯片 ROM 提供、(b) ADSP 转发、还是 (c) 必须先 PIL 载固件才有。

**下一步（已准备好工具）**：
1. `tools/build_ath_debug.sh` —— 重编内核打开 `CONFIG_ATH10K_DEBUG`
   （`ATH10K=y`，只影响 Image，不用重装模块）
2. 刷入后执行 `tools/test_ath_debug.ps1`：
   ```
   echo 0xffffffff > /sys/module/ath10k_core/parameters/debug_mask
   rmmod ath10k_snoc; modprobe ath10k_snoc
   ```
   日志会明确指出卡在 QMI 的哪一步
3. 另外可选：用 QRTR 客户端列出总线上的服务（`tools/qrtr_lookup.py`，
   但**设备上没有 python3**，需要交叉编译或装 python）

### 3.3 蓝牙：芯片对 `0xFC00` 无应答

现象：`hci0` 已创建、serdev 已绑定，但每个命令都 `command 0xfc00 tx timeout`。

**已排除**（不要重复）：
- UART 实例：`4a8c000`，与 Android 的 `4a8c000.qcom,qup_uart` 一致
- 引脚：gpio8/9/10 都是 `function qup3`，与 Android 一致
  （⚠️ 唯一差异：Android 上 gpio11 保持 `gpio` 功能，我们 mux 成了 qup3/RTS；
  但只 mux 8/9 的版本也失败，所以不是这个原因）
- 别名：`serial1` 已加，`Invalid line -19` 已修（根因是别名路径写成
  `/soc@0/` 而真实是 `/soc/`）
- 供电：4 路稳压器全部 `enabled`，映射与电压见 3.2
- GPIO 87（厂商的 `qca,bt-sw-ctrl-gpio`）：Android 上是 `in high`（输入），
  我们未使用 → **它是状态反馈脚，不是使能脚**

**下一步**：
- 用示波器/逻辑分析仪看 UART 波形（主机 TX 有没有发出去、芯片 RX 有没有回应）
- 对比 Android 的 **geni UART 寄存器配置**（Linux 侧没有调试手段）
- 注意一个强假设：**WiFi 和蓝牙共用同一颗芯片，如果芯片整体没起来，
  两个都会失败** —— 先修 WiFi 再回头看蓝牙可能更省力

---

## 4. 可用的设备操作方式

```powershell
# 串口执行命令
$env:ALPINE_CMD = 'command'
$env:ALPINEWAIT = '20000'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\TB331FCLinux\tools\alpine.ps1

# 进 fastboot：重启时按住 电源+音量下，然后
D:\搞机助手\fastboot.exe --set-active=b
D:\搞机助手\fastboot.exe flash vendor_boot_b <img>
D:\搞机助手\fastboot.exe reboot

# 回滚到 Android
fastboot --set-active=a && fastboot reboot
```

**当前镜像**：
- `boot_b` = `build/boot_wifi2.img`（内核，含全部 5 个补丁）
- `vendor_boot_b` = `build/vb_qrtr.img`（DNB + initramfs，**含 IPCRTR 修正**）
- 备份：`build/WORKING_boot_b.img` / `build/WORKING_vendor_boot_b.img`

**固件资产**（SD 卡 `fwtest/`）：
```
wifi/           wlanmdsp.mbn + 34 个 bdwlan.*
bt/             crbtfw21.tlv, crnv21.bin
dsp/            adsp.mdt + 35 分片, cdsp.mdt + 10 分片
modules-6.14.tar.gz   676 个 .ko
```

---

## 5. 关键发现（都是踩过坑换来的，别再走一遍）

### 5.1 ABL 需要 `__symbols__` stub
TB331FC 的 ABL 会应用 vendor overlay，overlay 引用 base DTB 的 `__symbols__`。
纯主线 DTB 没有 → overlay 失败 → ABL 拒绝启动（fastboot 卡 5 秒后重启）。
解法：加一个 `abl-stubs` 子树塞进约 120 个空标签节点，用 `dtc -@` 编译。

### 5.2 显示花屏 = DPU 核心时钟掉到 19.2 MHz
DT 的 OPP 写 200/300/383/470/560 MHz，而 dispcc 只支持
**19.2/192/256/307.2/384 MHz** → `clk_set_rate` 返回 `-EINVAL` → 时钟掉最低档
→ 带不动全屏刷新 → 满屏蓝绿网格。
**解法：DPU 的 OPP 表只留 384 MHz 一档**（`0x16e36000`）。

### 5.3 DSC 面板必须由 host 下发标准 PPS
只写面板初始化寄存器不够。必须在 `0x11`(sleep out) **之前**调用
`drm_dsc_pps_payload_pack()` + `mipi_dsi_picture_parameter_set()` +
`mipi_dsi_compression_mode_ext()`。缺这步怎么调 slice 都花屏。

### 5.4 ADSP：把 `.mdt` 符号链接成 `.mbn`
DT 写 `firmware-name = ".../adsp.mbn"`，厂商给的是分片（`adsp.mdt` + `adsp.bNN`），
主线 `qcom_q6v5_pas` **不会自动回退**。因为 `.mdt` 本身就是 ELF 头 + 分片索引：
```sh
ln -sf adsp.mdt adsp.mbn
echo start > /sys/class/remoteproc/remoteproc1/state   # 不用重启
```
⚠️ **不要自己把分片合成单文件 `.mbn`** —— SCM 安全校验依赖原始 phdr 布局，
重写 p_offset 会 `-22 initializing firmware`（`tools/pil_squasher.py` 仅作参考）。
⚠️ 分片命名是**十进制** phdr 索引（phdr[16] → `b16`，不是 `b10`）。

### 5.5 CDSP 起不来
`-22 initializing firmware`（squashed）或 `-22 reading firmware metadata`（分片）。
对 WiFi 不是必需，暂不处理。

### 5.6 DTB 缺 IPCRTR glink 通道（本轮关键发现）
```
厂商 DTB: adsp / cdsp / modem 三处都有 qcom,glink-channels = "IPCRTR"
原 DTB : 完全没有
```
缺失后果：QRTR 无传输端点 → 所有 QMI 客户端拿不到服务 →
`ath10k_snoc` 无限等待且不打日志。
解法：`tools/add_ipcrtr_channels.py`，给每个带 `qcom,remote-pid` 的
glink-edge **末尾**追加：
```dts
qcom,adsp_qrtr {
    qcom,glink-channels = "IPCRTR";
    qcom,intents = <0x800 0x05 0x2000 0x03 0x4400 0x02>;
    qcom,no-wake-svc = <0x190>;
};
```
⚠️ 坑 1：DTS 要求**属性必须在子节点之前**，插在中间会
`FATAL ERROR: Unable to parse input tree`。
⚠️ 坑 2：加载顺序必须是 `modprobe qrtr; modprobe qrtr-smd;` **再**启动 ADSP；
反过来 QRTR 拿不到通道。

### 5.7 其他坑
- `mount(2)` 在 initramfs 里返回 EFAULT → 改用 fork+exec `busybox mount`
- `switch_root` 必须写成 `busybox switch_root`（裸调用找不到）
- 必须禁用 BT 的 USB 传输（`BT_HCIBTUSB` 等），否则 modpost 报未定义符号
- 改配置后必须**先 `make Image` 再 `make modules`**，否则 Module.symvers 缺内置符号
- `ATH10K_SNOC` 只能 `=m`（依赖的 `QCOM_RPROC_COMMON` 是隐藏符号）
- 检查 DTS 节点是否存在**不要用依赖缩进的 awk 正则**，用 Python 大括号配对

---

## 6. 代码/文件位置

```
release/                       ← 开源仓库（可直接推到 GitHub）
├── README.md                  项目介绍（中英）
├── patches/                   5 个内核补丁（已验证可干净应用）
├── dtb/CANONICAL.dts          当前唯一权威设备树（含全部修复）
├── dtb/*.py                   每个修复一个脚本
├── initramfs/                 自写 init(C) + gadget.sh + switchroot.sh
├── tools/                     构建、固件提取、qrtr 查询、squasher 等
├── docs/PORTING-NOTES.zh-CN.md  完整移植笔记（2250 行，中文）
├── docs/FIRMWARE.md           固件提取指南（不含任何二进制）
└── prebuilt/                  预编译镜像 + 一键刷机脚本 + SHA256

WORKING-BOOT-RECIPE.md        ← 同一份笔记的工作副本
tools/                         ← 实际使用的脚本（143 个）
build/CANONICAL.dts           ← 权威 DTS 工作副本
```

**内核源码树**（WSL）：`~/kbuild/linux-next-tb128fu-hx83102-panel-port`
基线 zip：`C:\Users\Pluto\Desktop\linux-next-tb128fu-hx83102-panel-port.zip`

---

## 7. 建议的优先级

1. **WiFi**：按 3.2 的下一步重编内核开 `ATH10K_DEBUG`，读日志定位 QMI 卡点。
   这是唯一能直接看到失败原因的手段。
2. **蓝牙**：如果 WiFi 修好后蓝牙仍不行，再上示波器/寄存器对比。
   （共用芯片假设：芯片整体没起来时两个都会失败）
3. **触控**：找 Novatek SPI 版厂商驱动，否则难有突破。
4. **90Hz**：面板原生支持，属于最后锦上添花。
