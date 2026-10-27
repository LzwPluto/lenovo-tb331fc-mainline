#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port
F=$K/drivers/input/touchscreen/nt36523_ts.c
echo "=== 文件行数 ==="
wc -l $F
echo
echo "=== 关键函数位置 ==="
grep -nE "nvt_ts_work_func|nvt_ts_irq|request_threaded_irq|nvt_clear|nvt_read_packet|0xFE|0xfe|0xAA|0xaa|release|INT_TRIGGER|gpiod_get_value|nvt_scan|0xBA|0xba" $F | head -40
