#!/bin/bash
set -u
TREE=~/kbuild/linux-next-tb128fu-hx83102-panel-port
ZIP=/mnt/c/Users/Pluto/Desktop/linux-next-tb128fu-hx83102-panel-port.zip
TMP=~/kmcompare

echo "=== 1) dpu_core_perf.c : 你的版本 vs 原始 zip ==="
mkdir -p $TMP
cd $TMP || exit 1
if [ ! -f dpu_core_perf.orig.c ]; then
    unzip -o -q "$ZIP" "linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c" -d $TMP
    mv "$TMP/linux-next-tb128fu-hx83102-panel-port/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c" dpu_core_perf.orig.c
fi
diff -u dpu_core_perf.orig.c "$TREE/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c" | head -60

echo
echo "=== 2) nvt_panel_work 实现 ==="
grep -n -B4 -A40 "nvt_panel_work" "$TREE/drivers/input/touchscreen/nt36523_ts.c" | head -70

echo
echo "=== 3) panel 驱动里的 hook 上下文 ==="
grep -n -B8 -A4 "nvt_ts_panel_event(true)" "$TREE/drivers/gpu/drm/panel/panel-himax-hx83102.c"
