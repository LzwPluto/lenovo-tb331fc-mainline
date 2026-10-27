#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c
FW=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== nvt_sw_reset_idle / nvt_bootloader_reset: definitions ==="
grep -rn -A12 "void nvt_sw_reset_idle(void)\|void nvt_bootloader_reset(void)" $TS $FW | head -40

echo
echo "=== call sites of all reset helpers ==="
grep -rn "nvt_sw_reset_idle\|nvt_bootloader_reset\|SWRST_N8_ADDR\|ENG_RST_ADDR" $TS $FW | head -25

echo
echo "=== any HARDWARE reset (gpio) inside the touch driver ==="
grep -rn "reset_gpio\|reset-gpio\|gpiod_set_value\|gpio_set_value\|hw_reset" $TS $FW | head -25

echo
echo "=== download_init / download_firmware (where resets may happen) ==="
grep -n -A18 "nvt_download_init(void)" $FW | head -22
