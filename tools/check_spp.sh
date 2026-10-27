#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== slice_per_pkt usage in DSI host ==="
grep -rn "slice_per_pkt\|pkt_per_line\|bytes_per_pkt" drivers/gpu/drm/msm/dsi/dsi_host.c | head -25

echo
echo "=== our panel desc / dsc config: slice_count & spp ==="
grep -rn "slice_count\|slice_per_pkt\|has_dsc" drivers/gpu/drm/panel/panel-himax-hx83102.c | head -20

echo
echo "=== any local hacks left in dsi_host (search for TB331FC / slice) ==="
grep -rn "TB331FC" drivers/gpu/drm/msm/dsi/dsi_host.c | head -10
