#!/bin/bash
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== sw_ctrl in hci_qca.c ==="
grep -n "sw_ctrl\|sw-ctrl\|bt-enable\|devm_gpiod_get" drivers/bluetooth/hci_qca.c | head -15
echo
echo "=== how sw_ctrl is used ==="
grep -n -B3 -A10 "sw_ctrl" drivers/bluetooth/hci_qca.c | head -40
