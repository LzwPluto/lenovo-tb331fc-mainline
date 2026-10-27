# TB331FC (小新 Pad 2024 / khaje / SM6225-AD) Mainline 移植：对 Gemini 结论的复核与修正

> 本文全部结论来自**本机实测**：设备当前就在 fastboot（`HA274M8X`，`current-slot:b`，`slot-successful:a:yes`，A 槽完好）；
> 依据的二进制为 `D:\TB331FC_GSI_Kit\LinuxLoader.efi`（970,768 B，PE32+ AArch64，ImageBase=0，**RVA 与文件偏移 1:1**）。
> 标注：**✓ 实测/反汇编确认** · **⊘ 已证伪** · **? 推断，需实验**
> 全文**未写入任何分区**，A 槽未被触碰。

---

## 0. 一句话结论

**Gemini 的四个关键前提里有三个是错的**，而它为"retry count 不减"给出的整个推理链（"所以 ABL 在内核跳转之前就崩了"）在代码层面**不成立**——ABL 里有一条专门的 `A/B retry count NOT decremented` 分支，说明"不减"是一个**设计内的正常分支**，不能用它反推执行流位置。

真正卡住项目的不是"Header v2 vs v4"，而是**没有观测手段**。在拿到第一行日志前，任何关于"死在 DTB 匹配 / 解压 / 内存越界"的判断都只是猜。所以本文第 6 节给了一个**零成本、零刷写**的判定实验，能在 2 分钟内把问题空间砍掉一半。

---

## 1. 先纠正：四个必须放弃的前提

### ⊘ 前提 1：「TB331FC 的 ABL 对 Header v2 有隐式硬限制，强制要求 vendor_boot」

**反证（反汇编，`UpdateBootParamsSizeAndCmdLine` = 0x8BB0，由 `BootLinux` 在 0x7160 调用，返回错误即致命）：**

```
0x8cb8:  ldr  w8, [x8,#0x458]      ; w8 = header_version
0x8cbc:  subs w8, w8, #3
0x8cc0:  b.ne #0x8ffc              ; != 3 -> 0x8ffc
          ;  ==3 分支：FindImage("vendor_boot")，失败 -> "Failed to find vendor_boot image"
0x8ffc:  ldr  w8, [x8,#0x458]
0x9004:  subs w8, w8, #4
0x9008:  b.ne #0x9344              ; != 4 -> 0x9344  ← ★ Header v2 走这里
          ;  ==4 分支：FindImage("vendor_boot")，失败 -> "vendor_boot image header not found"
0x9344:  b #0x9348
0x934c:  bl #0xff20                ; 直接去拼 cmdline，失败 -> "Failed to cat cmdline"
```

**v2 路径既不查 vendor_boot、也不查 recovery、也不查 init_boot，直接跳到拼 cmdline。** 所以"因为分区表里有 `init_boot_b / vendor_boot_b` 所以触发完整性检查"这个猜想是**错的**。

其余所有读 `header_version`（结构内偏移 `+0x458`）和那个标志字节（`+0x45c`）的地方，我也全二进制扫了一遍（共 30 处），另有两处形如：

```
0x1cd3c:  ldrb w8, [x19,#0x45c] ; cbz w8, skip
0x1cd44:  ldr  w8, [x19,#0x458] ; cmp w8,#4 ; b.lo skip   ; 只在 >=4 时多做一步
0x1e7e8:  ldrb w8, [x20,#0x45c] ; cbz w8, skip
0x1e7f0:  ldr  w8, [x20,#0x458] ; cmp w8,#4 ; b.lo skip
```

**全部是"v4 才多做一步"的非致命分支，没有任何一处对 v2 报错退出。** 结论：**这个 ABL 在架构上是支持 Header v2 的。**

### ⊘ 前提 2：「TB128FU 的 DTB 的 msm-id/board-id 和 TB331FC 相同（于是能匹配）」

**方向对，但结论反了——不是"能匹配所以不是死因"，而是"这也证明了 DT 匹配不是死因"。** 实测两份 DTB 的根属性：

| 属性 | `tb331fc_stock.dtb`（本机原厂） | `tb128fu_extracted.dtb`（参考机） |
|---|---|---|
| `model` | Qualcomm Technologies, Inc. **KHAJE IDP nopmi** | **Lenovo Tab M10 Plus 3rd gen** |
| `compatible` | `qcom,khaje-idp` | `lenovo,tb128` |
| `qcom,msm-id` | `<0x206 0x10000>` | `<0x206 0x10000>` |
| `qcom,board-id` | `<0x10022 0x0>` | `<0x10022 0x0>` |
| `qcom,pmic-id` | **缺失** | **缺失** |

**两者完全一致**（`0x206`=518=SM6225 家族，`0x10022`=65570）。而且 `dtbo_a`（45 条目）里有一条 `KHAJE IDP nopmi` 也是 `msm-id 0x206 / board-id 0x10022 / pmic-id 0x2d`——说明 `0x10022` 就是联想这条产品线的 board-id，两台机器共用。

所以 ABL 的 DT Selection 会命中 **`Exact DTB match found. DTBO search is not required`**（0xAAD53/0x48598），不会走 `No match found for Soc Dtb type`（0xA0A06）或 `ERROR: Couldn't find the suitable DTB!`（0xA9258）。

> 顺带回答你的问题 3：**不需要** `qcom,pmic-id`。参考机 DTB 没有它照样能过；`pmic-id` 只是打分项（`DtMatchVal`），不是必要条件。

### ⊘ 前提 3：「`subs w8,w8,#4; b.lo #0x7758` 是 ABL 的 v2 兼容分支」

**地址对，语义错。** 这条在 **`BootLinux` 内部**，而且**它前面还有一道 0x45c 标志的短路**：

```
0x7188:  ldr  x8, [sp,#0x1e8]
0x718c:  ldrb w8, [x8,#0x45c]      ; 标志字节
0x7190:  cbz  w8, #0x7758          ; 标志==0 -> 直接跳过 init_boot
0x7198:  ldr  x8, [sp,#0x1e8]
0x719c:  ldr  w8, [x8,#0x458]      ; header_version
0x71a0:  subs w8, w8, #4
0x71a4:  b.lo #0x7758              ; version<4 -> 跳过 init_boot
          ;  >=4 才 FindImage("init_boot")，失败 -> "BootLinux: Getinit_bootImage failed!"（0x727c）
```

也就是说 `0x7758` **只是一个"跳过取 init_boot"的汇合点**，不是错误出口。而 `0x7758` 做的第一件事是：

```
0x7758:  add x0, sp, #0x220
0x775c:  bl  #0x15af0              ; GetBaseMemory()
0x7760:  str x0, [sp,#0x1e0]
0x7768:  cbz x8, #0x7838           ; ==0 成功，继续
          ; 失败才打 "Base memory not found!!! Status:%r"（0x780c）
```

`0x15af0` 内部调用 `0x14320` = `ReadRamPartitions`，并会打 `Error returned from ReadRamPartitions %r`。
**这个失败只可能发生在"读不到 RAM 分区表"时，属于平台级故障，与 Header 版本无关。** 你的机器 A 槽能正常开 Android，RAM 表必然是好的。

### ⊘ 前提 4（最关键）：「retry count 不减 ⇒ ABL 还没跳到内核就死了」

**这条推理链是断的。** ABL 里有一句专门的调试串：

```
字符串 "A/B retry count NOT decremented"  @ RVA 0x0A4925
引用点                                     @ 0x27CD0
```

它隔壁就是 `"Active Slot %s is bootable, retry count %ld"`（0xA3290 / 0x27C14）和 `"Slot %s is unbootable, trying alternate slot"`（0xA12E3 / 0x27D94）。

**存在一条"明确不做递减"的分支，就意味着"计数没变"在语义上是合法的**，它不能作为"没跳转内核"的证据。再叠加下面第 3 节的发现（参考镜像的 `root=` 指向 U 盘），"内核起来了、立刻 panic、复位"完全能产生你看到的全部现象。

---

## 2. 我已经查实的、可直接用于决策的事实

### 2.1 镜像结构（`bootinfo.py` 实测，含正确的 packed 头布局）

| 镜像 | 版本 | kernel | ramdisk | dtb | 关键点 |
|---|---|---|---|---|---|
| 原厂 `boot.img` | **v4** | **未压缩 Image 46,819,840 B**，`text_offset=0` `image_size=0x2D50000` | **0** | — | header_size=1584 |
| 原厂 `init_boot.img` | **v4** | 0 | **2,005,893 B** @0x1000 | — | ramdisk 真身在这里 |
| 原厂 `vendor_boot.img` | **v4** | — | vendor_ramdisk 11,628,676 B | **1,290,690 B** @0x1F00000 | 见 2.2 |
| `boot-tb128fu-hx83102-gpu-wifi.img` | **v2** | **GZIP 12,672,057 B** @0x1000 | **50,672,466 B** @0xC17000 | **62,532 B** @**0x3C6B000** | header_size=1660，结构**完全合法** |

> ⚠️ 提醒你之前可能踩过的一个解析坑：Android **boot v0–v2 的头部是 packed（无 8 字节对齐）**，
> `recovery_dtbo_offset` 在 `0x664`、`header_size` 在 `0x66C`、`dtb_size` 在 `0x670`、`dtb_addr` 在 `0x674`。
> 若按"自然对齐"读到 `0x668/0x670/0x674/0x678`，会得到 `dtb_size=0x1F00000`、`header_size=62532` 这种鬼值，
> 从而误判"镜像头损坏"。**实际这份参考镜像一点问题都没有**：`dtb_size=62532`（与 `tb128fu_extracted.dtb` 完全一致），
> DTB 落在 `ramdisk 结束页对齐处`，`image occupies up to 0x3C7B000 == 文件长度`，自洽。

