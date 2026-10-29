import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from ssh_exec import run_ssh

script = """
find /sys/firmware/devicetree/base -name "*pwrkey*" -o -name "*resin*" -o -name "*pon*"
"""
print(run_ssh(script))
