#!/bin/bash
set +e
cd /mnt/d/TB331FCLinux || exit 1
python3 tools/disable_spi_dma.py
cd build || exit 1
dtc -@ -f -I dts -O dtb -o ref_nodma.dtb CANONICAL.dts 2>&1 | grep -E "ERROR|FATAL" | head -3
ls -l ref_nodma.dtb
