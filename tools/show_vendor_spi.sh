#!/bin/bash
cd /mnt/d/TB331FCLinux/build || exit 1

echo "=== vendor ref.dts : spi@4a80000 ==="
awk '/spi@4a80000 \{/{f=1} f{print} f&&/^\t\t\t\};/{exit}' ref.dts | head -20

echo
echo "=== vendor ref.dts : i2c@4a84000 (for comparison) ==="
awk '/i2c@4a84000 \{/{f=1} f{print} f&&/^\t\t\t\};/{exit}' ref.dts | head -14
