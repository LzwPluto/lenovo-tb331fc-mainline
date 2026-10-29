from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "=== SETTING MEM_SLEEP TO S2IDLE ==="
echo s2idle > /sys/power/mem_sleep
cat /sys/power/mem_sleep

echo "=== INSTALLING OPENSSH ==="
apk update && apk add openssh
rc-service sshd start
rc-update add sshd default

sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
rc-service sshd restart

echo "=== SSH STATUS ==="
rc-service sshd status
""", 15000))