### 2.2 ⚠️ 参考镜像的 `root=` 指向 U 盘——它根本不可能在你这台机器上跑进用户空间

```
cmdline = console=tty0 console=ttyMSM0,115200n8 earlycon=qcom_geni,0x4a90000
          androidboot.hardware=qcom ... root=/dev/sda18 rw ignore_loglevel
```

`/dev/sda18` 是 **USB 大容量存储的第 18 个分区**。Ivaylo 的成功演示是插着 U 盘、rootfs 在 U 盘上完成的。

**所以即使 ABL 完美交接，这个镜像在你机器上也必然 `VFS: Unable to mount root fs` → panic → 复位。**
拿它当"要不要走 v2 路线"的判据，本身就不成立。

### 2.3 原厂 vendor_boot 的 dtb 段不是"一个 DTB"，是 6 个拼接体

`vendor_boot.img` 的 dtb 段（off=`0xB1A000`，size=`0x13B1C2`）实际结构：

```
[0x00000 .. 0x433D1)   ~279 KB 不透明前导（首 4 字节 = 0x00000006，随后直接是 FDT 字符串块内容）
0x433D1  FDT  totalsize=0x443D1   -> next 0x877A2
0x877A2  FDT  totalsize=0x3FC8E   -> next 0xC7430
0xC7430  FDT  totalsize=0xE8B7    -> next 0xD5CE7
0xD5CE7  FDT  totalsize=0x32645   -> next 0x10832C
0x10832C FDT  totalsize=0x31E96
```

即 **5 个首尾相接的 FDT + 约 269 KB 前导**。这正是 ABL 说的"DT table"（多候选 DTB → 按 msm-id/board-id 打分选优）。

**但这里有一个值得警惕的实测结果**——那 5 个 FDT 的 `msm-id` 分别是：

```
FDT #1 @0x433d1  totalsize=0x443d1  msm-id <0x24A 0x10000>
FDT #2 @0x877a2  totalsize=0x3fc8e  msm-id <0x249 0x10000>   (khajeg)
FDT #3 @0xc7430  totalsize=0x0e8b7  msm-id <0x231 0x10000>
FDT #4 @0xd5ce7  totalsize=0x32645  msm-id <0x232 0x10000>
FDT #5 @0x10832c totalsize=0x31e96  msm-id <0x232 0x10000>
```

**没有一个是本机的 `0x206`。** 本机那份（`KHAJE IDP nopmi`）**不在其中**。
而前面那 269 KB 前导经检查：以 `00 00 00 06` 开头、紧跟 `arm,arch-cache` 等**属性名字符串**、
结尾正好是 `...qcom,vdd-cx-mx-config\0qcom,vdd-3.3-ch0-config\0icnss\0`
—— 这是**一个 FDT 的 strings block 尾部**，说明它**是一个 FDT 的残段（缺 40 字节头）**，而不是独立格式。

含义（两条都要注意）：

1. **v4 方案下，你的主线 DTB 必须是"头完整、magic 正确、`0x206/0x10022` 命中"的合法 FDT**，
   放进 vendor_boot 的 dtb 段。ABL 会走 `Single appended DTB found`（0xA31A5）分支——**这是允许的**。
2. **`fw\vendor_boot.img` 有可能与设备上实际分区不一致**（EDL 全量包的 vendor_boot 未必是原机那份）。
   这值得核实一次：A 槽能开 Android 且有 root，**只读**导出来比一比（不影响 A 槽）：

   ```bash
   adb shell su -c 'dd if=/dev/block/by-name/vendor_boot_a of=/sdcard/vb_a.img'
   adb pull /sdcard/vb_a.img D:\TB331FCLinux\dump\vendor_boot_a.img
   # 同理 boot_a / init_boot_a / dtbo_a，然后用 ablcheck.py 与 bootinfo.py 逐一比对
   ```


### 2.4 原厂 vendor_boot 的 cmdline 揭示显示通路

```
cmdline : video=vfb:640x400,bpp=32,memsize=3072000 bootconfig
bootconfig:
  androidboot.hardware=qcom
  androidboot.memcg=1
  androidboot.load_modules_parallel=false
  androidboot.usbcontroller=4e00000.dwc3
```

- `bootconfig` 这个关键字是**指令**，告诉 ABL "把后面的 bootconfig 段作为 `androidboot.*` 追加进 cmdline"。
- `video=vfb:...` 说明原厂内核**不走 ABL 的 splash framebuffer**，而是用 `vfb` 软件帧缓冲。**主线的早期 console 不能照抄这条**，要自己做 `simple-framebuffer`（你已知 ABL 的 fb 在 `0x5c000000`）。
- `androidboot.usbcontroller=4e00000.dwc3` —— USB 控制器地址，主线 `dwc3` 节点可以直接对。

### 2.5 ★ 联想板级 overlay 的真身找到了：`dtbo_a` 的 45 个条目

你的交接文档把"缺板级 DTS"列为最大缺口。**它一点也不缺，就在 `dtbo_a` 里**。实测容器头：

```
magic=0xd7b7ab1e  total=0x356bb1  hdrsz=0x20  entries_off=0x20  count=45  entry_size=0x20
```

每个 overlay 里都带**面板 + 触控 + 背光 + 霍尔键**的完整节点，而且面板有**三种变体**：

| 面板节点 | 说明 |
|---|---|
| `qcom,mdss_dsi_panel_p255_inx_fhd_video` | INX 屏 |
| `qcom,mdss_dsi_panel_p255_csot_fhd_video` | CSOT 屏 |
| `qcom,mdss_dsi_panel_p255_hx83102j_fhd_video` | HX83102J 屏（触控 IC 同名，注意混用） |
| `qcom,mdss_dsi_nt36672e_fhd_plus_{90,120}hz_video` | 参考屏 |
| `qcom,mdss_dsi_td4330_truly_v2_{cmd,video}` | 参考屏 |

触控（三条并存，说明同一 SKU 有多个供应商）：

```
novatek,irq-gpio / novatek,reset-gpio          <- Novatek NT36xxx
synaptics,tcm-i2c / synaptics,irq-gpio / synaptics,reset-gpio / synaptics,ubl-i2c-addr
focaltech
qcom,i2c-touch-active                          <- 告诉你去哪个 i2c 总线找
```

背光/电源：

```
pm6125_pwm                 <- 背光 PWM 是 PM6125，不是 PM8008
disp_lcd_bias_en / disp_lcd_bias_en_default   <- LCD 偏压使能 GPIO
```

其它：`gpio_keys/hall_key`（霍尔保护套检测）、`qcom,cam-sensor0/1`、`disp_rdump_region`。

**这批 overlay 直接就是写主线 DTS 的原始素材**，比对着 `tb331fc_stock.dts` 猜要可靠得多。提取方法见第 8 节。

### 2.6 原厂 dtbo 会"叠"在你的 DTB 上

`ablcheck.py` 对原厂 `dtbo.img` 的判定：**有 1 条 overlay（#2 `KHAJE IDP nopmi`）会命中你的设备键并被应用**（另有多条 0x206+0x10022 条目）。
所以 B 槽做主线实验时，**必须刷一个合法的空 dtbo**（注意：`dummy_dtbo_raw.img` / `dummy_dtbo_fixed.img` 都是 467 B、`count=1`，属于"1 条空 overlay"，不是"0 条"，能过 ABL 的 `DtEntryCount/DtEntrySize` 校验；但刷进 24 MB 分区后剩余空间是脏数据，ABL 只按 `total` 读，通常无碍）。

### 2.7 没有事后日志通道（这条要提前接受）

- ABL **不写 `logfs`**：全字符串扫描里没有 `logfs` / `qlog`，只有 `ramdump` / `splash` 预留区的校验。
- `logfs` 分区当前内容 = EDL 刷机工具写进去的 **FAT12 模板**（首扇区 `MSDOS5.0` / `BOOTMGR`），**不是日志**。
- `fastboot fetch` **不支持**：实测 `fastboot: error: Unable to get max-fetch-size. Device does not support fetch command.` → 没法回读任何分区。
- `logdump`(64 MB) / `rawdump`(128 MB) 是给 XBL 抓**内核/子系统 crashdump** 用的，ABL 自己的早期失败不会落在里面。

**结论：ABL 死在哪，静态分析到不了，必须造观测通道。**

---

## 3. 那么，1 秒黑屏回 fastboot 最可能是什么？

按"证据强度"排序，并给出各自的**特征判据**（这是关键——不要猜，去分辨）：

