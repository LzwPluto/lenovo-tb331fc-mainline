# pull_file.ps1 - pull one file from the Alpine device over the serial console.
# Uses a single heredoc of base64 (the USB stack provides flow control).
param(
    [string]$Remote = '/mnt/shot.png',
    [string]$Out    = 'D:\TB331FCLinux\build\shot.png',
    [string]$Port   = 'COM3'
)

$sp = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$sp.ReadTimeout = 400
$sp.WriteTimeout = 60000
$sp.Open()
Start-Sleep -Milliseconds 400

function RU($p,$ms){ $b=''; $sw=[Diagnostics.Stopwatch]::StartNew()
    while($sw.ElapsedMilliseconds -lt $ms){ try{$b+=$sp.ReadExisting()}catch{}
        if($b -match $p){ return $b }; Start-Sleep -Milliseconds 60 }
    return $b }

$sp.DiscardInBuffer(); $sp.Write("`r`n")
$s = RU '#|login:' 3000
if($s -match 'login:'){ $sp.Write("root`r`n"); $p = RU 'Password:|#' 4000
    if($p -match 'Password:'){ $sp.Write("`r`n"); RU '#\s*$' 8000 | Out-Null } }
Write-Host "connected"

# size + base64 on the device
$sp.Write("wc -c < $Remote; base64 $Remote | wc -c`r`n")
$r = RU '#\s*$' 20000
Write-Host ($r -replace "`r",'')

# stream base64 through a heredoc into a local file
$sp.Write("base64 $Remote > /tmp/xfer.b64; wc -c < /tmp/xfer.b64`r`n")
$r = RU '#\s*$' 60000
$sz = ($r -split "`n" | Where-Object { $_ -match '^\s*\d+\s*$' } | Select-Object -Last 1)
Write-Host "b64 size on device: $sz"

$sw = [Diagnostics.Stopwatch]::StartNew()
$sp.Write("cat /tmp/xfer.b64`r`n")
$buf = New-Object System.Text.StringBuilder
$deadline = $sw.Elapsed.TotalSeconds + 240
while($sw.Elapsed.TotalSeconds -lt $deadline){
    try { $chunk = $sp.ReadExisting() } catch { $chunk = '' }
    if($chunk){ [void]$buf.Append($chunk) }
    else { Start-Sleep -Milliseconds 80 }
    $txt = $buf.ToString()
    if($txt -match '#\s*$' -and $txt.Length -gt 1000){ break }
}
$sp.Close()

$all = $buf.ToString()
$lines = $all -split "`r?`n" | Where-Object { $_ -match '^[A-Za-z0-9+/=]+$' }
$b64 = ($lines -join '')
Write-Host ("received {0} base64 chars, {1:N1}s" -f $b64.Length, $sw.Elapsed.TotalSeconds)
try {
    [IO.File]::WriteAllBytes($Out, [Convert]::FromBase64String($b64))
    Write-Host ("wrote {0} bytes -> {1}" -f (Get-Item $Out).Length, $Out)
} catch { Write-Host "base64 decode failed: $_" }
