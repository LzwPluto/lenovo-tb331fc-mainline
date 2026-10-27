param()
$b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("D:\TB331FCLinux\rootfs\draw.py"))
$cmd = "echo " + $b64 + " | base64 -d > /root/draw.py"
& "D:\TB331FCLinux\tools\alpine.ps1" -Cmd $cmd
& "D:\TB331FCLinux\tools\alpine.ps1" -Cmd "ls -la /root/draw.py; head -n 5 /root/draw.py"
