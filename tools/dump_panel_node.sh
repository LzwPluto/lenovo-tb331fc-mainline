#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

echo "=== all panel nodes with 1200 width (0x4b0) ==="
grep -n "qcom,mdss-dsi-panel-width = <0x4b0>" ov0.dts | head

echo
echo "=== full dump: the p255_inx / 1200-wide panel node ==="
N=$(grep -n "qcom,mdss-dsi-panel-width = <0x4b0>" ov0.dts | head -1 | cut -d: -f1)
echo "width line = $N"
if [ -n "$N" ]; then
    START=$((N-40))
    END=$((N+80))
    sed -n "${START},${END}p" ov0.dts | grep -nE "qcom,mdss-dsi-(h|v)(fp|bp|pw)-value|panel-width|panel-height|panel-framerate|panel-clockrate|dsi-panel-type|dsc-|compression-mode|t-clk|panel-orientation|refresh" | head -40
fi

echo
echo "=== every compression-mode block with its panel size ==="
grep -n "qcom,mdss-dsi-panel-width\|qcom,mdss-dsi-panel-height\|qcom,mdss-dsc-slice-per-pkt\|qcom,mdss-dsc-slice-width\|qcom,mdss-dsc-slice-height\|compression-mode" ov0.dts | sed -n '1,80p'
