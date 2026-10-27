#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/fix_bt_supplies.py
echo "=== bluetooth node now ==="
awk '/compatible = "qcom,wcn3990-bt"/,/};/' build/CANONICAL.dts | head -10
echo "=== build dtb ==="
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_btsup.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_btsup.dtb
