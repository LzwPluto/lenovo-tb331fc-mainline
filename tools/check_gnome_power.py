from remote_sh import run_remote_sh

print(run_remote_sh("""
su - pluto -c '
export $(cat /proc/$(pgrep -u pluto gnome-shell | head -1)/environ | tr "\\0" "\\n" | grep -E "DBUS_SESSION_BUS_ADDRESS|WAYLAND_DISPLAY|XDG_RUNTIME_DIR")
echo "=== GNOME POWER BUTTON ACTION ==="
gsettings get org.gnome.settings-daemon.plugins.power power-button-action
echo "=== GNOME SLEEP INACTIVE AC TYPE ==="
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type
echo "=== GNOME SLEEP INACTIVE BATTERY TYPE ==="
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type
echo "=== GNOME MEDIA-KEYS POWER SHORTCUT ==="
gsettings get org.gnome.settings-daemon.plugins.media-keys power
'
"""))
