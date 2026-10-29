import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from remote_sh import run_remote_sh

script = """
su - pluto -c '
export $(cat /proc/$(pgrep -u pluto gnome-shell | head -1)/environ | tr "\\0" "\\n" | grep -E "DBUS_SESSION_BUS_ADDRESS|WAYLAND_DISPLAY|XDG_RUNTIME_DIR")

echo "=== GSD POWER BUTTON ACTION ==="
gsettings get org.gnome.settings-daemon.plugins.power power-button-action

echo "=== GSD MEDIA-KEYS POWER ==="
gsettings get org.gnome.settings-daemon.plugins.media-keys power

echo "=== GNOME SHELL OVERRIDES / KEYBINDINGS ==="
gsettings get org.gnome.desktop.session idle-delay
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout
'
"""
print(run_remote_sh(script, 5000))
