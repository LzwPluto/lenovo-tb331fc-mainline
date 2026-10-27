#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux/ref/android || exit 1
ls -l
echo "=== dtc full output (tail) ==="
dtc -f -I dtb -O dts -o vendor.dts vendor.fdt 2>&1 | tail -12
echo "rc=$?"
ls -l vendor.dts 2>/dev/null || echo "vendor.dts NOT created"