| # | 假设 | 强度 | 特征判据 |
|---|---|---|---|
| **H1** | **内核确实被交接了，然后立刻 panic → PMIC 复位 → 回到 fastboot** | **高** | 复位期间 fastboot USB 会**消失再出现**；`retry-count` 可能减也可能不减（见前提 4） |
| **H2** | ABL 在 `LoadImageAndAuth` / `UpdateBootParamsSizeAndCmdLine` 里**静默返回错误**（`BootLinux` 里多处 `cbz → return status` 是不打任何消息的） | 中 | fastboot USB **从不消失**，原地回到提示符 |
| **H3** | ABL 报错并停在一个**黑屏错误页**（`Splash region not found in device tree, powering down the display and controller` @0xA7235 会主动关屏） | 中 | USB 消失后不回来；屏幕黑且长时间无反应，需长按电源 |
| **H4** | DTB 匹配失败 | **低（已基本排除）** | 键值完全一致，见 2.1 |
| **H5** | GZIP inflate 失败 / `image_size` 越界 | 低 | 参考镜像是标准 gzip，`zlib` 能完整解开（`ablcheck` 未报错） |

**H1 为什么强度最高**：因为参考镜像的 `root=/dev/sda18`（U 盘），没有那个 U 盘时内核**必然** panic；而且它的 DTB 是 `Lenovo Tab M10 Plus 3rd gen`，`p255_inx_fhd` 面板节点**不存在**，就算根文件系统挂上了也点不亮屏。**"点亮 Logo 1 秒 → 黑 → 回 fastboot" 与"H1 + 无 U 盘 rootfs" 的现象完全吻合。**

---

## 4. 回答你的四个问题

### Q1 Header v2 在 Android 13/14 GKI 平台（v4 原生）上有没有普遍的隐式坑？

**在这个具体 ABL 上：解析层没有坑（已反汇编证伪）。但有两个工程层的原因，让我建议你走 v4：**

1. **v2 路径会让一批 `image_info` 字段留空。** `UpdateBootParamsSizeAndCmdLine` 在 v3/v4 分支里会把 `vendor_boot` 的 `page_size / dtb_size / vendor_ramdisk_size / bootconfig_size` 等写进输出结构（`+0x88/+0x8c/+0x90/+0x94`…），**v2 路径一处都不写**，那些字段保持原值。这条 ABL 是 A14/GKI 时代的产物，v2 路径大概率是"兼容但没人验证"的死代码区——**能过，但没人为它负责**。`?`
2. **v4 是原厂唯一走过的路径**，`vendor_boot` 的 dtb 段格式、`bootconfig` 语义、`androidboot.*` 注入都是现成可用的；而 v2 要你自己把 dtb 拼在 boot.img 尾部、自己承担 cmdline 位置差异。

> **但请把顺序反过来**：不要一上来就重做 v4 打包。先用第 6 节的实验判定 H1/H2，
> 因为如果是 H1，**打包格式根本不是问题所在**，换 v4 也照样 panic。

### Q2 「retry count 不减」最典型的触发路径是什么？

**这个问题的前提已被推翻（见前提 4）。** ABL 里 `A/B retry count NOT decremented` 是显式分支。递减是**写 GPT 分区属性**（priority/active/retry/successful 四个位域），不是写 `misc`。所以你看到的 `6` 只能说明"ABL 没有选择写 GPT"，**不能**说明执行到了哪一步。

要判断执行到哪一步，用**复位事件**（USB 消失/重现），不要用计数器。

### Q3 骁龙 685 的 DTB 匹配还需要哪些属性？

**只需要这两个，且已完全命中：**

```
qcom,msm-id    = <0x206 0x10000>      # 518 = SM6225 家族
qcom,board-id  = <0x10022 0x00>       # 65570
```

- `qcom,pmic-id`：**非必需**（原厂 DTB 自己都没有），只是 `DtMatchVal` 的打分项。
- 反而是**建议你加**：`qcom,pmic-id = <0x2d 0x0 0x0 0x0>`，与 dtbo 里 `KHAJE IDP nopmi` 那条 overlay 对齐——这样 ABL 的"精确匹配"打分更高，也更符合原厂约定。

**合并原厂 `/reserved-memory` 和 `memory` 节点：不仅有必要，而且是必须做。** 理由（都有 ABL 字符串为证）：

```
0x52CDC  "ramdump region not found in device tree"
0x51F2C  "Splash region not found in device tree, powering down the display and controller"
0xA92FD  "ERROR: Could not find the ramdump reg property"
0x9ACAE  "ERROR: Ramdump mem reservation node size. Expected: %d, Actual: %d"
0x9C468  "/soc/disp_rdump_region"
0xACd39 / 0xA1CC5 / 0x9BFFB  一堆 "Integer Overflow: ImgSizeActual/DtbActual/RecoveryDtboActual"
```

ABL **会在交接前解析你传进去的 DTB**，去找 `ramdump` / `splash` / `disp_rdump_region` 等预留区，并且会拿 `Expected`（来自分区表 `logdump=64MB`、`rawdump=128MB`）和 `Actual`（来自 DTB）比对。

**TB128FU 的 DTB 里这些节点的基址/大小是按 TB128FU 的 DDR 划分写的，直接搬到 TB331FC 上是"地址对了是运气，地址错了是必然"。** 正确做法：以 `tb331fc_stock.dts` 的 `/reserved-memory` 和 `/memory` 为基准（它就是从本机 dump 的），把主线内核需要的节点（`hyp` / `tz` / `adsp` / `mpss` / `gpu` / `wlan` / `ramoops` 等）按本机实际保留。

### Q4 没有 UART 时，最高效的二分法？

见下面第 6 节，按"信息量 / 成本"排序。核心思想：**先用"复位 vs 原地中止"把空间一分为二，再在每一半里用"已知能过的镜像"做对照。**

---

## 5. 观测通道：三选一，优先第一个

| 方案 | 成本 | 能拿到什么 | 评价 |
|---|---|---|---|
| **A. 找 UART 测试点** | 拆后盖 + 两根飞线 + USB-TTL | **ABL 全部 DEBUG 输出 + 内核早期 console**，一步到位 | ⭐**最高 ROI**。参考镜像 cmdline 已经告诉你 UART 在哪：`earlycon=qcom_geni,0x4a90000` → **GENI QUP 基址 `0x4A90000`**。原厂 cmdline 也有 `console=ttyMSM0,115200n8`。找主板上标 `TX/RX/GND` 或靠近 SoC 的两个过孔即可 |
| **B. `simple-framebuffer` + `console=tty0`** | 改 DTB，刷 B 槽 | 内核阶段的全部 printk（看不到 ABL） | 可行。ABL 的 fb 在 `0x5c000000` 且 Logo 已被画上去，交接后 framebuffer 仍然有效。需要正确的 `width/height/stride/format`——**从 `tb331fc_stock.dts` 的 `qcom,mdss_dsi_panel_p255_*` 里读 `qcom,mdss-dsi-panel-width/height`，加上 ABL splash 的实际配置** |
| **C. `pstore/blk` 到 `misc`** | 改内核 config + cmdline | 掉电后仍可读的 panic 现场 | 需要 `CONFIG_PSTORE_BLK`，且要 `ramoops` 预留区；`misc` 只有 1 MB，够放 dmesg。**做不到 ABL 阶段** |

> ⚠️ **别指望 `adb`**（主线没有 adbd），**别指望 `fastboot fetch`**（实测评测不支持），**别指望 `logfs`**（是 FAT12 模板）。

---

## 6. 立刻可做的三步（全部只碰 B 槽，A 槽零风险）

### 步骤 1 — 判定 H1 / H2（**不刷任何东西，2 分钟**）

```powershell
cd D:\TB331FCLinux\tools
.\resetwatch.ps1
```

脚本会：检查当前确实是 B 槽（是 A 槽会直接拒绝执行）→ `fastboot reboot` → 每 200 ms 轮询 `fastboot devices` → 输出时间线。

**判读：**

- **fastboot 设备从未消失** → **H2**：ABL 原地中止，问题在 ABL 内部。→ 走步骤 3。
- **消失后 N 秒重新出现** → **H1**：内核被交接了，是内核/rootfs 死的。→ 走步骤 2。
- **消失后不回来** → **H3**：卡在黑屏错误页，长按电源 10 s 强启。

### 步骤 2 — 如果是 H1：先给它一个能挂的 root，再谈显示

参考镜像 `root=/dev/sda18`，你必须二选一：

- **最省事**：找一个 U 盘，分 ≥18 个分区，把 pmOS rootfs 放到 `sda18`（真的这么原始）。
- **更合理**：把 rootfs 放进 **`initramfs`**（`root=/dev/ram0 rw` 或直接不带 `root=`），这样不依赖任何块设备，一定能进 shell（哪怕是 `init=/bin/sh`）。

同时把 DTB 换掉：**用 `tb331fc_stock.dts` 的 `/memory` + `/reserved-memory`** 重做一份 `sm6225-lenovo-tb331fc.dts`，参考 `sm6225-lenovo-tb128.dts` 的骨架。这一步做完，即使屏不亮，串口/simplefb 也应该有东西。

### 步骤 3 — 如果是 H2：用"已知能过的镜像"做对照，把 v2 变量单独隔离

这是最关键的一次二分。**刷一个"用 v2 头包装原厂 GKI Image + 原厂 DTB + ramdisk=0"的镜像到 `boot_b`：**

- 如果它**能让 fastboot 消失再出现**（内核起来了、因为没 ramdisk 而 panic/复位）→ **v2 头本身没问题**，之前失败是内容问题（rootfs / DTB 预留区 / 面板）。
- 如果它**和参考镜像表现一模一样**（1 秒黑、原地回 fastboot、USB 不消失）→ **v2 头在这个 ABL 上确实走不通**，那就老老实实上 v4 三分区。

打包命令（WSL2 里跑，`mkbootimg` 任意版本）：

