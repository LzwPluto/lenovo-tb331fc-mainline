#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/add_ipcrtr_channels.py
echo "=== verify ==="
grep -n -A4 'qcom,glink-channels = "IPCRTR"' build/CANONICAL.dts | head -20
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_qrtr.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_qrtr.dtb
