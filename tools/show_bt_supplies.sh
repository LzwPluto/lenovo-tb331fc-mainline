#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== qca_soc_data_wcn3990 ==="
sed -n '2080,2095p' drivers/bluetooth/hci_qca.c
echo
echo "=== our bluetooth DT node ==="
sed -n '/bluetooth {/,/};/p' /mnt/d/TB331FCLinux/build/CANONICAL.dts | head -12
