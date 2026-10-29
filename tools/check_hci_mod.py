import sys
from remote_sh import run_remote_sh

print(run_remote_sh("""
lsmod | grep -iE 'qca|hci|blue'
echo '---CONFIG---'
zcat /proc/config.gz 2>/dev/null | grep -iE 'HCI_UART|BT_QCA' || grep -iE 'HCI_UART|BT_QCA' /boot/config* 2>/dev/null || true
"""))
