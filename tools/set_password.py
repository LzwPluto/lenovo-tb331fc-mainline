import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from remote_sh import run_remote_sh

script = """
echo "root:123456" | chpasswd
echo "pluto:123456" | chpasswd
echo "Password set to 123456 for root and pluto"
"""
print(run_remote_sh(script, 4000))
