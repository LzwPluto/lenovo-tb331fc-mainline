from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== TESTING DPMS OFF ==="
echo 500 > /sys/class/backlight/ktz8866-backlight/brightness
echo "brightness before: $(cat /sys/class/backlight/ktz8866-backlight/actual_brightness)"

echo Off > /sys/class/drm/card1-DSI-1/dpms 2>/dev/null || echo "legacy dpms sysfs not writable"
sleep 1
echo "dpms state: $(cat /sys/class/drm/card1-DSI-1/dpms 2>/dev/null)"
echo "brightness during dpms off: $(cat /sys/class/backlight/ktz8866-backlight/actual_brightness)"

sleep 2
echo On > /sys/class/drm/card1-DSI-1/dpms 2>/dev/null || true
echo "dpms restored: $(cat /sys/class/drm/card1-DSI-1/dpms 2>/dev/null)"
""", 6000))
