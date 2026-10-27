#!/bin/bash
set +e
K=~/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen
echo "=== struct nvt_ts_data 定义位置 ==="
grep -rn "struct nvt_ts_data" "$K"/*.h "$K"/*.c | head -5
echo
echo "=== 定义体 ==="
LN=$(grep -n "^struct nvt_ts_data" "$K/nt36523_ts.c" | head -1 | cut -d: -f1)
if [ -z "$LN" ]; then
    LN=$(grep -rn "^struct nvt_ts_data" "$K"/*.h | head -1)
    echo "in header: $LN"
    F=$(echo "$LN" | cut -d: -f1); N=$(echo "$LN" | cut -d: -f2)
else
    F="$K/nt36523_ts.c"; N="$LN"
fi
echo "file=$F line=$N"
sed -n "${N},$((N+80))p" "$F"
echo
echo "=== irq_gpio / lock / delayed_work 相关字段 ==="
grep -nE "irq_gpio|struct mutex|delayed_work|struct work|nvt_work|esd" "$K/nt36523_ts.c" | head -20
