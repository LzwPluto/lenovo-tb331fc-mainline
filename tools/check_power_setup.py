from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== LOGIND STATUS ==="
rc-service elogind status || true

echo "=== LOGIND CONF ==="
grep -E 'HandlePowerKey|PowerKeyIgnoreInhibited' /etc/elogind/logind.conf || true

echo "=== RUNNING COMPOSITOR ==="
ps aux | grep -E 'gnome-shell|mutter|wayland|Xorg' | grep -v grep || true

echo "=== BACKLIGHT STATUS ==="
ls -l /sys/class/backlight/* || true
cat /sys/class/backlight/*/brightness /sys/class/backlight/*/max_brightness 2>/dev/null || true

echo "=== POWER STATES SUPPORTED BY KERNEL ==="
cat /sys/power/state
cat /sys/power/mem_sleep 2>/dev/null || true
"""))
