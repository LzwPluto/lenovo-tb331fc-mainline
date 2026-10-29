from remote_sh import run_remote_sh

print(run_remote_sh("""
grep -E 'pm8941|pwrkey|resin|gpio-keys' /proc/interrupts
"""))
