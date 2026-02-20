# Consolidate PROINSULATIONESTIMATION project folders into this repo
# Run from repo root: .\scripts\consolidate-project-folders.ps1
# Use -DryRun (default) to only report; use -Copy to copy missing/different files.

param(
    [switch]$Copy = $false  # Pass -Copy to copy files; otherwise dry-run only
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot | Split-Path -Parent

# Edit these paths to match your other project variants (full paths).
$OtherProjectRoots = @(
    "G:\My Drive\code\App_packs\insulation_estimator_cloud_run"
    # "G:\My Drive\code\PROINSULATIONESTIMATION-other"
    # Add more paths as needed
)

# Extensions we care about for comparison
$RelevantExtensions = @(".py", ".ts", ".tsx", ".json", ".md", ".yml", ".yaml", ".sh", ".ps1", ".toml")

function Get-RelativePaths {
    param([string]$Root, [string[]]$Extensions)
    $all = @()
    foreach ($ext in $Extensions) {
        Get-ChildItem -Path $Root -Recurse -File -Filter "*$ext" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.streamlit)\\' } |
            ForEach-Object { $_.FullName.Replace($Root.TrimEnd('\') + "\", "").Replace("\", "/") } |
            ForEach-Object { $all += $_ }
    }
    $all | Sort-Object -Unique
}

function Get-FileHashSafe {
    param([string]$BasePath, [string]$RelativePath)
    $full = Join-Path $BasePath ($RelativePath -replace "/", [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path $full)) { return $null }
    try {
        return (Get-FileHash -Path $full -Algorithm SHA256).Hash
    } catch { return $null }
}

Write-Host "Repo root: $RepoRoot"
$DryRun = -not $Copy
Write-Host "Mode: $(if ($DryRun) { 'DryRun (report only)' } else { 'Copy' })"
Write-Host ""

$canonicalFiles = Get-RelativePaths -Root $RepoRoot -Extensions $RelevantExtensions
$canonicalSet = @{}
foreach ($f in $canonicalFiles) { $canonicalSet[$f] = $true }

foreach ($OtherRoot in $OtherProjectRoots) {
    if (-not (Test-Path $OtherRoot)) {
        Write-Host "Skip (not found): $OtherRoot" -ForegroundColor Yellow
        continue
    }

    Write-Host "Comparing with: $OtherRoot" -ForegroundColor Cyan
    $otherFiles = Get-RelativePaths -Root $OtherRoot -Extensions $RelevantExtensions

    $onlyInOther = $otherFiles | Where-Object { -not $canonicalSet[$_] }
    $inBoth = $otherFiles | Where-Object { $canonicalSet[$_] }

    if ($onlyInOther.Count -gt 0) {
        Write-Host "  Only in other folder ($($onlyInOther.Count)):"
        foreach ($rel in $onlyInOther) {
            Write-Host "    + $rel"
            if (-not $DryRun -and $Copy) {
                $src = Join-Path $OtherRoot ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)
                $dst = Join-Path $RepoRoot ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)
                $dstDir = Split-Path $dst -Parent
                if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
                Copy-Item -Path $src -Destination $dst -Force
                Write-Host "      -> copied" -ForegroundColor Green
            }
        }
    }

    $different = @()
    foreach ($rel in $inBoth) {
        $hCanon = Get-FileHashSafe -BasePath $RepoRoot -RelativePath $rel
        $hOther = Get-FileHashSafe -BasePath $OtherRoot -RelativePath $rel
        if ($hCanon -and $hOther -and $hCanon -ne $hOther) { $different += $rel }
    }
    if ($different.Count -gt 0) {
        Write-Host "  Different content ($($different.Count)):"
        foreach ($rel in $different) {
            Write-Host "    ~ $rel"
            if (-not $DryRun -and $Copy) {
                $src = Join-Path $OtherRoot ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)
                $dst = Join-Path $RepoRoot ($rel -replace "/", [IO.Path]::DirectorySeparatorChar)
                $backup = "$dst.bak.$((Get-Date).ToString('yyyyMMddHHmmss'))"
                Copy-Item -Path $dst -Destination $backup -Force
                Copy-Item -Path $src -Destination $dst -Force
                Write-Host "      -> backed up and overwritten" -ForegroundColor Green
            }
        }
    }

    if ($onlyInOther.Count -eq 0 -and $different.Count -eq 0 -and $inBoth.Count -gt 0) {
        Write-Host "  No missing or different files."
    }
    Write-Host ""
}

if ($DryRun) {
    Write-Host "Re-run with -Copy to apply changes." -ForegroundColor Gray
}