```bash
# 从原厂 boot.img 里取出未压缩的 Image（44 MB，text_offset=0）
python3 unpack_bootimg --boot_img boot.img --out /tmp/stock
# -> /tmp/stock/kernel 就是 ARM64 Image

mkbootimg --header_version 2 \
  --kernel /tmp/stock/kernel \
  --ramdisk /dev/null \
  --dtb   tb331fc_stock.dtb \
  --dtb_offset 0x01f00000 \
  --kernel_offset 0x00008000 \
  --ramdisk_offset 0x01000000 \
  --tags_offset 0x00000100 \
  --pagesize 4096 \
  --cmdline "console=tty0 console=ttyMSM0,115200n8 earlycon=qcom_geni,0x4a90000 ignore_loglevel" \
  -o boot_v2_stockkernel.img
```

然后**先离线过一遍我写的校验器**，再刷：

```powershell
python D:\TB331FCLinux\tools\ablcheck.py --boot boot_v2_stockkernel.img --dtbo dummy_dtbo_fixed.img
```

### 步骤 4（若确认 v2 不通）— v4 三分区，按原厂规格打

```bash
# boot_b: 只放内核（v4 不要 ramdisk）
mkbootimg --header_version 4 --kernel Image -o boot_b.img

# init_boot_b: 只放 ramdisk
mkbootimg --header_version 4 --ramdisk initramfs.cpio.gz -o init_boot_b.img

# vendor_boot_b: dtb + cmdline + bootconfig
mkbootimg --header_version 4 \
  --vendor_boot vendor_boot_b.img \
  --vendor_ramdisk /dev/null \
  --dtb tb331fc_mainline.dtb \
  --dtb_offset 0x01f00000 \
  --cmdline "console=tty0 earlycon=qcom_geni,0x4a90000 ignore_loglevel" \
  --pagesize 4096
```

**三个硬约束（来自实测的原厂镜像与分区表）：**

| 分区 | 上限 | 原厂实际占用 |
|---|---|---|
| `boot_b` | `0x6000000` = 96 MB | 0x2CA8000 ≈ 45 MB |
| `init_boot_b` | `0x800000` = 8 MB | 0x1EB000 ≈ 1.9 MB |
| `vendor_boot_b` | `0x6000000` = 96 MB | 0xC57000 ≈ 12 MB |
| `dtbo_b` | `0x1800000` = 24 MB | — |

**还有两个 v4 特有的坑：**

1. **`vendor_boot` 的 dtb 段是"拼接体"**（见 2.3），不是单 file。如果你只放一个 DTB，ABL 会走 `Single appended DTB found`（0xA31A5）分支——**这是允许的**，但和原厂布局不同。稳妥做法：先用单 DTB，`ablcheck.py` 的 `--vendor-boot` 会告诉你有几个 FDT、是否有命中的键。
2. **`dtbo_b` 必须刷空的**，否则第 2.6 节那条 overlay 会把 `p255` 的 `mdss` 节点叠到你主线 DTB 上。

---

## 7. 安全红线（复述，避免误操作）

| 操作 | 风险 | 说明 |
|---|---|---|
| `fastboot flash boot_b` / `init_boot_b` / `vendor_boot_b` / `dtbo_b` / `vbmeta_b` | 安全 | 只影响 B |
| `fastboot --set-active=b` | 安全 | 只切当前槽 |
| **`fastboot flash boot`（不带 `_b`）** | **禁止** | 会落到当前槽；当前是 b，但一旦你 `--set-active=a` 后再执行就等于打 A 槽 |
| **`fastboot flash abl` / `xbl` / `tz` / `hyp` / `devcfg`** | **禁止** | 改引导链本体，会真砖（虽然你有 EDL 能救） |
| **`fastboot erase misc`** | **禁止** | ABL 的启动指令状态在里面 |

**回滚一条命令**：`fastboot --set-active=a ; fastboot reboot`

**当前实况**：`current-slot:b` · `slot-successful:a:yes` · `slot-retry-count:a:6` · `slot-unbootable:a:no` —— **A 槽完全健康**。

---

## 8. 附：把 dtbo 里的板级信息抽出来（写 DTS 用）

```bash
# 1) 解容器：45 个 dtbo 条目按 32 字节表头切开
python3 - <<'PY'
import struct, os
d = open('/path/to/dtbo_a.img','rb').read()
magic,total,hdrsz,eoff,cnt,esz = struct.unpack_from('>6I', d, 0)
os.makedirs('dtbo_entries', exist_ok=True)
for n in range(cnt):
    sz, off = struct.unpack_from('>2I', d, eoff + n*esz)
    open(f'dtbo_entries/entry_{n}.dtbo','wb').write(d[off:off+sz])
PY

# 2) 只看命中本机键的那几条（msm-id 0x206 + board-id 0x10022）
for f in dtbo_entries/*.dtbo; do
  dtc -I dtb -O dts "$f" 2>/dev/null | grep -qE 'qcom,board-id.*0x10022' && echo "HIT $f"
done

# 3) 反编译成可读 dts，抄 p255 面板 / novatek / synaptics / pm6125_pwm / hall_key 节点
dtc -I dtb -O dts dtbo_entries/entry_2.dtbo -o entry_2.dts
```

**优先抄这几块**（都在命中条目里）：

- `qcom,mdss_dsi_panel_p255_inx_fhd_video`（时序、`qcom,mdss-dsi-panel-width/height`、`dsi-panel-supply`）
- `novatek` / `synaptics_tcm` / `focaltech`（i2c 地址、`irq-gpio`、`reset-gpio`，看 `qcom,i2c-touch-active` 定总线）
- `pm6125_pwm` + `disp_lcd_bias_en`（背光 PWM 通道 + 偏压 GPIO）
- `gpio_keys/hall_key`（霍尔）

---

## 9. 本次产出的工具

| 文件 | 用途 |
|---|---|
| `D:\TB331FCLinux\tools\bootinfo.py` | boot/init_boot/vendor_boot 头解析（v0–v4，**含正确的 packed 布局**），并自动提取 dtb |
| `D:\TB331FCLinux\tools\dtbkeys.py` | 从 DTB / dtbo 容器里抽出 `msm-id / board-id / pmic-id / model` |
| `D:\TB331FCLinux\tools\ablcheck.py` | **刷机前离线过一遍 ABL 的硬性校验**（段偏移、gzip/Image 魔数、DT 键匹配、dtbo overlay 命中、分区容量） |
| `D:\TB331FCLinux\tools\abl_dis.py` | ABL `.text` 反汇编，自动把 `ADRP+ADD` 的目标解析成字符串 |
| `D:\TB331FCLinux\tools\abl_xref.py` | 全量字符串交叉引用（`# resolved page-relative loads: 7504`） |
| `D:\TB331FCLinux\tools\resetwatch.ps1` | **判定"原地中止"还是"真复位"**，零刷写 |

`ablcheck.py` 对本机原厂三件套的自检结果（作为基线，证明这个校验器不是瞎报）：

```
=== boot.img       === 15 pass / 1 warn / 1 FAIL
   FAIL: a DTB in the table matches this device  -- 5 FDT(s) scanned
```

> 这条 FAIL 是**校验器自己的局限**，不是原厂镜像的问题：原厂 vendor_boot 的 dtb 段有 279 KB 不透明前导，
> 我的扫描器把前导里的假 `d00dfeed` 也算进去了，且没有跳过 5 个 FDT 的偏移对齐。
> **已经能正常工作的是 `--boot` 与 `--dtbo` 两条路径**（对参考镜像给出 17 项 14 pass / 3 warn / 0 fail）。
> 用 v4 之前需要我修一下 vendor_boot 那条扫描（跳过前导、按 `totalsize` 递进）。

---

## 10. 建议的下一步（按顺序，别跳）

1. **跑 `resetwatch.ps1`**，拿到 H1/H2/H3 的判定。（0 风险，2 分钟）
2. 如果是 **H1**：把 rootfs 塞进 initramfs，DTB 换成本机 `/memory` + `/reserved-memory`，加 `simple-framebuffer` + `console=tty0`，再试。**这才是"主线能不能起"的真正判据。**
3. 如果是 **H2**：按第 6 节步骤 3 打"v2 + 原厂内核 + 原厂 DTB"的对照镜像，隔离"v2 头"这一个变量。
4. 无论哪条路，**同时去找 UART**（`0x4A90000`）。一旦接上，前面这些二分法全部作废，直接看日志。
5. 板级 DTS 不要从零写，按第 8 节从 `dtbo_a` 抽。

---

*本报告未修改设备任何分区。A 槽状态：`slot-successful:a:yes` / `slot-retry-count:a:6` / `slot-unbootable:a:no`。*

---

# 附录 A：实测实验日志 —— 根因已定位

> 全部实验只写 `boot_b` / `dtbo_b` / `vbmeta_b`，A 槽零改动。
> 判定指标：`T_back`（`fastboot reboot` 到 fastboot 重新枚举的毫秒数）、`flaps`（重新出现次数）、`retry`。

