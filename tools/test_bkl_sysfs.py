from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== DRM CONNECTOR DETAILS ==="
for c in /sys/class/drm/card*-*; do
    [ -d "$c" ] && echo "$c: status=$(cat $c/status 2>/dev/null) dpms=$(cat $c/dpms 2>/dev/null)"
done

echo "=== BACKLIGHT ATTRIBUTES ==="
cat /sys/class/backlight/ktz8866-backlight/brightness
cat /sys/class/backlight/ktz8866-backlight/actual_brightness
cat /sys/class/backlight/ktz8866-backlight/max_brightness

echo "=== TEST TURNING OFF BACKLIGHT VIA SYSFS ==="
echo 0 > /sys/class/backlight/ktz8866-backlight/brightness
sleep 1
echo "actual after setting 0: $(cat /sys/class/backlight/ktz8866-backlight/actual_brightness)"
sleep 1
echo 500 > /sys/class/backlight/ktz8866-backlight/brightness
echo "actual after restoring 500: $(cat /sys/class/backlight/ktz8866-backlight/actual_brightness)"
""", 6000))
