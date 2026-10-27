#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== our mdss compatible in DTS ==="
grep -n -A6 "display-subsystem@5e00000" /mnt/d/TB331FCLinux/build/ref_nvt3.dts | head -12

echo
echo "=== msm_mdss data structs ==="
sed -n '560,660p' drivers/gpu/drm/msm/msm_mdss.c

echo
echo "=== dpu_plane format_mod_supported ==="
sed -n '1555,1600p' drivers/gpu/drm/msm/disp/dpu1/dpu_plane.c
