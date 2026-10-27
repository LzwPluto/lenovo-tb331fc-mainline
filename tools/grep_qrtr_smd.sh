#!/bin/bash
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/net/qrtr/qrtr-smd.c
echo "=== driver file ==="
ls -l $F 2>/dev/null || find drivers/net/qrtr -name '*smd*'
echo
echo "=== probe / failed to create endpoint ==="
grep -n -B20 "failed to create endpoint" $F | head -40
echo
echo "=== what returns ENOMEM in qrtr core endpoint alloc ==="
grep -n -A30 "int qrtr_endpoint_register" drivers/net/qrtr/af_qrtr.c | head -40
