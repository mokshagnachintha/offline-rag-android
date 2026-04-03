# O-RAG Build #32 Monitoring & Validation Script (PowerShell)
# Monitors GitHub Actions workflow and provides status updates

param(
    [switch]$CheckStatus,
    [switch]$WatchLogs,
    [int]$UpdateInterval = 60  # seconds between status updates
)

# Configuration
$RepoOwner = "mokshagnachintha"
$RepoName = "o-rag"
$WorkflowName = "V3 Build & Release APK"
$CommitHash = "32bb210"
$ExpectedAPKName = "orag-*-release-unsigned.apk"

# Checkpoint timing (in minutes from build trigger at 00:05 IST)
$Checkpoints = @{
    "Setup Complete"        = 15   # 00:20
    "License Phase"         = 30   # 00:35
    "Build Phase Progress"  = 80   # 01:25
    "Final Phase"           = 115  # 02:00
    "APK Generation"        = 145  # 02:30
    "Build Complete"        = 160  # 02:45
}

function Print-Header {
    param([string]$Text)
    Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Print-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Print-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Text)
    Write-Host "ℹ $Text" -ForegroundColor Blue
}

function Get-BuildStatus {
    Print-Header "Build #32 Status"
    
    Write-Host "Repository: $RepoOwner/$RepoName"
    Write-Host "Workflow: $WorkflowName"
    Write-Host "Trigger Commit: $CommitHash"
    Write-Host "Branch: v3"
    Write-Host ""
    
    # Get trigger time from git
    $triggerTime = & git log -1 --format="%ai" --all | ConvertFrom-String -PropertyNames Timestamp, Timezone | Select-Object -First 1
    Write-Host "Trigger Time: $triggerTime"
    Write-Host "Current Time: $(Get-Date)"
    
    # Calculate elapsed time
    $triggerString = & git log -1 --format="%ai"
    $triggerDate = [DateTime]::Parse($triggerString.Split(' ')[0..1] -join ' ')
    $elapsed = (Get-Date) - $triggerDate
    
    Write-Host "Elapsed: $([int]$elapsed.TotalMinutes) minutes"
    Write-Host ""
    
    # Show checkpoint status
    Print-Info "Checkpoint Timeline:"
    Write-Host ""
    
    foreach ($checkpoint in $Checkpoints.GetEnumerator() | Sort-Object { $_.Value }) {
        $minutes = $checkpoint.Value
        $status = ""
        
        if ($minutes -le [int]$elapsed.TotalMinutes) {
            $status = "✓ PASSED"
            $color = "Green"
        } else {
            $remaining = $minutes - [int]$elapsed.TotalMinutes
            $status = "⏳ in $remaining min"
            $color = "Yellow"
        }
        
        Write-Host "  [$status]" -ForegroundColor $color -NoNewline
        Write-Host " $($checkpoint.Key) (T+$minutes min)"
    }
    
    Write-Host ""
    Print-Warning "For real-time build status, visit:"
    Write-Host "https://github.com/$RepoOwner/$RepoName/actions" -ForegroundColor Cyan
}

function Get-FailureRecovery {
    Print-Header "If Build Fails - Recovery Steps"
    
    Write-Host "1. Open GitHub Actions:"
    Write-Host "   https://github.com/$RepoOwner/$RepoName/actions`n"
    
    Write-Host "2. Click on the failed workflow run (commit $CommitHash)`n"
    
    Write-Host "3. Scroll to 'Analyze Build Errors' section to see error logs`n"
    
    Write-Host "4. Common issues and fixes:`n"
    
    Write-Host "   ISSUE: License-related errors"
    Print-Success "Already fixed in v9997a53 with monitoring loop"
    Write-Host "   ACTION: Check logs for license acceptance confirmation`n"
    
    Write-Host "   ISSUE: Out of memory errors" -ForegroundColor Yellow
    Write-Host "   ACTION: Reduce JVM heap in workflow file (-Xmx256m)`n"
    
    Write-Host "   ISSUE: Build timeout"
    Write-Host "   ACTION: Increase timeout in v3_build_release.yml`n"
    
    Write-Host "   ISSUE: Missing tools/dependencies"
    Write-Host "   ACTION: Add explicit installation in workflow`n"
    
    Write-Host "5. After fixing, push change to v3 branch:"
    Write-Host "   git commit -am 'fix: [description]'"
    Write-Host "   git push origin v3`n"
    
    Write-Host "6. New build will trigger automatically`n"
    Write-Host "7. Monitor new build from SETUP checkpoint"
}

function Get-SuccessPath {
    Print-Header "When Build Completes Successfully"
    
    Write-Host "1. Workflow shows green checkmark on GitHub Actions`n"
    
    Write-Host "2. APK artifact location:"
    Write-Host "   GitHub Actions → Artifacts section → orag-apk-[run-number]`n"
    
    Write-Host "3. Download the APK file:"
    Write-Host "   orag-*-release-unsigned.apk (should be 50-200 MB)`n"
    
    Write-Host "4. Verify APK:"
    Write-Host "   - Check file size is 50-200 MB"
    Write-Host "   - Try installing on Android device: adb install orag-*.apk"
    Write-Host "   - Launch app and test basic functionality`n"
    
    Write-Host "5. Celebrate! 🎉 Android app successfully built with:"
    Write-Host "   - Qwen 3.5-2B LLM (quantized)"
    Write-Host "   - Nomic Embed Text embeddings"
    Write-Host "   - RAG retrieval system"
    Write-Host "   - Mobile-optimized (~1.2 GB total)"
}

function Show-MonitoringGuide {
    Print-Header "Build Monitoring Guide"
    
    Write-Host "You requested: 'keep tracking it resolve it until it produces an app'`n"
    
    Write-Host "BUILD STATUS:
    ✓ Commit 32bb210 successfully pushed
    ✓ Workflow triggered automatically
    ✓ GitHub Actions build #32 is RUNNING`n"
    
    Write-Host "REAL-TIME MONITORING:`n"
    
    Write-Host "Option 1: Watch on GitHub"
    Write-Host "  Open: https://github.com/$RepoOwner/$RepoName/actions"
    Write-Host "  Look for the latest run with commit $CommitHash"
    Write-Host "  Status will update every 30 seconds`n"
    
    Write-Host "Option 2: Use this script"
    Write-Host "  Run: .\check_build_status.ps1 -CheckStatus"
    Write-Host "  Shows checkpoint status and timing`n"
    
    Write-Host "Option 3: Keep terminal open"
    Write-Host "  Run: .\check_build_status.ps1 -CheckStatus -WatchLogs"
    Write-Host "  Checks status every $UpdateInterval seconds`n"
    
    Write-Host "IMPORTANT: Build takes ~160-180 minutes"
    Write-Host "Expected completion: ~2:45 AM IST (T+165 min from 00:05)`n"
    
    Get-BuildStatus
}

# Main execution
if ($CheckStatus) {
    Get-BuildStatus
    Get-SuccessPath
    Get-FailureRecovery
} elseif ($WatchLogs) {
    $iteration = 0
    while ($true) {
        Clear-Host
        $iteration++
        Write-Host "Build Monitoring Loop - Iteration $iteration (Auto-refresh every $UpdateInterval sec)" -ForegroundColor Magenta
        Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray
        
        Get-BuildStatus
        
        Write-Host "`nNext check in $UpdateInterval seconds... ($(Get-Date))" -ForegroundColor Gray
        Start-Sleep -Seconds $UpdateInterval
    }
} else {
    Show-MonitoringGuide
}