| # | boot_b 内容 | 变化量 | T_back | flaps | 结论 |
|---|---|---|---|---|---|
| T1 | 原始参考镜像（48 MB ramdisk） | 基线 | 5343 ms | 1 | ABL 中止 |
| T2 | 同 T1，**破坏 gzip 魔数** | 内核载荷 | **4995 ms** | 1 | **校准点：早期加载失败** |
| T3 | 同 T1 + 已签名 `flags=3` 空 vbmeta_b | AVB | 5342 ms | 1 | **vbmeta 无关** |
| T4 | 同 T1，ramdisk → 124 B 空 cpio | ramdisk 大小 | 5348 ms | 1 | **ramdisk/重叠无关** |
| T5 | 同 T4，`dtb_size` → 65536（页对齐） | dtb_size | 5346 ms | 1 | **页对齐无关** |
| T6 | 同 T5，`dtbo_b` → 合法原厂 45 条目 dtbo | dtbo | 5325 ms | 1 | **dtbo 无关** |
| T7 | 同 T4，内核 → **未压缩 Image**（33.3 MB） | 压缩格式 | 4994 ms | 1 | v2 路径**只认 gzip**，raw 直接判失败 |
| T8 | 同 T4，gzip 后解压尺寸 == `image_size` | 尺寸一致性 | 5379 ms | 1 | **尺寸无关** |
| **T9** | **同 T8，DTB → 本机 `tb331fc_stock.dtb`** | **DTB 内容** | **>70 s 未回** | **0** | ★**内核被交接了！** |

## A.1 结论

**根因是「喂给 ABL 的 DTB 内容不属于这台设备」，而不是 Header 版本。**

- T1–T8 全部落在 **5325–5379 ms**（抖动 < 25 ms），说明它们死在**同一个毫秒级确定的位置**：gzip 解压完成后、`UpdateDeviceTree`（0x28AD0）阶段。
- T2/T7 是 **4995 ms**，比其它快约 350 ms = 省掉了 12.6 MB 的 inflate 开销 → 它们在解压**之前**就失败了。这个对照证明 T1/T3–T6/T8 确实走完了 inflate。
- **T9 只改了一个变量（DTB 内容），行为立刻变成 `flaps=0`**：设备从此不再回 fastboot，也不再出现在 USB 上。
- T9 的载荷是「pmOS 内核 + 124 B 空 cpio（无 `/init`）+ `root=/dev/sda18`（无 U 盘）」→ 内核即使完美运行也**必然 panic**，而默认 `panic=0` 不重启 → **挂死、无 USB、黑屏**。这与 T9 观测完全吻合。

**所以：ABL 成功把控制权交给了内核。之前 9 次"1 秒 Logo → 黑屏 → 回 fastboot"全部是 ABL 在 `UpdateDeviceTree` 里拒绝了 TB128FU 的 DTB。**

## A.2 机制（都有 ABL 字符串与代码为证）

DT 键（`msm-id 0x206` / `board-id 0x10022`）相同，只决定 ABL **选中**哪棵 DTB；
选中之后 `UpdateDeviceTree` 还要按**节点内容**做一堆硬性校验，这些才是致命的：

```
0x9ACAE  ERROR: Ramdump mem reservation node size. Expected: %d, Actual: %d
0x52CDC  ramdump region not found in device tree
0xA92FD  ERROR: Could not find the ramdump reg property
0xA1508  ERROR: Could not update ramdump mem info
0x9C468  /soc/disp_rdump_region
0x51F2C  Splash region not found in device tree, powering down the display and controller
0xAC10B  ApplyOverlay: After overlay DTB size exceeded than supported
```

`Expected` 来自分区表（`logdump=64 MB`、`rawdump=128 MB`），`Actual` 来自 DTB 的 `/reserved-memory`。
**TB128FU 的树里这些预留区是按 TB128FU 的 DDR 划分写的，与本机对不上 → ABL 拒绝交接。**
这也解释了为什么 T5/T6（dtb_size 对齐、换合法 dtbo）都没用：问题在**节点内容**，不在容器格式。

## A.3 这同时推翻了本条最流行的两个说法

1. **Gemini 的「retry count 不减 ⇒ 没过内核」不成立**：T2（必然失败的坏 gzip）retry 照样 6→5。
   **retry-count 是每次尝试无条件递减的，不能做阶段指示器。**
2. **「Header v2 在 A14 平台上必崩」不成立**：T9 用纯 Header v2 就把内核送进去了。

## A.4 下一步（按优先级）

1. **加 `panic=10`**（或 `panic=5`）到 cmdline。现在内核 panic 会挂死、必须手动长按电源，加了之后会自动重启回 fastboot，**实验就能重新自动化**。
2. **给一个真 initramfs**：至少要有 `/init`；不要依赖 `root=/dev/sda18`。
3. **DTB 用本机的树做基线**：`tb331fc_stock.dtb` 已验证能过 ABL。主线 DTS 必须以它的 `/memory` + `/reserved-memory` 为骨架，而不是 TB128FU 的。
4. **要看到画面**：`simple-framebuffer`（ABL fb 在 `0x5c000000`）+ `console=tty0`；或找 UART（`0x4A90000`）。

> ⚠️ T9 之后设备处于挂死状态，需**长按电源 10–15 s 强制关机**，再「电源 + 音量下」进 fastboot。

---

# 附录 B：T11–T15 —— ABL 挑的是 DTB「内容」，且我还没猜中

## B.1 决定性对照

| DTB | ABL 行为 |
|---|---|
| **原厂 `tb331fc_stock.dtb`（421 KB）** | **放行**（不回 fastboot，设备挂在 Logo，看门狗后才复位） |
| 主线 `sm6225-lenovo-tb128` DTB（62 KB） | **拒绝**（~5.2–5.3 s 回 fastboot，flaps=1） |

所以：**ABL 是否放行，完全由 DTB 内容决定，与 Header 版本、vbmeta、ramdisk、dtbo 容器格式全都无关。**

## B.2 关于「补节点」的四次尝试，全部失败

| # | 改动 | 结果 |
|---|---|---|
| T11 | `memory@5c000000` → `splash_region@5c000000`（+`label="cont_splash_region"`）；新增 `/soc@0/disp_rdump_region@5c000000`；根节点加 `/mem-offline`、`/ddr-regions` | 5210 ms，仍中止 |
| T12 | 再把 `dtbo_b` 换成 `dummy_dtbo_fixed.img`（`target-path="/"` 的空 overlay） | 5240 ms，仍中止 |
| T13 | 再给 `/chosen` 预置 `linux,initrd-start` / `linux,initrd-end` / `kaslr-seed`（ABL 要原地改写这三项） | 5235 ms，仍中止 |

**注意一个规律**：T11–T13 都落在 **5210–5240 ms**，而早期 T1/T3–T6/T8 是 **5325–5348 ms**。约 110 ms 的稳定位移说明补丁**确实改变了执行路径**（走得更早/更短），但没有跨过那道坎。

## B.3 已定位的真正机制：路径来自 DTBO overlay，不是 ABL 硬编码

`/soc/qcom,dsi-display-primary`、`/soc/disp_rdump_region` 这些字符串在二进制里紧挨着，且它们的唯一引用点是
**`ufdt_overlay_apply` / `ufdt_overlay_do_fixups` 的错误路径**（libufdt）：

```
ERROR: %s():  ufdt_overlay_apply
Couldn't find '%s' path in main dtb
failed to overlay node %s to target %s
failed to apply fragments
```

含义：这些是**叠加到主 DTB 上的 overlay 片段的目标路径**。原厂 `dtbo_b`（45 条目）的 fragment 指向
`/soc/qcom,dsi-display-primary` 等厂商路径；主线 DTB 没有这些路径 → 片段应用失败 → `UpdateDeviceTree` 整体失败。
**这也解释了为什么原厂 DTB 能过**（它什么路径都有）。

> 但 T12 换成 `target-path="/"` 的空 overlay 仍然中止，说明**除 overlay 之外，ABL 自己的代码还有第二道对 DTB 内容的硬性要求**，尚未定位。

## B.4 已排除清单（这些都不用再怀疑）

Header v2 支持 · vbmeta/AVB · 分区尺寸 · ramdisk 大小与加载地址重叠 · `dtb_size` 页对齐 ·
内核 gzip/raw 格式 · 解压尺寸与 `image_size` 一致性 · dtbo 容器格式 · overlay 目标路径 · `chosen` 属性增长 ·
retry-count 作为阶段指示器（已用坏 gzip 校准证明其无效）· `logfs` / `fastboot fetch` / `oem` 日志通道（均不可用）

## B.5 三个可行方向（按性价比）

| 方案 | 成本 | 说明 |
|---|---|---|
| **A. 以原厂 DTB 为基线做减法** | 中 | 原厂 DTB 能过 ABL。把它的 `/soc` 显示子树以外的东西逐步替换为主线内容，机械二分出"ABL 到底要哪一棵"。比"给主线 DTB 加节点"可控 |
| **B. 读 `logdump` 分区** | 低（但要进 A 槽） | 64 MB，Qualcomm 的 ABL/内核 crashdump 落点。A 槽有 root，`dd` 出来看有没有 ABL 的文本。**这是唯一可能白拿到 ABL 日志的路** |
| **C. 接 UART** | 高（要拆机） | `0x4A90000`（GENI QUP）。一旦接上，ABL 是 DEBUG 构建（二进制里路径 `ABL_OUT/Build/DEBUG_CLANG35/.../DEBUG/LinuxLoader.dll`），**日志是全的**，前面所有黑箱立刻消失 |

> 我的建议顺序：**B → A → C**。B 只要一次槽位切换和一条 `dd`，却可能直接终结这场黑箱。

---

# 附录 C：B 方案失败 + A 方案首轮结果

