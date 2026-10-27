#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
echo "=== DPU 里 partial update 相关开关 ==="
grep -rn "partial_update\|partial update\|_pu\b\|PU_" "$K/drivers/gpu/drm/msm/disp/dpu1/"*.c "$K/drivers/gpu/drm/msm/disp/dpu1/"*.h 2>/dev/null | grep -iE "module_param|debugfs|enable|disable|bool" | head -15
echo
echo "=== 是否有模块参数 ==="
grep -rn "module_param" "$K/drivers/gpu/drm/msm/disp/dpu1/"*.c 2>/dev/null | head -10
echo
echo "=== msm 整体的模块参数 ==="
grep -rn "module_param" "$K/drivers/gpu/drm/msm/msm_drv.c" 2>/dev/null | head -10
