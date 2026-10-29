import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from ssh_exec import run_ssh

script = """
echo "=== TESTING S2IDLE (FREEZE) WITH RTC WAKE IN 3 SECONDS ==="
echo 0 > /sys/class/rtc/rtc0/wakealarm
echo +3 > /sys/class/rtc/rtc0/wakealarm
echo "Triggering freeze..."
echo freeze > /sys/power/state
echo "Returned from freeze! Exit code: $?"
dmesg | tail -20
"""

print(run_ssh(script, timeout=15))
