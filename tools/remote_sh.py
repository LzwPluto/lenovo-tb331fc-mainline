import subprocess, base64, sys

def run_remote_sh(script, wait_ms=5000):
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
echo "=== INPUT DEVICES ==="
for d in /sys/class/input/event*; do
    echo -n "$(basename $d): "
    cat $d/device/name 2>/dev/null || echo "unknown"
done

echo "=== BLUETOOTH ==="
hciconfig -a 2>&1 || true
bluetoothctl show 2>&1 || true

echo "=== BATTERY ==="
cat /sys/class/power_supply/mm8013/uevent 2>&1 || true

echo "=== KERNEL DMESG (Bluetooth & PON) ==="
dmesg | grep -iE 'qca|wcn|blue|pon|pwrkey|resin|gpio-keys' | tail -25
"""
    out = run_remote_sh(test_script, 6000)
    print(out)
