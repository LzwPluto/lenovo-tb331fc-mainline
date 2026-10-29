import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from remote_sh import run_remote_sh

script = """
mkdir -p /var/empty
chown root:root /var/empty
chmod 700 /var/empty
rc-service sshd start
rc-service sshd status
"""
print(run_remote_sh(script, 5000))
