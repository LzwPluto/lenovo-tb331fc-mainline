from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== IRQ 21 COUNT ==="
grep -E 'pm8941|pwrkey|resin|gpio-keys' /proc/interrupts

echo "=== ELOGIND LOGS ==="
loginctl list-sessions
loginctl session-status 2>/dev/null || true

echo "=== DMESG LAST 20 ==="
dmesg | tail -20
"""))
