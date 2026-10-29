import subprocess, sys

def run_ssh(cmd, timeout=10):
    res = subprocess.run([
        "ssh", "-i", r"C:\Users\Pluto\.ssh\id_ed25519",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "root@10.227.201.127",
        cmd
    ], capture_output=True, text=True, timeout=timeout)
    return res.stdout + res.stderr

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "uname -a"
    print(run_ssh(cmd))
