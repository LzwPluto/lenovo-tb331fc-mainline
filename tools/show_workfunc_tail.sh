#!/bin/bash
set +e
F=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c
echo "=== work_func 尾部（1080-1200）==="
sed -n '1080,1200p' "$F"