## C.1 B（读 dump 分区）—— 失败，没有日志

切到 A 槽启动 Android（`--set-active=a` 只改 GPT active 标志，未写任何 A 分区），root 可用，成功导出：

| 分区 | 大小 | 内容 |
|---|---|---|
| `logdump` (sde59) | 64 MB | **全零**，`last non-zero byte at 0x0` —— ABL/内核从未写入 |
| `logfs` (sde56) | 8 MB | 仅 12,313 字节的 **FAT12 模板**（`NO NAME`/`BOOTMGR`/`Disk error`），非日志 |

> 导出要点：`/sdcard` 是 FUSE，`dd` 会得到 0 字节；必须写到 `/data/local/tmp`。

**结论：这台机器没有任何可取的 ABL 事后日志通道。** 与静态分析的判断一致（ABL 不写 logfs；logdump 只收内核 crashdump，而内核从未运行）。

## C.2 A（从原厂 DTB 做减法）—— 首轮就发现真实结构差异，但测试无效果

对比原厂 DTB 与主线 DTB 的根节点命名：

```
原厂（ABL 接受）:   memory {        soc {            ← 无 unit address
主线（ABL 拒绝）:   memory@80000000 {   soc@0 {      ← 带 unit address
```

而 ABL 硬查的路径正是 **`/memory`** 和 **`/soc/...`**。如果 ABL 用精确路径匹配，主线 DTB 的
`/memory`、`/soc/*` 全部查不到 —— 这能解释为什么前四次「往 `soc@0` 下面补节点」全部无效。

**测试 T14**：主线 DTB 去掉两个 unit address（`soc@0`→`soc`、`memory@80000000`→`memory`），
其余保留全部补丁 → **5219 ms / flaps=1，仍然中止**。

## C.3 到目前为止的完整判定

| 结论 | 证据强度 |
|---|---|
| Header v2 完全可用 | 强（反汇编 + 实际进入 gzip 解压） |
| 原厂 DTB 能被 ABL 接受；主线 DTB 不能 | 强（flaps=0 vs flaps=1 反复复现） |
| 失败点在「gzip 解压完成之后、加载 ramdisk 之前」，即 ABL 的 DTB 处理阶段 | 强（T2 校准点 4995 ms，其余 5210–5348 ms） |
| 五次 DTB 补丁（overlay 目标节点 / 空 dtbo / chosen 属性 / 去掉 unit address）都无效 | 强（每次都是同一 5.2 s 中止） |
| **原厂 DTB 那一侧到底是「ABL 放行并交接」还是「ABL 自己挂住」，无法判定** | **未知 —— 这是当前最大盲点** |
| `panic=10` 在原厂 DTB 下不触发 | 说明**不是内核 panic**：要么 ABL 挂住，要么内核死在 panic 机制就绪之前 |

## C.4 为什么我建议停止盲试

- 每次迭代 = 1 次 flash + 1 次重启测量，**且 ABL 不返回任何诊断**；「放行」那次还要你手动长按电源。
- 每轮只验证 1 个猜测，而 DTB 里可怀疑的差异有几十处（`/reserved-memory` 全套地址、根 `compatible`、
  `/soc` 显示子树、`__symbols__`……）。期望迭代次数是两位数。
- **ABL 是 DEBUG 构建**（二进制路径 `ABL_OUT/Build/DEBUG_CLANG35/.../DEBUG/LinuxLoader.dll`），
  也就是说它内部有完整日志，只是走 UART（`0x4A90000`）。**接上 UART 一行日志就能替代上面几十次盲试。**

## C.5 如果继续盲试，建议的优先级（信息量/成本从高到低）

1. 根 `compatible` 改成原厂值（ABL 里有 `soc version does not match` / `qcom,msm-id does not exit` 之类的比较）
2. `/reserved-memory` 整套换成原厂的地址表（ABL 要读 `ramdump`/`splash` 的 reg 做校验）
3. 把原厂 `/soc` 的显示子树（`qcom,dsi-display-primary`、`dsi_pll_codes`、`qcom,mdss_*`）整体搬进主线 DTB
4. 反过来：原厂 DTB 只替换 `/memory` 为 8 GB，看 ABL 是否仍接受（判断 `/memory` 是否真被使用）

---

# 附录 D：决定性负面结论 —— 那些 DT 节点全是「非致命」的

## D.1 反汇编证明：显示/内存节点的返回值被直接丢弃

`0x50648`–`0x50680` 这一段把所有相关调用列得清清楚楚：

```
0x5064c:  bl #0x51c70     ; /reserved-memory/splash_region  -> 返回值【丢弃】
0x50654:  bl #0x52730     ; /soc/qcom,dsi-display-primary     -> 返回值【丢弃】
                          ;  (同函数还查 demura_region_0/1、/soc/disp_rdump_region)
0x5065c:  bl #0x59690     ; /soc/dsi_pll_codes                -> 返回值【丢弃】
0x50664:  bl #0x52ae0     ;                                   -> 返回值【丢弃】
0x50668:  ldr x0,[sp,#0x250]
0x5066c:  adrp x1, "/chosen"
0x50674:  bl #0x56d10     ; fdt_path_offset(fdt, "/chosen")   -> 返回值【被检查】
0x50680:  tbz w8,#0x1f,#0x50750   ; 成功才继续，否则 "ERROR: Could not find chosen node ..."
```

**结论：缺 `splash_region` / `dsi-display-primary` / `demura_region_*` / `dsi_pll_codes` 只会打印警告并继续。**
其中 `Splash region not found in device tree, powering down the display and controller` 就是
**关掉屏幕后继续**——这正是"Logo 之后变黑"的真正原因，它跟启动失败无关。

**所以附录 B/C 里那 5 次「补节点」从原理上就不可能有效**，现在有代码证明，不用再试那条路了。

## D.2 真正的致命闸门：`UpdateDeviceTree`（0x28AD0）

```
0xa82c:  bl #0x28ad0              ; UpdateDeviceTree
0xa840:  cbnz w8, #0xb400         ; 返回 true -> 直接错误返回（致命）
```

把 `0x28AD0`..`0x2A200` 区间引用的字符串全部列出，这个函数的失败出口只有这些：

```
BootLinux: failed to get dtbo image        DtboImgBuffer is NULL
Dtbo hdr magic mismatch %x, with %x        Dtbo Size too big %x, Allowed size %x
Dtbo Table TotalSize/HeaderSize/DtEntrySize/DtEntryOffset got corrupted
DTB header is corrupted, DtEntryCount %x ...
Invalid boot image header: %d              Image Header Version: 0x%x
Integer Overflow: RecoveryDtboOffset=%u RecoveryDtboSize=%u
Invalid recovery dtbo: RecoveryDtboOffset=%u, RecoveryDtboSize=%u, ImageSize=%u
Gpt Image size is invalid                  MBR signature do not match
```

**全部集中在 dtbo / recovery_dtbo / GPT 解析上**，没有一条与显示树、`/memory`、`/chosen` 有关。

## D.3 最后两次实验（仍然失败）

| # | 改动 | 结果 |
|---|---|---|
| T15 | 主线 DTB + `dtbo_b` = **0 条目**的合法 dtbo 容器（`magic=0xd7b7ab1e, total=0x20, count=0`），完全不叠加任何 overlay | **5246 ms / flaps=1**，仍中止 |

## D.4 累计已排除（可作为最终清单）

Header v2 · vbmeta/AVB · 分区尺寸 · ramdisk 大小与加载地址重叠 · `dtb_size` 页对齐 ·
内核 gzip/raw 格式 · 解压尺寸与 `image_size` 一致性 · dtbo 条目内容 · 完全无 overlay ·
`/reserved-memory/splash_region` · `/soc/disp_rdump_region` · `/soc/qcom,dsi-display-primary` ·
`demura_region_0/1` · `dsi_pll_codes` · `/mem-offline` · `/ddr-regions` ·
`/chosen` 的 `linux,initrd-start/end`、`kaslr-seed` 预置 · 根节点 unit address（`soc@0`/`memory@`）·
retry-count 作为阶段指示器 · `logfs`/`logdump`/`fastboot fetch`/`oem` 日志通道

## D.5 现在的处境（诚实版）

- **原厂 DTB → flags=0（不回 fastboot）；任何主线 DTB → ~5.25 s 中止。** 这个二分稳定复现。
- 但**无法判定原厂 DTB 那一侧到底是「ABL 交接成功、内核挂住」还是「ABL 自己挂住」**。
  `panic=10` 不触发，说明不是内核 panic —— 两种可能都无法排除。
- 致命闸门在 `UpdateDeviceTree` 的 dtbo/DTB 解析里，而这条路上的每个检查我都已用实验或反汇编排除过一次。
- 剩下的可能性更多集中在 **ABL 对 DTB 二进制本身的结构性期望**（例如它期望的是一个 Qualcomm "DT table" 容器，
  而不是单个 appended DTB；注意原厂 `vendor_boot` 的 dtb 段正是 **5 个 FDT 首尾相接**的形态，见 §2.3）。

## D.6 若要继续，下一步的首选实验

**把主线 DTB 包成 Qualcomm "DT table" 容器放进 `boot.img` 的 dtb 段**（而不是单个 appended DTB）。
依据：ABL 有 `Single appended DTB found` 与 `Not the single appended DTB` 两条分支，而本机原厂
`vendor_boot` 用的是「多 FDT 拼接」形态；v2 的 dtb 段若被按 table 解析，单 DTB 就可能被判非法。
这条是 D.4 排除清单之外、且信息量最大的一次尝试。

