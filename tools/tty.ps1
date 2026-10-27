# Sends $env:TTYCMD to the tablet's USB serial console and prints the reply.
# Using an environment variable avoids all command-line quoting problems.
$cmd = $env:TTYCMD
$wait = if ($env:TTYWAIT) { [int]$env:TTYWAIT } else { 1500 }
$port = if ($env:TTYPORT) { $env:TTYPORT } else { "COM3" }

if (-not $cmd) { Write-Error "TTYCMD not set"; exit 1 }

$sp = New-Object System.IO.Ports.SerialPort $port, 115200, None, 8, One
$sp.ReadTimeout = 3000
$sp.Open()
Start-Sleep -Milliseconds 250
$sp.DiscardInBuffer()
$sp.Write("`n")
Start-Sleep -Milliseconds 200
$sp.Write($cmd + "`n")
Start-Sleep -Milliseconds $wait
$out = $sp.ReadExisting()
$sp.Close()
$out
