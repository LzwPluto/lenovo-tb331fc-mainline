from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== WLAN0 IP ADDRESS ==="
ip -4 addr show wlan0

echo "=== SSHD SERVICE SETUP ==="
rc-service sshd status 2>&1 || true
rc-service sshd start 2>&1 || true
rc-update add sshd default 2>&1 || true

echo "=== SSHD CONFIG CHECK ==="
grep -E '^#?PermitRootLogin' /etc/ssh/sshd_config || true
grep -E '^#?PasswordAuthentication' /etc/ssh/sshd_config || true

echo "=== MEM_SLEEP CURRENT VALUE ==="
cat /sys/power/mem_sleep
"""))
