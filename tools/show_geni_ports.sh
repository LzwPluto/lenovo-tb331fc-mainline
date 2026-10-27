#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== get_port_from_line ==="
grep -n -B2 -A20 "static struct qcom_geni_serial_port \*get_port_from_line" drivers/tty/serial/qcom_geni_serial.c
echo
echo "=== array size / max ports ==="
grep -n "qcom_geni_serial_ports\[\|QCOM_GENI_MAX_PORTS\|qcom_geni_console_ports\[" drivers/tty/serial/qcom_geni_serial.c | head -8
echo
echo "=== port array definition ==="
grep -n -A12 "static struct qcom_geni_serial_port qcom_geni_serial_ports" drivers/tty/serial/qcom_geni_serial.c | head -20
