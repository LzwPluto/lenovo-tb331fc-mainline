import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from ssh_exec import run_ssh

script = """
echo "=== MEM SLEEP ==="
cat /sys/power/mem_sleep

echo "=== PON / KEY INTERRUPTS ==="
grep -iE "pon|pwrkey|resin|key" /proc/interrupts

echo "=== INPUT DEVICES ==="
for d in /sys/class/input/event*; do
    printf "%-12s: %s\\n" "$(basename $d)" "$(cat $d/device/name 2>/dev/null)"
done

echo "=== ELOGIND STATUS AND CONFIG ==="
rc-service elogind status || true
grep -v "^#" /etc/elogind/logind.conf | grep -v "^$" || echo "(default)"

echo "=== POWER SUPPLY ==="
ls -l /sys/class/power_supply/
cat /sys/class/power_supply/mm8013/uevent 2>/dev/null || true

echo "=== UPOWER ==="
upower -d 2>/dev/null | head -30 || echo "no upower"

echo "=== RUNNING PROCESSES (GNOME/elogind/acpid) ==="
ps aux | grep -iE "gnome-shell|mutter|elogind|gsd-power|upower|acpid" | grep -v grep
"""

print(run_ssh(script, timeout=15))
