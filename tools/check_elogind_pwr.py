from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== UDEVADM EVENT0 ==="
udevadm info /dev/input/event0

echo "=== ELOGIND INHIBITORS ==="
loginctl list-inhibitors

echo "=== SYSTEM LOG (LOGREAD) ==="
logread 2>/dev/null | tail -25 || tail -25 /var/log/messages 2>/dev/null || true
"""))
