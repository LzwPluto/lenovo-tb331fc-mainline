#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

echo "=== vendor DSC properties (ref.dts) ==="
grep -nE "qcom,mdss-dsc-|qcom,compression-mode" ref.dts | head -40

echo
echo "=== vendor panel timing (p255_inx node) ==="
awk '/qcom,mdss_dsi_panel_p255_inx_fhd_video|p255_inx/{f=1} f&&/qcom,mdss-dsi-(h|v)(fp|bp|pw)-value|qcom,mdss-dsi-panel-(width|height)|qcom,mdss-dsi-panel-framerate|qcom,mdss-dsi-panel-clockrate|qcom,mdss-dsi-t-clk/{print NR": "$0} /^\t\t\t\};/{if(f)exit}' ref.dts | head -30

echo
echo "=== our driver DSC values (panel-himax-hx83102.c probe) ==="
grep -n -A20 "desc->has_dsc" ~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/panel/panel-himax-hx83102.c | head -26
