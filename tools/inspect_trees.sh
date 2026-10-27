#!/bin/bash
for T in ~/kbuild/linux-next-tb128fu-hx83102-panel-port ~/linux-sm6225; do
    echo "=============================================="
    echo "TREE: $T"
    echo "=============================================="
    [ -d "$T" ] || { echo "  (missing)"; continue; }
    echo "-- build artifacts --"
    ls -l --time-style=+%m-%d\ %H:%M "$T/arch/arm64/boot/Image" "$T/vmlinux" 2>/dev/null
    echo
    echo "-- dpu_core_perf.c: OPP clamp region --"
    grep -n -B6 -A18 "opp_table\|clamp\|dev_pm_opp_find_freq_floor" "$T/drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c" 2>/dev/null | head -60
    echo
    echo "-- panel driver: nvt/weak changes --"
    grep -n "nvt_ts_panel_event\|__attribute__((weak))" "$T/drivers/gpu/drm/panel/panel-himax-hx83102.c" 2>/dev/null | head -10
    echo
    echo "-- nt36523_ts.c panel_event impl --"
    grep -n -A15 "void nvt_ts_panel_event" "$T/drivers/input/touchscreen/nt36523_ts.c" 2>/dev/null | head -25
done