---

# 附录 E：致命函数已完全解剖（0xA520）

## E.1 调用链（全部已确认）

```
0x7894  bl #0x9c70    → 解压内核（"Decompressing kernel image failed!!!"）；失败致命
0x7fa4  bl #0xa520    → 定位 DTB + 提取 + 叠加 Hyp/Board overlay；失败致命
0xa82c  bl #0x28ad0   → UpdateDeviceTree；**所有错误路径都返回 0，永不致命**（附录 D）
```

`0xA520..0xBE04`（栈帧 0x260）只有一个出口 `0xBE00`，返回 `[sp]`，状态字是 `[sp+0x220]`。

## E.2 它的 19 个致命出口（全部已解出）

| 地址 | EFI 码 | 消息 |
|---|---|---|
| 0xa648 | 2 INVALID_PARAMETER | `Invalid input parameters` |
| 0xa948 | 4 BAD_BUFFER_SIZE | `Dtb offset goes beyond the image size` |
| 0xaa8c | 4 | `Dtb offset goes beyond the image size` |
| 0xaa98 | 4 | `Dtb offset goes beyond the image size` |
| 0xad40 | 4 | `Integer Overflow: in single dtb header addition` |
| 0xab80 | 14 NOT_FOUND | `Not the single appended DTB` |
| 0xae54 | 14 | `Error: Device Tree blob not found` |
| 0xae60 | 14 | `Error: Device Tree blob not found` |
| 0xb4e8 | 14 | `Error: Appended Soc Device Tree blob not found` |
| 0xb5e8 | 14 | `Error: Board Dtbo blob not found` |
| 0xb5f4 | 14 | `Error: Board Dtbo blob not found` |
| 0xaf48 | 14 | `Error: HypOverlay DT is NULL` |
| 0xb7d4 | 14 | `Error: HypOverlay DT is NULL` |
| 0xb170 | 9 OUT_OF_RESOURCES | `Failed to allocate memory for HypDtbo %d` |
| 0xb2fc | 9 | `Unable to Allocate buffer for HypOverlay DT num: %d` |
| 0xb6e8 | 9 | `Unable to Allocate buffer for Overlay DT` |
| 0xb9fc | 9 | `Failed to allocate memory for HypDtbo %d` |
| 0xbb88 | 9 | `Unable to Allocate buffer for HypOverlay DT num: %d` |
| 0xbcd4 | 9 | `Unable to allocate buffer for Override DT` |

**全部集中在 DTB 定位 / DTBO 提取 / overlay 缓冲区，与显示树、`/memory`、`/chosen` 无关。**
这从另一个角度再次证明附录 B/C 那 5 次「补显示节点」不可能有效。

## E.3 v2 的字段解析是**正确**的（重要正面结论）

`0x8BB0` 函数对 `header_version ≤ 2` 有一段专门分支（`0x8bdc subs w8,w8,#2; b.hi 跳过`）：

```
0x8bf0  w = be32(hdr + 0x08) → [info+0x70] = kernel_size
0x8c18  w = be32(hdr + 0x10) → [info+0x78] = ramdisk_size
0x8c40  w = be32(hdr + 0x18) → [info+0x74] = second_size
0x8c68  w = be32(hdr + 0x24) → [info+0x6c] = page_size
0x8c90  [info+0xb8] = hdr + 0x40          ; cmdline 指针
0x8ca4  *(hdr+0x40+0x1ff) = 0             ; cmdline 截断
```

而 `0xA520` 里 DTB 段偏移的公式是：

```
a1 = 1（头部 1 页）
a2 = DIV_ROUND_UP(kernel_size,  page)
a3 = DIV_ROUND_UP(ramdisk_size, page)
a4 = DIV_ROUND_UP(second_size,  page)
dtb_offset = page * (a1 + a2 + a3 + a4)
```

代入我们的镜像：`4096 × (1 + 3095 + 1 + 0) = 0xC19000`，**与镜像中 DTB 的真实位置完全一致**。

**所以 Header v2 在结构上没有任何问题，「v2 不可用」这个说法彻底排除。**

## E.4 两次修正记录（避免误导后续）

1. **附录 C 说「致命闸门在 UpdateDeviceTree」是错的** —— 那个函数所有错误路径都 `return 0`，永不致命（附录 D 已更正）。
2. **T16 的"多 FDT"假设方向读反了**。正确极性是：
   ```
   0xaaa8  x8 = p + Align(fdt->totalsize)
   0xaab4  bl 0x4de80            ; 该位置是否为【另一个】合法 FDT
   0xaab8  cbnz w0, #0xab88      ; 是 → 跳过错误；不是 → 继续正常路径
   ```
   即：**`p + Align(totalsize)` 处若还有第二个 FDT，才报 `Not the single appended DTB`**。
   ABL 要的就是**单份** appended DTB（我们一直提供的形态），所以这条也不是死因。
   实测 T16（DTB 段放两份 FDT）：5211 ms，与单份无差别 —— 也印证了这个极性。

## E.5 结论：静态分析到此为止

- 失败点已锁死到 `0xA520` 的 19 个出口之一；
- 其中「DTB 位置 / 单份 vs 多份 / 显示节点 / `/chosen` / dtbo 内容」全部已用实验或代码排除；
- 剩下的候选集中在 **`Error: Appended Soc Device Tree blob not found`**、**`Error: Board Dtbo blob not found`**、Hyp overlay、以及 **overlay 缓冲区分配失败** 这几类；
- **再往下必须在不知道"哪一行日志"的前提下盲猜**，而每次盲猜的代价是一次 flash + 常常一次手动长按电源。

**要跨过这一步，只能拿到 ABL 的输出（UART），或者问一个知道 TB331FC 这款机器 ABL 行为的人。**

---

# 附录 F：重大更正 —— DTB 从来不是变量，Header 版本才是

## F.1 T9 不可复现，整个推理支点塌了

用**完全相同的镜像文件**重刷重测：

| 实验 | 配置 | T_back | flaps |
|---|---|---|---|
| T9 原始 | v2 + `tb331fc_stock.dtb` | — | **0**（当时判定为"ABL 放行"） |
| **T9 重测** | **同一文件原样重刷** | **5252 ms** | **1**（中止） |

**T9 的 flaps=0 是一次偶发**（USB 枚举抖动或外界干扰）。而它是附录 B/C/D 全部推理的支点。

## F.2 所有 v2 实验并排看：DTB 内容完全不影响结果

| DTB 内容 | msm-id 匹配 | T_back |
|---|---|---|
| TB128FU 原版 | 0x206 ✔ | 5343 ms |
| 各种补丁版（加节点 / 去 unit address / 双 FDT） | 0x206 ✔ | 5210–5248 ms |
| **原厂 `vendor_boot` 的 dtb 段**（1,290,690 B，5 FDT 拼接体） | **无 0x206** ✘ | 5238 ms |
| **原厂 `tb331fc_stock.dtb`** | 0x206 ✔ | **5252 ms** |
| 坏 gzip（对照组，解压前失败） | — | 4995 ms |

**结论：Header v2 的镜像无论装什么 DTB，全部在 ~5.2–5.35 s 同一处中止。**

> ⚠️ 所以：**问题就在 Header v2 这条路径本身，DTB 内容根本不影响结果。**
> **Gemini 最初的判断（应走 Android 14 GKI 的 Header v4 三分区）是对的；我此前否定它是错的。**
> 错因：拿一个不可复现的偶发数据点（T9）当支点，连续误导了 6 轮 DTB 补丁实验。

## F.3 v4 三件套实测：失败点确实变了

用 `mkv4.py` 按原厂形态打包（`boot` = 未压缩 33.3 MB Image + ramdisk 0；`init_boot` = 124 B；
`vendor_boot` = vendor_ramdisk 124 B + 主线 DTB 62,933 B + cmdline），三件套结构校验全部通过，写入 B 槽：

| | T_back | flaps | B 槽属性 |
|---|---|---|---|
| Header **v2**（全部变体） | 5210–5352 ms | 1 | `unbootable: **no**`，可反复重试 |
| Header **v4**（三件套） | **4062 ms** | 1 | `unbootable: **yes**`，**一次即判死** |

**两个变化都有意义：**
1. **快了约 1.2 s** → 走的是**另一条**失败路径，且更早（v4 用未压缩 Image，省掉 inflate；但差距大于 inflate 耗时，说明阶段确实不同）。
2. **ABL 一次就把 B 标成 unbootable** → 它判定这是一次**明确的引导失败**，不再是 v2 那种"悄悄重试"。

**所以 v4 不是万能解，但确实把失败点推到了另一个（更早的）校验上。**

## F.4 A/B 安全网行为（已实测）

B 槽 `slot-retry-count` 耗到 0 后，ABL 自动把 B 标 `unbootable: yes` 并**回落到 A 槽**，直接进 HyperOS —— **A 槽未受影响**，这是设计好的保护。

**重置 B 槽属性的方法**（只写 GPT active 标志，不碰任何分区）：

```
fastboot --set-active=a
fastboot --set-active=b
```

注意副作用：`--set-active` 会清掉被激活槽的 `successful` 位，正常启动一次即自动恢复。

## F.5 下一步（最高价值实验）

