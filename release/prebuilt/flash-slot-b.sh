#!/bin/sh
# Flash the prebuilt mainline images to slot B of a TB331FC.
#
#   ./flash-slot-b.sh                 # 刷 boot_b + vendor_boot_b
#   ./flash-slot-b.sh --with-vbmeta   # 同时刷 dtbo_b / vbmeta_b（需要你自备原厂文件）
#
# 安全策略：
#   * 只写 _b 分区，绝不动 A 槽
#   * 每一步都检查 fastboot 返回值
#   * 开始前打印当前 slot，让你二次确认
set -e

DATE=2026-10-24
BOOT="boot_b-${DATE}.img"
VBOOT="vendor_boot_b-${DATE}.img"
WITH_VBMETA=0

for a in "$@"; do
    case "$a" in
        --with-vbmeta) WITH_VBMETA=1 ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "未知参数: $a"; exit 1 ;;
    esac
done

command -v fastboot >/dev/null 2>&1 || { echo "找不到 fastboot"; exit 1; }
[ -f "$BOOT" ]  || { echo "缺少 $BOOT"; exit 1; }
[ -f "$VBOOT" ] || { echo "缺少 $VBOOT"; exit 1; }

echo "=== 校验文件 ==="
if [ -f SHA256SUMS ]; then
    sha256sum -c SHA256SUMS 2>/dev/null || echo "  (CANONICAL.dts 不在这个目录，跳过它)"
fi

echo
echo "=== 设备状态 ==="
fastboot devices
CUR=$(fastboot getvar current-slot 2>&1 | sed -n 's/current-slot: *//p')
echo "  当前 slot: ${CUR:-unknown}"

echo
echo ">>> 将会执行："
echo "    fastboot --set-active=b"
echo "    fastboot flash boot_b        $BOOT      (37.6 MB)"
echo "    fastboot flash vendor_boot_b $VBOOT     (3.1 MB)"
[ "$WITH_VBMETA" = 1 ] && echo "    fastboot flash dtbo_b / vbmeta_b        (你自备的原厂文件)"
echo
printf "确认继续？(yes/no) "
read -r ans
[ "$ans" = "yes" ] || { echo "已取消"; exit 1; }

echo
echo "=== 切换到 B 槽 ==="
fastboot --set-active=b

echo "=== 刷入 boot_b ==="
fastboot flash boot_b "$BOOT"

echo "=== 刷入 vendor_boot_b ==="
fastboot flash vendor_boot_b "$VBOOT"

if [ "$WITH_VBMETA" = 1 ]; then
    [ -f dtbo_minimal.img ] || { echo "缺少 dtbo_minimal.img（原厂 dtbo 只保留条目 0,2 重建）"; exit 1; }
    [ -f vbmeta_stock.img ] || { echo "缺少 vbmeta_stock.img（原厂 vbmeta.img 改名即可）"; exit 1; }
    echo "=== 刷入 dtbo_b ==="
    fastboot flash dtbo_b dtbo_minimal.img
    echo "=== 刷入 vbmeta_b ==="
    fastboot flash vbmeta_b vbmeta_stock.img
fi

echo
echo "=== 重启 ==="
fastboot reboot

cat <<'EOF'

刷机完成。首次启动后请注意：

  * 显示应该正常显示内核日志（tty0），画面旋转 90° 是正常的
    （面板原生 1200x1920 竖屏，平板是横屏使用）
  * 串口控制台：USB 接电脑后会出现一个 COM 口（115200 8N1）
  * 如果黑屏或卡住，回滚：
        fastboot --set-active=a
        fastboot reboot

  * 需要先准备好根文件系统（见 docs/FIRMWARE.md）
  * WiFi 还需要安装内核模块（见 docs/FIRMWARE.md 第 4 节）
EOF
