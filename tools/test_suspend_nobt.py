from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "Testing with hci0 down / rfkill blocked..."
rfkill block bluetooth

echo "Unbinding hci_uart_qca from serial0-0 to prevent -110 timeout..."
echo "serial0-0" > /sys/bus/serial/drivers/hci_uart_qca/unbind 2>/dev/null || true

echo "Setting RTC alarm for +5 seconds..."
echo +5 > /sys/class/rtc/rtc0/wakealarm
echo freeze > /sys/power/state
echo "Resumed successfully without Bluetooth blocking!"
dmesg | tail -15
""", 10000))
