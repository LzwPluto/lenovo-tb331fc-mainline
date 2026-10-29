from remote_sh import run_remote_sh

print(run_remote_sh("""
echo "Running loginctl suspend..."
loginctl suspend
echo "Command exited with $?"
sleep 2
dmesg | tail -20
"""))
