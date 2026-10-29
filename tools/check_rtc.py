from remote_sh import run_remote_sh

print(run_remote_sh("""
which rtcwake || echo "no rtcwake"
ls -l /dev/rtc*
cat /sys/class/rtc/rtc0/name 2>/dev/null || true
"""))