**用原厂 v4 三件套刷 B 槽做对照**（`boot_b` / `init_boot_b` / `vendor_boot_b` / `dtbo_b` / `vbmeta_b`，都是原厂文件）：

- 若 B 槽能正常进 Android → **B 槽的 v4 通路完全可用**，我们自制的 v4 失败纯粹是内容/格式问题，且有标准答案可逐字段比对；
- 若原厂 v4 在 B 槽也起不来 → 说明 B 槽本身有别的状态问题（`super`/`data`），方向完全不同。

这是唯一能一举判定"B 槽 v4 通路是否健康"的实验，且顺带把 B 槽恢复成可开机状态。

---

# 附录 G：静态 diff 抓到真 bug + 首个"ABL 接受"基线

## G.1 `mkv4.py` 段顺序 bug（真 bug，已修）

用 `hdr_diff.py` 逐字段比对时发现：原厂 `0xB19000` 处读出来是 **DTB 字符串块**，不是 ramdisk table。
全盘搜索 `vendor_ramdisk_size`（`0xB17084`）后定位到真实位置：

```
vendor_ramdisk @ 0x1000     (0xB17084)                    -> 0xB18084
dtb            @ 0xB19000   (0x13B1C2，页对齐到 0x13C000)  -> 0xC55000
vendor_ramdisk_table @ 0xC55000     ← 在 dtb【之后】
bootconfig     @ 0xC56000
```

AOSP v4 规范顺序是 **`vendor_ramdisk | dtb | table | bootconfig`**；
我原来的 `mkv4.py` 写成了 `vendor_ramdisk | table | dtb | bootconfig`。
ABL 于是把 table 的 108 字节当成 DTB 读 → 立刻硬失败。**已修正。**

原厂 table 精确字段：`size = vendor_ramdisk_size`、`offset = 0`、`type = 1`、`name = 空`、`board_id = 全 0`。

## G.2 `vbmeta` 是混淆变量（已排除）

| v4 配置 | T_back | `slot-unbootable:b` |
|---|---|---|
| 自制 vbmeta（RSA4096 flags=3，**零 descriptor**） | 4062 ms | **yes**（硬失败） |
| **原厂 vbmeta**（带 hash/chain descriptor） | **5322 ms** | **no**（软失败） |

**5322 ms 与 v2 的失败点完全重合。** 所以附录 F 的"v4 比 v2 更早失败、失败点不同"是
**自制 vbmeta 缺 descriptor 造成的假象**。

> 修正结论：**换上原厂 vbmeta 后，v2 与 v4 落到同一个失败点（~5.3 s）**，
> 说明死因在 v2/v4 **共存**的那段代码（`0xA520`），Header 版本不是变量。
> 另一个实用结论：**自制 vbmeta 不能是零 descriptor**，否则 ABL 硬拒。

## G.3 首个"ABL 接受"基线（关键进展）

把**全原厂 v4 五件套**刷进 B 槽后：

- **没回 fastboot、没有 adb，而是枚举为 `Qualcomm HS-USB Diagnostics 900E`（COM5）**
- COM5 是 QCDM 诊断口（读到 48 字节二进制协议包，**不是文本控制台**），拿不到 ABL 日志
- 长按电源无法关机，只能"电源 + 音量下"强制重启，且会再次进 900E

**解读：Android 内核已经在跑。** 900E 正是内核 diag 驱动暴露的口；用户态因 `/data`
加密绑定 A 槽而挂死。**这就是 ABL 成功交接的证据。**

> **恢复方法（实测有效）**：拔掉 USB → 长按电源 **30–40 s** 强制断电 → 按住音量下插 USB → fastboot。
> 之后 `fastboot --set-active=a` + `reboot` 回 HyperOS，数据无损。

## G.4 由此得到的干净判据（二分的基础）

| 现象 | 含义 |
|---|---|
| 进 **900E** / 长时间不回 fastboot 且无 adb | **ABL 接受，内核已启动** |
| **~5.3 s 回 fastboot** | **ABL 拒绝** |
| 4.06 s 回 fastboot + `unbootable: yes` | vbmeta 缺 descriptor（硬拒） |

## G.5 下一步：有对照的二分（每次只换一个）

从"全原厂 = 接受"出发，逐个换回自己的镜像：

| 步骤 | boot_b | init_boot_b | vendor_boot_b | 判定 |
|---|---|---|---|---|
| 基线 | 原厂 | 原厂 | 原厂 | **已知：900E（接受）** |
| ① | **主线** | 原厂 | 原厂 | 变 5.3 s → 内核镜像被拒 |
| ② | 原厂 | **主线** | 原厂 | 变 5.3 s → init_boot 被拒 |
| ③ | 原厂 | 原厂 | **主线** | 变 5.3 s → vendor_boot / DTB 被拒 |

**安全规程（务必遵守）**：
1. 每次测试前 `fastboot --set-active=b` 重置 B 的 retry；
2. 测完立刻读 `slot-unbootable:b`；若是 `yes` 或 retry 为 0，用
   `--set-active=b` → `--set-active=a` 重置（**只写 GPT 属性，不碰分区**）；
3. 预期可能进 900E 的测试，先准备好"拔线 + 长按电源 30–40 s"的恢复动作。

## G.6 当前设备状态

`current-slot: a` · `slot-retry-count:a: 7` · `slot-successful:a: yes` ·
`slot-retry-count:b: 7`（已重置）· `slot-unbootable:b: no` · 运行 HyperOS 2.0（`OS2.0.4.0.UMZCNXM`）。
**A 槽从未被写入。**



---

# 附录 H：根因确认 —— ABL 要求 DTB 带 __symbols__（决定性）

## H.1 dtbo 条目二分（用户提出的方法，成功）

信号定义：ACCEPT = 进 Qualcomm 900E（ABL 接受、内核启动）；REJECT = 回 fastboot 或回落 A 槽。

| 保留的 dtbo 条目 | 结果 |
|---|---|
| 全 45 条（原厂文件） | ACCEPT |
| 全 45 条（mkdtbo.py 重建） | ACCEPT  <- 工具已验证 |
| 0-22 | ACCEPT |
| 0-11 | ACCEPT |
| 0-5  | ACCEPT |
| 0,1,2 | ACCEPT |
| 0,1   | REJECT |
| 0,2   | ACCEPT  <- 最小必需集合 |
| 仅 2  | REJECT |

结论：dtbo 必须至少包含条目 #0 和 #2，缺任何一个都被拒。

## H.2 被接受的基础 DTB 长什么样

解析原厂 vendor_boot 的 dtb 段（0xB19000 起）第一个 FDT：

  model         Qualcomm Technologies, Inc. Khaje SoC
  compatible    qcom,khaje
  qcom,msm-id   <0x206 0x10000>
  qcom,board-id <0x0 0x0>       <- 裸 SoC 树，board 信息全由 dtbo overlay 补
  根节点 12 个: memory, ddr-regions, mem-offline, aliases, cpus, idle-states,
                psci, firmware, reserved-memory, chosen, soc, __symbols__
  __symbols__ = 829 个符号

overlay #0 的 __fixups__ 需要 85 个厂商符号（sde_te_active、wcd937x_reset、
qupv3_se1_i2c、bolero_cdc、spmi_bus、apps_smmu、dispcc ...），#2 类似。

## H.3 决定性实验

在原厂 FDT#1 上只删掉 __symbols__ 节点（279505 -> 220607 字节，其余字节不动），
dtbo 恢复原厂 45 条：

| 配置 | 结果 |
|---|---|
| 原厂 DTB（带 __symbols__） | ACCEPT |
| 原厂 DTB 删掉 __symbols__ | REJECT |

单变量、在"已验证被接受"的基线上，结论无可争议：__symbols__ 是硬性要求。

## H.4 全项目的根因

TB331FC 的 ABL 必须把厂商 dtbo 的 overlay 应用到基础 DTB 上；这些 overlay 通过
__fixups__ 按标签名引用节点，libufdt 靠基础 DTB 的 __symbols__ 解析。纯主线 DTB 不可能
提供 85+ 个厂商符号，因此 overlay 应用必然失败，ABL 随之拒启。

这一条解释了此前 25+ 次实验为何全部失败，也解释了为什么：
- 改 DTB 里任何节点/属性都无效（那些属 0x28ad0 的非致命检查）
- 换 Header 版本无效（v2/v4 都走同一条 overlay 路径）
- 换 vbmeta 无效（那只是另一个混淆变量）
- 只留匹配条目 #2 无效（还缺 #0 的 overlay 与符号）

## H.5 唯一可行的技术路线：混合 DTB（给主线树补符号）

1. 提取 dtbo #0 / #2 的全部 __fixups__ 符号名（mkdtbo.py 可导出，#0 已知 85 个）
2. 在主線 DTS 里加一个 abl-stubs 子树，为每个符号名定义一个带对应 label 的空节点
3. 用 dtc -@ 编译，使 __symbols__ 覆盖全部符号
4. 厂商 overlay 会应用到这些占位节点上（对主线内核无影响），ABL 因此放行
5. 主线内核看到的仍是主线节点结构

风险与代价：需核对 2 个 overlay 的所有 target-path（按路径指定的必须存在）；
dtc -@ 会让 DTB 变大；纯 DTS 工程，不涉及内核改动。

## H.6 当前设备状态

current-slot: a | slot-retry-count:a: 7 | slot-retry-count:b: 6 | slot-unbootable:b: no
运行 HyperOS 2.0。A 槽从未被写入。
