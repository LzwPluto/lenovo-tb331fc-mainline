#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== module build progress ==="
if pgrep -f "make.*modules" >/dev/null; then
    echo "  still building..."
else
    echo "  finished"
fi
tail -3 /tmp/mods.log 2>/dev/null
echo "  .ko count: $(find . -name '*.ko' 2>/dev/null | wc -l)"
echo
echo "=== ath10k WCN3990 firmware names ==="
grep -rn "wlanmdsp\|bdwlan\|firmware_name\|dt_firmware" \
    drivers/net/wireless/ath/ath10k/qmi.c drivers/net/wireless/ath/ath10k/snoc.c \
    drivers/net/wireless/ath/ath10k/core.c 2>/dev/null | grep -iE "wlanmdsp|bdwlan|firmware_name|dt_firm" | head -10
echo
echo "=== hci_qca firmware names ==="
grep -rn "crbtfw\|crnv\|firmware-name\|qca/.*tlv\|EUNIVERSAL\|WCN3990" \
    drivers/bluetooth/btqca.c drivers/bluetooth/hci_qca.c 2>/dev/null | grep -iE "crbtfw|crnv|\.tlv|\.bin" | head -12
