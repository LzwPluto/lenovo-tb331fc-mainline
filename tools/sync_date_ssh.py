import time, sys
import os
sys.path.append(r"D:\TB331FCLinux\tools")
from remote_sh import run_remote_sh

now = int(time.time())
script = f"""
date -s @{now}
hwclock -w
date
apk update --allow-untrusted
apk add openssh ca-certificates --allow-untrusted
rc-service sshd start
rc-update add sshd default
sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config 2>/dev/null || true
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config 2>/dev/null || true
rc-service sshd restart 2>/dev/null || true
rc-service sshd status
"""
print(run_remote_sh(script, 25000))
