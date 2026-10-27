#!/bin/bash
# Look for WiFi/BT firmware names inside the factory NON-HLOS.bin (a FAT image).
cd "/mnt/d/TB331FC_GSI_Kit/08_一键刷机/fw" || { echo "fw dir not found"; exit 1; }

if [ ! -f NON-HLOS.bin ]; then
    echo "NON-HLOS.bin missing"
    exit 1
fi

echo "NON-HLOS.bin size: $(du -m NON-HLOS.bin | cut -f1) MB"
echo
for s in wlanmdsp bdwlan crbtfw crnv adspso modem.b00; do
    n=$(grep -ac "$s" NON-HLOS.bin 2>/dev/null)
    printf "  %-12s hits=%s\n" "$s" "${n:-0}"
done
