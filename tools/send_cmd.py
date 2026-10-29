import subprocess, base64

script = """
sed -i 's/#HandlePowerKey=poweroff/HandlePowerKey=suspend/' /etc/elogind/logind.conf
sed -i 's/#HandlePowerKeyLongPress=ignore/HandlePowerKeyLongPress=poweroff/' /etc/elogind/logind.conf
sed -i 's/#PowerKeyIgnoreInhibited=no/PowerKeyIgnoreInhibited=yes/' /etc/elogind/logind.conf
grep -E 'HandlePowerKey|PowerKeyIgnoreInhibited' /etc/elogind/logind.conf
killall -HUP elogind || rc-service elogind restart
"""

b64 = base64.b64encode(script.encode()).decode()
cmd = f"echo {b64} | base64 -d | sh"

subprocess.run([
    "powershell", "-ExecutionPolicy", "Bypass",
    "-File", r"D:\TB331FCLinux\tools\alpine.ps1",
    "-Cmd", cmd
])
