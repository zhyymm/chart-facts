# Download Swiss Ephemeris ephemeris files for 1800-2399 AD.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dest = Join-Path $Root "ephe"
$Base = "https://www.astro.com/ftp/swisseph/ephe"

New-Item -ItemType Directory -Force -Path $Dest | Out-Null

foreach ($file in @("sepl_18.se1", "semo_18.se1")) {
    $target = Join-Path $Dest $file
    if (Test-Path $target) {
        Write-Host "Already exists: $target"
        continue
    }
    Write-Host "Downloading $file..."
    Invoke-WebRequest -Uri "$Base/$file" -OutFile $target
}

Write-Host "Done. Ephemeris files in $Dest"
