#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
F=$K/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c
echo "=== dpu_core_perf_crtc_update 里设时钟的部分 ==="
LN=$(grep -n "failed to set core clock rate" "$F" | cut -d: -f1)
echo "at line $LN"
sed -n "$((LN-40)),$((LN+10))p" "$F"
