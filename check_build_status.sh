#!/bin/bash
# O-RAG Build #32 Monitoring & Validation Script
# Monitors GitHub Actions workflow and validates APK when complete

# Configuration
REPO_OWNER="mokshagnachintha"
REPO_NAME="o-rag"
WORKFLOW_NAME="V3 Build & Release APK"
EXPECTED_APK_NAME="orag-*-release-unsigned.apk"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Checkpoint timing (in seconds from build trigger)
CHECKPOINT_1_SETUP=900           # 15 min - Setup complete
CHECKPOINT_2_LICENSE=1800        # 30 min - License phase
CHECKPOINT_3_BUILD=4800          # 80 min - Build phase
CHECKPOINT_4_FINAL=6900          # 115 min - Final phase
CHECKPOINT_5_COMPLETE=8700       # 145 min - Completion
CHECKPOINT_6_VERIFY=9600         # 160 min - Verification

BUILD_TRIGGER_TIME=$(date +%s)  # Capture current time

function print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

function seconds_to_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    printf "%02d:%02d" $hours $minutes
}

function get_time_until_checkpoint() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - BUILD_TRIGGER_TIME))
    local remaining=$1
    
    if [ $elapsed -ge $remaining ]; then
        echo "NOW OVERDUE"
    else
        local secs_remaining=$((remaining - elapsed))
        echo "in $(seconds_to_time $secs_remaining)"
    fi
}

function check_workflow_status() {
    print_header "Workflow Status Check"
    
    echo "Repository: $REPO_OWNER/$REPO_NAME"
    echo "Workflow: $WORKFLOW_NAME"
    echo "Trigger commit: 32bb210"
    echo "Branch: v3"
    echo ""
    
    # This would require GitHub CLI or API auth in real implementation
    echo "Current time: $(date)"
    echo "Build elapsed: $(seconds_to_time $(($(date +%s) - BUILD_TRIGGER_TIME)))"
    echo ""
    
    print_warning "To get real-time status, visit:"
    echo "https://github.com/$REPO_OWNER/$REPO_NAME/actions"
    echo ""
    
    # Expected checkpoints
    echo "Expected Checkpoints:"
    echo "  Checkpoint 1 (Setup)    : $CHECKPOINT_1_SETUP sec - $(seconds_to_time $CHECKPOINT_1_SETUP) - $(get_time_until_checkpoint $CHECKPOINT_1_SETUP)"
    echo "  Checkpoint 2 (License)  : $CHECKPOINT_2_LICENSE sec - $(seconds_to_time $CHECKPOINT_2_LICENSE) - $(get_time_until_checkpoint $CHECKPOINT_2_LICENSE)"
    echo "  Checkpoint 3 (Build)    : $CHECKPOINT_3_BUILD sec - $(seconds_to_time $CHECKPOINT_3_BUILD) - $(get_time_until_checkpoint $CHECKPOINT_3_BUILD)"
    echo "  Checkpoint 4 (Final)    : $CHECKPOINT_4_FINAL sec - $(seconds_to_time $CHECKPOINT_4_FINAL) - $(get_time_until_checkpoint $CHECKPOINT_4_FINAL)"
    echo "  Checkpoint 5 (Complete) : $CHECKPOINT_5_COMPLETE sec - $(seconds_to_time $CHECKPOINT_5_COMPLETE) - $(get_time_until_checkpoint $CHECKPOINT_5_COMPLETE)"
    echo "  Checkpoint 6 (Verify)   : $CHECKPOINT_6_VERIFY sec - $(seconds_to_time $CHECKPOINT_6_VERIFY) - $(get_time_until_checkpoint $CHECKPOINT_6_VERIFY)"
}

function validate_apk() {
    print_header "APK Validation"
    
    if [ -f "$1" ]; then
        local size=$(stat -f%z "$1" 2>/dev/null || stat -c%s "$1" 2>/dev/null)
        local size_mb=$((size / 1024 / 1024))
        
        print_success "APK found: $(basename $1)"
        print_success "Size: $size_mb MB"
        
        if [ $size_mb -ge 50 ] && [ $size_mb -le 500 ]; then
            print_success "Size is reasonable (50-500 MB range)"
            return 0
        else
            print_error "Size is suspicious: $size_mb MB"
            return 1
        fi
    else
        print_error "APK not found: $1"
        return 1
    fi
}

function main() {
    echo ""
    print_header "O-RAG Build #32 Monitor"
    echo ""
    
    check_workflow_status
    
    echo ""
    print_header "Monitoring Instructions"
    echo ""
    echo "1. Visit: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
    echo "2. Click on the latest run (should be labeled with commit 32bb210)"
    echo "3. Watch for status: "
    echo "   - Yellow spinner = In Progress"
    echo "   - Green checkmark = Success"
    echo "   - Red X = Failed"
    echo ""
    echo "4. When complete, APK will be in Artifacts section"
    echo "5. Download: orag-*-release-unsigned.apk"
    echo ""
    
    print_header "What to do if build fails"
    echo ""
    echo "1. Click workflow run"
    echo "2. Scroll to 'Analyze Build Errors' section"
    echo "3. Check for license, memory, or timeout errors"
    echo "4. If license issue:"
    echo "   - Workflow already has monitoring loop (every 2 sec)"
    echo "   - Licenses created in both locations"
    echo "5. If memory issue:"
    echo "   - Reduce JVM heap in v3_build_release.yml"
    echo "6. Commit fix to v3 branch and push (retriggers build)"
    echo ""
}

main
