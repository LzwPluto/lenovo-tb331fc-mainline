# transfer_apks.ps1 - push .apk files into the running Alpine system over the
# serial console, base64 encoded, then install them with apk.
# Keeps one connection open so it is fast.
param(
    [string]$Port = 'COM3',
    [string]$Src  = 'D:\TB331FCLinux\rootfs\alpine\apks',
    [string[]]$Only = @('wayland-libs-server-1.25.0-r0.apk','libseat-0.9.3-r0.apk',
                        'seatd-0.9.3-r0.apk','seatd-openrc-0.9.3-r0.apk',
                        'evtest-1.36-r0.apk')
)

$sp = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$sp.ReadTimeout = 500
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
function SendLine($s){ $sp.Write($s + "`r`n") }

# login if needed
$sp.DiscardInBuffer(); SendLine ''
$seen = ReadUntil '#|login:' 2500
if($seen -match 'login:'){
    SendLine 'root'
    $p = ReadUntil 'Password:|#' 4000
    if($p -match 'Password:'){ SendLine ''; $seen = ReadUntil '#\s*$' 8000 }
    else { $seen = $p }
}
Write-Host "connected"

SendLine 'mkdir -p /tmp/apks'
ReadUntil '#\s*$' 3000 | Out-Null

foreach($f in $Only){
    $path = Join-Path $Src $f
    if(-not (Test-Path $path)){ Write-Host "skip missing $f"; continue }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $b64   = [Convert]::ToBase64String($bytes)
    $out   = "/tmp/apks/$f.b64"
    Write-Host ("sending {0} ({1:N0} bytes, b64 {2:N0})" -f $f, $bytes.Length, $b64.Length)

    SendLine "rm -f $out"
    ReadUntil '#\s*$' 2000 | Out-Null

    $i = 0; $chunk = 400
    while($i -lt $b64.Length){
        $len = [Math]::Min($chunk, $b64.Length - $i)
        $piece = $b64.Substring($i, $len)
        SendLine "printf %s '$piece' >> $out"
        $i += $len
        # keep the pipe drained so the tty doesn't overrun
        if(([Math]::Floor($i / $chunk) % 25) -eq 0){ [void]$sp.ReadExisting(); Start-Sleep -Milliseconds 60 }
    }
    ReadUntil '#\s*$' 8000 | Out-Null
    SendLine "base64 -d $out > /tmp/apks/$f && rm -f $out && ls -l /tmp/apks/$f"
    $r = ReadUntil '#\s*$' 8000
    Write-Host ($r -replace "`r",'')
}

SendLine 'ls -l /tmp/apks/ | tail -10'
Write-Host (ReadUntil '#\s*$' 5000)
$sp.Close()
