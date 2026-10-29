import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from remote_sh import run_remote_sh

script = """
apk add evtest
echo "evtest installed"
"""
print(run_remote_sh(script, 10000))
