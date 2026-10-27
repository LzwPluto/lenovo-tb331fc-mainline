# transfer_apks2.ps1 - stream .apk files into the running Alpine over the serial
# console using a single heredoc per file (no per-chunk round trips: the USB
# stack provides the flow control).
param(
    [string]$Port = 'COM3',
    [string]$Src  = 'D:\TB331FCLinux\rootfs\alpine\apks',
    [string[]]$Files = @(
        'wayland-libs-server-1.25.0-r0.apk',
        'libseat-0.9.3-r0.apk',
        'seatd-0.9.3-r0.apk',
        'seatd-openrc-0.9.3-r0.apk',
        'evtest-1.36-r0.apk')
)

$sp = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$sp.ReadTimeout = 500
$sp.WriteTimeout = 30000
$sp.Open()
Start-Sleep -Milliseconds 300

function ReadUntil($pattern, $timeoutMs) {
    $buf=''; $sw=[System.Diagnostics.Stopwatch]::StartNew()
    while($sw.ElapsedMilliseconds -lt $timeoutMs){
        try { $buf += $sp.ReadExisting() } catch {}
        if($buf -match $pattern){ return $buf }
        Start-Sleep -Milliseconds 80
    }
    return $buf
}

$sp.DiscardInBuffer()
$sp.Write("`r`n")
$seen = ReadUntil '#|login:' 2500
if($seen -match 'login:'){
    $sp.Write("root`r`n")
    $p = ReadUntil 'Password:|#' 4000
    if($p -match 'Password:'){ $sp.Write("`r`n"); $seen = ReadUntil '#\s*$' 8000 }
}
Write-Host "connected"
$sp.Write("mkdir -p /tmp/apks`r`n"); ReadUntil '#\s*$' 3000 | Out-Null

foreach($f in $Files){
    $path = Join-Path $Src $f
    if(-not (Test-Path $path)){ Write-Host "skip $f"; continue }
    $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($path))
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    # open the heredoc, then stream the payload as CRLF lines
    $sp.Write("base64 -d > /tmp/apks/$f << 'TBEOF'`r`n")
    Start-Sleep -Milliseconds 120
    $sb = New-Object System.Text.StringBuilder
    for($i=0; $i -lt $b64.Length; $i += 200){
        $len = [Math]::Min(200, $b64.Length - $i)
        [void]$sb.Append($b64.Substring($i,$len)).Append("`r`n")
    }
    $sp.Write($sb.ToString())
    Start-Sleep -Milliseconds 200
    $sp.Write("TBEOF`r`n")

    $r = ReadUntil 'TBEOF|#\s*$' 20000
    $r2 = ReadUntil '#\s*$' 5000
    $sw.Stop()
    $chk = ReadUntil '#\s*$' 0
    $sp.Write("ls -l /tmp/apks/$f`r`n")
    $l = ReadUntil '#\s*$' 5000
    Write-Host ("{0}  {1:N0} B -> {2:N0} B b64 in {3:N1}s" -f $f, (Get-Item $path).Length, $b64.Length, $sw.Elapsed.TotalSeconds)
    Write-Host ($l -replace "`r",'')
}

$sp.Write("ls -l /tmp/apks/`r`n")
Write-Host (ReadUntil '#\s*$' 5000)
$sp.Close()
