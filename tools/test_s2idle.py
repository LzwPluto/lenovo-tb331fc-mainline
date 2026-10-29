from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "Setting RTC alarm for +5 seconds and testing s2idle suspend..."
cat /sys/class/rtc/rtc0/since_epoch
echo +5 > /sys/class/rtc/rtc0/wakealarm
echo freeze > /sys/power/state
echo "Resumed from s2idle successfully!"
cat /sys/class/rtc/rtc0/since_epoch
dmesg | tail -20
""", 10000))
