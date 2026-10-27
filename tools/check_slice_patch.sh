#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
F=$K/drivers/gpu/drm/msm/dsi/dsi_host.c
echo "=== dsi_host.c 里 DSC 打包逻辑 ==="
grep -n -A4 -B2 "bytes_per_pkt\|pkt_per_line\|slice_per_intf" "$F" | head -40
echo
echo "=== 面板驱动里的 slice 参数 ==="
grep -n "slice_per_pkt\|slice_width\|slice_height\|slice_count" \
    "$K/drivers/gpu/drm/panel/panel-himax-hx83102.c"
echo
echo "=== 仓库里的 0002 补丁内容 ==="
cat /mnt/d/TB331FCLinux/release/patches/0002-dsi_host.patch
