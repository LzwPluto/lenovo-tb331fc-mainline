import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from remote_sh import run_remote_sh

script = """
su - pluto -c '
export $(cat /proc/$(pgrep -u pluto gnome-shell | head -1)/environ | tr "\\0" "\\n" | grep -E "DBUS_SESSION_BUS_ADDRESS|WAYLAND_DISPLAY|XDG_RUNTIME_DIR")

echo "=== TESTING GNOME SCREENSAVER BLANK ==="
gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive true
sleep 2
echo "Brightness during ScreenSaver Active: $(cat /sys/class/backlight/ktz8866-backlight/actual_brightness)"

echo "=== TESTING GNOME SCREENSAVER UNBLANK ==="
gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.SetActive false
sleep 2
echo "Brightness after ScreenSaver Inactive: $(cat /sys/class/backlight/ktz8866-backlight/actual_brightness)"
'
"""
print(run_remote_sh(script, 8000))
