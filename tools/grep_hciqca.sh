#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== hci_qca power-on requirements (wcn3990) ==="
grep -rn "bt-enable-gpios\|bt_en\|wcn3990\|qcom,requires-h4-ibs\|max-speed\|vddch0\|vddio" \
    drivers/bluetooth/hci_qca.c | head -25
echo
echo "=== of_device_id table ==="
grep -n -A12 "static const struct of_device_id qca_bluetooth_of_match" drivers/bluetooth/hci_qca.c
