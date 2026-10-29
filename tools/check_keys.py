import sys
sys.path.append(r"D:\TB331FCLinux\tools")
from ssh_exec import run_ssh

script = """
for ev in /sys/class/input/event*; do
    name=$(cat $ev/device/name 2>/dev/null)
    ev_bits=$(cat $ev/device/capabilities/ev 2>/dev/null)
    key_bits=$(cat $ev/device/capabilities/key 2>/dev/null)
    echo "$(basename $ev): $name | EV=$ev_bits | KEY=$key_bits"
done

echo "=== GPIO KEYS IN DT ==="
for d in /sys/firmware/devicetree/base/*gpio*keys*; do
    echo "Found node: $d"
    ls -la $d 2>/dev/null
    for sub in $d/*; do
        if [ -d "$sub" ]; then
            echo "  Subnode: $(basename $sub)"
            cat $sub/label 2>/dev/null && echo ""
            cat $sub/linux,code 2>/dev/null | hexdump -C || true
        fi
    done
done

echo "=== PMIC PON IN DT ==="
for d in /sys/firmware/devicetree/base/soc/*/*pon*; do
    echo "PON node: $d"
    ls -la $d 2>/dev/null
    for sub in $d/*; do
        if [ -d "$sub" ]; then
            echo "  Subnode: $(basename $sub)"
            cat $sub/compatible 2>/dev/null && echo ""
            cat $sub/interrupts 2>/dev/null | hexdump -C || true
        fi
    done
done
"""

print(run_ssh(script, timeout=10))
