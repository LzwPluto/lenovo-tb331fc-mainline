# 预编译镜像

**这是在 TB331FC 上实际验证过能启动的镜像**，可以直接刷入 B 槽使用，
不必自己编译。

> ⚠️ **全程只写 B 槽，A 槽原系统保持不动。**
> 出问题随时 `fastboot --set-active=a && fastboot reboot` 回滚。

---

## 1. 文件说明

| 文件 | 大小 | 内容 |
|---|---|---|
| `boot_b-2026-10-24.img` | 37.6 MB | 内核（未压缩 arm64 `Image`），含全部 5 个补丁 |
| `vendor_boot_b-2026-10-24.img` | 3.1 MB | initramfs + 我们的 DTB（`dtb/CANONICAL.dts` 编译而来）+ cmdline |

## 2. 内核信息

```
版本字符串 : 6.14.0-rc5-next-20250306
架构       : arm64 (aarch64)
基线       : linux-next-tb128fu-hx83102-panel-port
             （tb128fu 主线移植项目，SM6225 同平台）
已应用补丁 : patches/0001 ~ 0005（见仓库根目录 README）
```

**内核里已经启用的关键选项：**

```
显示 : DRM_MSM, panel-himax-hx83102（含 p255_inx 条目 + DSC + 标准 PPS）
     DRM_MSM_GPU_STATE, QCOM_SCM, QCOM_MDT_LOADER
存储 : BLK_DEV_LOOP, EXT4_FS, VFAT_FS, MSDOS_FS
输入 : SPI_QCOM_GENI=y, INPUT_HIMAX_V3_MMI=y, TOUCHSCREEN_NT36523_SPI=m
其他 : BACKLIGHT_PWM, USB_CONFIGFS(+ACM), CDC_ACM
无线 : CFG80211=y, MAC80211=y, RFKILL=y, ATH10K=y, ATH10K_SNOC=m,
       BT=y, BT_HCIUART=y, BT_HCIUART_QCA=y, BT_QCA=y
```

> 注意：`ATH10K_SNOC` 只能是 `=m`（其依赖 `QCOM_RPROC_COMMON` 是隐藏符号，
> 只能跟随 Q6V5 系列为 `=m`）。所以**WiFi 需要额外安装内核模块**到
> `/lib/modules/6.14.0-rc5-next-20250306/`，见 `docs/FIRMWARE.md` 第 4 节。

## 3. vendor_boot 里的 DTB

来自 `dtb/CANONICAL.dts`（SHA256 见 `SHA256SUMS`），包含全部修复：

```
ABL stub __symbols__（约 120 个符号，否则 ABL 拒绝启动）
aliases 路径修正 /soc@0/ -> /soc/
面板 compatible = "lenovo,p255-inx"
触控 touchscreen@1 = "novatek,nt36523-spi"（touchscreen@0 禁用）
DPU OPP 只保留 384 MHz（显示不花屏的关键）
wifi: vdd-3.3-ch0 / vdd-3.3-ch1
bluetooth: vddio/vddxo/vddrf/vddch0 + serial1 别名
serial@4a8c000: pinctrl-0 = qup3 四线（gpio8-11）
```

cmdline：

```
console=tty0 keep_bootcon ignore_loglevel loglevel=8 fbcon=rotate:1
clk_ignore_unused pd_ignore_unused rdinit=/init
earlycon=qcom_geni,0x4a90000 androidboot.hardware=qcom panic=10
```

## 4. 还需要自备的两个分区

这两个**不在本仓库**（属于原厂文件，且必须和你自己的设备匹配）：

| 分区 | 用什么 |
|---|---|
| `dtbo_b` | 用原厂 `dtbo.img` 里**只保留 vendor overlay 条目 {0, 2}** 重建（见下方脚本注释） |
| `vbmeta_b` | 原厂 `vbmeta.img` 原样 |

> 为什么 dtbo 只留条目 {0,2}：TB331FC 的 ABL 会应用 dtbo 里的 vendor overlay，
> 而我们的 mainline DTB 已经自带所有需要的配置，多余条目反而会冲突。
> 二分测试结果：全部 45 条 / 前 22 / 前 11 / 前 5 / {0,1,2} / {0,2} 都通过，
> 但 {0,1} 和只有 {2} 会失败 → 最小可用集合是 **{0, 2}**。

## 5. 刷机

```sh
# 最省事：用仓库里的脚本（会做安全检查）
cd prebuilt
./flash-slot-b.sh

# 或手动
fastboot --set-active=b
fastboot flash boot_b        boot_b-2026-10-24.img
fastboot flash vendor_boot_b vendor_boot_b-2026-10-24.img
fastboot flash dtbo_b        dtbo_minimal.img
fastboot flash vbmeta_b      vbmeta_stock.img
fastboot reboot
```

`init_boot_b` 放一个**空 cpio**即可（我们的 initramfs 在 vendor_boot 里）。

## 6. 校验

```sh
sha256sum -c SHA256SUMS
```

## 7. 自己重建

```sh
# 1. 打补丁 + 编译
cd linux-next-tb128fu-hx83102-panel-port
for p in ../release/patches/*.patch; do patch -p1 < "$p"; done
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) Image

# 2. 打包
python3 ../release/dtb/mkv4.py --mode boot \
    --kernel arch/arm64/boot/Image --out boot_b.img

dtc -@ -f -I dts -O dtb -o CANONICAL.dtb ../release/dtb/CANONICAL.dts
# （之后按 docs/FIRMWARE.md 的说明替换 DTB 里的 bootargs，见 mkv4.py 用法）

python3 ../release/dtb/mkv4.py --mode vendor_boot \
    --vendor-ramdisk initramfs.cpio \
    --dtb CANONICAL.dtb \
    --cmdline 'console=tty0 keep_bootcon ignore_loglevel loglevel=8 fbcon=rotate:1 \
clk_ignore_unused pd_ignore_unused rdinit=/init earlycon=qcom_geni,0x4a90000 \
androidboot.hardware=qcom panic=10' \
    --out vendor_boot_b.img
```

> `CANONICAL.dts` 是从厂商 DTB 反编译而来的，里面残留的 `bootargs` 是原厂的
> （含 `root=/dev/sda18 noinitrd` 这种对我们无用的值，而且长度固定）。
> `mkv4.py` 打包时用 `--cmdline` 指定的值才是生效的，但如果你的工具链会
> 优先读 DTB 里的 bootargs，需要按原长度替换（详见 PORTING-NOTES 附录）。
