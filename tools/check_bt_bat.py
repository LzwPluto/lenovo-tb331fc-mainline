import subprocess, base64

def run_remote_sh(script, wait_ms=4000):
    b64 = base64.b64encode(script.encode('utf-8')).decode('ascii')
    cmd = f"echo {b64} | base64 -d | sh"
    res = subprocess.run([
        "powershell", "-ExecutionPolicy", "Bypass",
        "-File", r"D:\TB331FCLinux\tools\alpine.ps1",
        "-Cmd", cmd,
        "-Wait", str(wait_ms)
    ], capture_output=True, text=True)
    return res.stdout

if __name__ == "__main__":
    test_script = """
echo "=== BATTERY UEVENT ==="
cat /sys/class/power_supply/mm8013/uevent

echo "=== BLUETOOTH DMESG ==="
dmesg | grep -iE 'qca|hci|bluetooth'

echo "=== FIRMWARE /lib/firmware/qca ==="
ls -la /lib/firmware/qca/ 2>/dev/null || echo "directory does not exist"
"""
    print(run_remote_sh(test_script, 4000))
