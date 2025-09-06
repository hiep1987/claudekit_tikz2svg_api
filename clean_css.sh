#!/bin/bash

# CSS Cleanup Helper Script
echo "🧹 CSS CLEANUP HELPER"
echo "====================="

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  redundant-box     Remove redundant box-sizing: border-box"
    echo "  stylelint         Run Stylelint checks"
    echo "  stylelint-fix     Run Stylelint with auto-fix"
    echo "  backup            Create backup of all CSS files"
    echo "  restore           Restore from latest backup"
    echo ""
    echo "Options:"
    echo "  --dry-run         Preview changes without modifying files"
    echo "  --files FILE...   Process specific files only"
    echo ""
    echo "Examples:"
    echo "  $0 redundant-box --dry-run"
    echo "  $0 redundant-box --files index.css navigation.css"
    echo "  $0 stylelint"
    echo "  $0 stylelint-fix"
}

# Function to remove redundant box-sizing
remove_redundant_box_sizing() {
    local dry_run=""
    local files=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="--dry-run"
                shift
                ;;
            --files)
                shift
                files="--files $*"
                break
                ;;
            *)
                echo "Unknown option: $1"
                return 1
                ;;
        esac
    done
    
    # Build command
    local cmd="python3 remove_redundant_box_sizing.py"
    if [[ -z "$dry_run" ]]; then
        cmd="$cmd --live"
    fi
    if [[ -n "$files" ]]; then
        cmd="$cmd $files"
    fi
    
    echo "🔧 Running: $cmd"
    eval $cmd
}

# Function to run Stylelint
run_stylelint() {
    echo "🔍 Running Stylelint checks..."
    npx stylelint "static/css/**/*.css"
}

# Function to run Stylelint with auto-fix
run_stylelint_fix() {
    echo "🔧 Running Stylelint with auto-fix..."
    npx stylelint "static/css/**/*.css" --fix
}

# Function to create backup
create_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="static/css/backup_$timestamp"
    
    echo "💾 Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"
    cp static/css/*.css "$backup_dir/" 2>/dev/null || true
    echo "✅ Backup created: $backup_dir"
}

# Function to restore from backup
restore_backup() {
    local latest_backup=$(ls -td static/css/backup_* 2>/dev/null | head -1)
    
    if [[ -z "$latest_backup" ]]; then
        echo "❌ No backup found"
        return 1
    fi
    
    echo "🔄 Restoring from $latest_backup..."
    cp "$latest_backup"/*.css static/css/ 2>/dev/null || true
    echo "✅ Restored from backup"
}

# Main script logic
case "${1:-help}" in
    redundant-box)
        shift
        remove_redundant_box_sizing "$@"
        ;;
    stylelint)
        run_stylelint
        ;;
    stylelint-fix)
        run_stylelint_fix
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
