#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== our driver: nvt_read_pid ==="
grep -n -A15 "static int32_t nvt_read_pid" drivers/input/touchscreen/nt36523_ts.c | head -25

echo
echo "=== mem_map struct fields (chip map) ==="
grep -n -A40 "struct nvt_ts_mem_map" drivers/input/touchscreen/nt36523_mem_map.h | head -45

echo
echo "=== actual map used ==="
grep -n -B2 -A30 "static const struct nvt_ts_mem_map" drivers/input/touchscreen/nt36523_mem_map.h | head -45
