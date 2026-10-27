#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== DPU pitch / stride checks ==="
grep -rn "pitch\|stride" drivers/gpu/drm/msm/disp/dpu1/*.c | grep -iE "align|%|check|invalid|err" | head -20

echo
echo "=== framebuffer pitch checks in msm ==="
grep -rn "pitch" drivers/gpu/drm/msm/msm_fb.c drivers/gpu/drm/msm/msm_gem.c 2>/dev/null | head -15

echo
echo "=== UBWC support for display? ==="
grep -rn "UBWC\|ubwc" drivers/gpu/drm/msm/disp/dpu1/dpu_formats.c 2>/dev/null | head -12
grep -rn "ubwc" drivers/gpu/drm/msm/disp/dpu1/dpu_plane.c 2>/dev/null | head -12

echo
echo "=== DSI widebus / dsc requirements ==="
grep -rn "widebus\|WIDEBUS" drivers/gpu/drm/msm/dsi/*.c | head -12
