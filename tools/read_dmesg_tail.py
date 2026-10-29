from remote_sh import run_remote_sh

print(run_remote_sh("""
dmesg | tail -30
"""))
