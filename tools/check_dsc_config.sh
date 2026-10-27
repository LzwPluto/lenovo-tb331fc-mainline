#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c
echo "=== 面板驱动里的 DSC 配置 ==="
grep -nE "dsc|DSC|compression|pps|slice" "$F" | head -30
echo
echo "=== DSC 结构体本体 ==="
LN=$(grep -n "drm_dsc_config" "$F" | head -1 | cut -d: -f1)
[ -n "$LN" ] && sed -n "$((LN-8)),$((LN+18))p" "$F"
echo
echo "=== DSI 模式带宽相关 ==="
grep -nE "MIPI_DSI_MODE_VIDEO|lanes|clock =|htotal|vtotal" "$F" | head -12
