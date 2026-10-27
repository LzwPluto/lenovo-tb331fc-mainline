# push_file.ps1 - push one file into the running Alpine system over the serial
# console using base64 + a single heredoc per file (USB flow control paces it).
param(
    [string]$Path,
    [string]$Remote = '',
    [string]$Port = 'COM3'
)

if (-not (Test-Path $Path)) { Write-Error "no such file: $Path"; exit 1 }
if (-not $Remote) { $Remote = '/tmp/' + (Split-Path $Path -Leaf) }

$bytes = [System.IO.File]::ReadAllBytes($Path)
$b64 = [Convert]::ToBase64String($bytes)
$sum = (Get-FileHash $Path -Algorithm MD5).Hash.ToLower()

$sp = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$sp.ReadTimeout = 500
$sp.WriteTimeout = 60000
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

Write-Host ("pushing {0} ({1:N0} bytes -> {2:N0} b64) to {3}" -f (Split-Path $Path -Leaf), $bytes.Length, $b64.Length, $Remote)
$sw = [System.Diagnostics.Stopwatch]::StartNew()

$sp.Write("base64 -d > $Remote << 'TBEOF'`r`n")
Start-Sleep -Milliseconds 150
# stream in small chunks: one huge Write() overflows the USB serial buffer and
# kills the port
$payload = New-Object System.Text.StringBuilder
for($i=0; $i -lt $b64.Length; $i += 200){
    $len = [Math]::Min(200, $b64.Length - $i)
    [void]$payload.Append($b64.Substring($i,$len)).Append("`r`n")
}
$all = $payload.ToString()
$chunk = 1024
for($i=0; $i -lt $all.Length; $i += $chunk){
    $len = [Math]::Min($chunk, $all.Length - $i)
    $sp.Write($all.Substring($i, $len))
    Start-Sleep -Milliseconds 60
}
Start-Sleep -Milliseconds 400
$sp.Write("TBEOF`r`n")
[void](ReadUntil '#\s*$' 40000)

$sp.DiscardInBuffer()
$sp.Write("md5sum $Remote`r`n")
$r = ReadUntil '#\s*$' 8000
$sw.Stop()

$r -split "`r?`n" | Where-Object { $_ -match 'md5|No such' } | ForEach-Object { Write-Host $_ }
if($r -match $sum){
    Write-Host ("OK  md5 matches, {0:N1}s" -f $sw.Elapsed.TotalSeconds)
} else {
    Write-Host ("MISMATCH - expected {0}, {1:N1}s" -f $sum, $sw.Elapsed.TotalSeconds)
}
$sp.Close()
