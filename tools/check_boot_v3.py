from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== UNAME ==="
uname -a

echo "=== BACKLIGHT & PANEL DMESG ==="
dmesg | grep -iE 'ktz|backlight|p255|himax|hx83102'

echo "=== DRM CONNECTORS ==="
ls -l /sys/class/drm/card*-*/ 2>/dev/null || true

echo "=== BACKLIGHT SYSFS ==="
ls -l /sys/class/backlight/* 2>/dev/null || true
""", 6000))
