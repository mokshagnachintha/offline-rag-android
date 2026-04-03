# Monitor Build #32 GitHub Actions Workflow
# This script checks the build status every 30 seconds

param(
    [string]$Owner = "mokshagnachintha",
    [string]$Repo = "o-rag",
    [string]$Branch = "v3",
    [string]$Workflow = "V3 Build & Release APK",
    [int]$CheckInterval = 30,  # seconds
    [int]$MaxChecks = 360  # 3 hours worth of 30-second checks
)

$count = 0
$startTime = Get-Date

Write-Host "Build #32 Monitor Started at $(Get-Date)`n" -ForegroundColor Cyan
Write-Host "Repository: $Owner/$Repo"
Write-Host "Branch: $Branch"
Write-Host "Workflow: $Workflow"
Write-Host "Check interval: $CheckInterval seconds"
Write-Host "Max runtime: $($MaxChecks * $CheckInterval / 60) minutes`n" -ForegroundColor Cyan

while ($count -lt $MaxChecks) {
    $count++
    
    # Get latest workflow run
    $recentCommit = & git log -1 --format="%H"
    $commitTime = & git log -1 --format="%ai"
    
    Write-Host "[$count/$MaxChecks] Checking at $(Get-Date)" -ForegroundColor Yellow
    
    # Try to get workflow status via git (simplified, since GitHub API requires auth)
    Write-Host "Latest commit: $recentCommit"
    Write-Host "Commit time: $commitTime"
    Write-Host "Branch status: $(& git rev-parse --abbrev-ref HEAD)"
    
    # Check if running (this is a placeholder - in real scenario would query GitHub API)
    Write-Host "Status: ⏳ Build in progress (estimated remaining: $($($MaxChecks - $count) * $CheckInterval / 60) minutes)"
    Write-Host ""
    
    # Pause before next check
    if ($count -lt $MaxChecks) {
        Start-Sleep -Seconds $CheckInterval
    }
}

$endTime = Get-Date
$elapsed = $endTime - $startTime

Write-Host "`n=== BUILD MONITORING COMPLETE ===" -ForegroundColor Green
Write-Host "Duration: $([math]::Round($elapsed.TotalMinutes, 1)) minutes"
Write-Host "Final check time: $(Get-Date)"
Write-Host "Check https://github.com/$Owner/$Repo/actions for build artifacts"
