#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== panel driver hooks ==="
grep -n "nvt_ts_panel_event" drivers/gpu/drm/panel/panel-himax-hx83102.c

echo
echo "=== dpu_core_perf clamp present? ==="
grep -n "max_opp_rate\|clamp to the highest OPP" drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c || echo "  (no clamp)"

echo
echo "=== touch driver: panel event / work ==="
grep -n "nvt_ts_panel_event\|nvt_panel_on_work\|nvt_panel_work\|schedule_work\|schedule_delayed_work" drivers/input/touchscreen/nt36523_ts.c | head -20

echo
echo "=== touch driver: what the work actually does ==="
grep -n -A30 "static void nvt_panel_on_work" drivers/input/touchscreen/nt36523_ts.c | head -40

echo
echo "=== status ==="
git status --short 2>/dev/null | head -20
echo "HEAD: $(git log --oneline -1 2>/dev/null)"
