# NetDoctor Code Signing Script
# Usage: .\scripts\code-sign.ps1 -CertificatePath "path/to/cert.pfx" -CertificatePassword "your-password"
#        .\scripts\code-sign.ps1 -CertificatePath "path/to/cert.pfx" -CertificatePassword "your-password" -TimestampServer "http://timestamp.digicert.com"
#
# Requires: signtool.exe (Windows SDK)
# To sign the MSI installer:
#   .\scripts\code-sign.ps1 -File "installer/output/NetDoctor-Setup-2.0.0.exe" -CertificatePath "cert.pfx" -CertificatePassword "pass"

param(
    [Parameter(Mandatory=$true)]
    [string]$File,                          # File to sign (e.g., dist\NetDoctor.exe or installer\output\NetDoctor-Setup-2.0.0.exe)

    [Parameter(Mandatory=$true)]
    [string]$CertificatePath,               # Path to .pfx certificate file

    [Parameter(Mandatory=$true)]
    [string]$CertificatePassword,           # Password for the certificate

    [string]$TimestampServer = "http://timestamp.digicert.com",  # RFC 3161 timestamp server
    [string]$Description = "NetDoctor - Internet Speed Test & Network Health Monitor",
    [string]$DescriptionUrl = "https://github.com/JosephJonathanFernandes/netdoctor",
    [switch]$Verbose
)

# Find signtool.exe in common Windows SDK locations
$signtoolPaths = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\*\x86\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\8.1\bin\x86\signtool.exe",
)

$signtool = $null
foreach ($pattern in $signtoolPaths) {
    $matches = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    if ($matches) {
        $signtool = $matches[0].FullName
        break
    }
}

if (-not $signtool) {
    Write-Error "signtool.exe not found. Install Windows SDK to enable code signing."
    exit 1
}

if (-not (Test-Path $File)) {
    Write-Error "File to sign not found: $File"
    exit 1
}

if (-not (Test-Path $CertificatePath)) {
    Write-Error "Certificate file not found: $CertificatePath"
    exit 1
}

# Convert password to secure string
$securePassword = ConvertTo-SecureString -String $CertificatePassword -AsPlainText -Force

# Build signtool command
$signtoolArgs = @(
    "sign",
    "/a",                                               # Use best certificate from store
    "/f", $CertificatePath,                             # Certificate file
    "/p", $CertificatePassword,                         # Certificate password
    "/tr", $TimestampServer,                            # Timestamp server
    "/td", "SHA256",                                    # Timestamp digest algorithm
    "/fd", "SHA256",                                    # File digest algorithm
    "/d", $Description,                                 # Description
    "/du", $DescriptionUrl,                             # Description URL
    $File                                               # File to sign
)

if ($Verbose) {
    $signtoolArgs += "/v"
}

Write-Host "Signing $File..." -ForegroundColor Cyan
Write-Host "Using: $signtool" -ForegroundColor Gray

try {
    & $signtool @signtoolArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Code signing completed successfully!" -ForegroundColor Green
        
        # Verify the signature
        Write-Host "Verifying signature..." -ForegroundColor Cyan
        & $signtool "verify" "/v" "/a" $File
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Signature verified successfully!" -ForegroundColor Green
        } else {
            Write-Warning "Signature verification failed."
        }
    } else {
        Write-Error "Code signing failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} catch {
    Write-Error "Code signing error: $_"
    exit 1
}
