#!/bin/bash

# 🚀 BOOTSTRAP CONSOLIDATION - AUTOMATION SCRIPTS
# Execute these commands step-by-step for migration

echo "🎯 BOOTSTRAP CONSOLIDATION MIGRATION - AUTOMATION SCRIPTS"
echo "=========================================================="

# PHASE 1: AUDIT COMMANDS
echo ""
echo "📋 PHASE 1: AUDIT & MAPPING"
echo "----------------------------"

echo "# 1.1 Find all Tailwind-like classes"
echo 'grep -r "class=.*\b(flex|hidden|gap-|bg-.*\/|rounded-[0-9]|backdrop-blur)" templates/ > tailwind_classes_audit.txt'

echo ""
echo "# 1.2 Find all Bootstrap classes"  
echo 'grep -r "class=.*\b(d-flex|container|row|col|btn|list-unstyled)" templates/ > bootstrap_classes_audit.txt'

echo ""
echo "# 1.3 Find conflicting combinations"
echo 'grep -r "class=.*\b(d-flex.*flex|align-items.*items-)" templates/ > conflicts_audit.txt'

echo ""
echo "# 1.4 Count usage statistics"
echo 'echo "=== TAILWIND-LIKE USAGE ===" > usage_stats.txt'
echo 'grep -c "flex\|hidden\|gap-\|bg-.*/" templates/*.html >> usage_stats.txt'
echo 'echo "=== BOOTSTRAP USAGE ===" >> usage_stats.txt' 
echo 'grep -c "d-flex\|container\|btn\|list-unstyled" templates/*.html >> usage_stats.txt'

# PHASE 2: BACKUP COMMANDS
echo ""
echo "📁 PHASE 2: BACKUP CREATION"  
echo "----------------------------"

echo "# 2.1 Create template backups"
echo 'find templates/ -name "*.html" -exec cp {} {}.backup_bootstrap_consolidation \;'

echo ""
echo "# 2.2 Create CSS backups"
echo 'find static/css/ -name "*.css" -exec cp {} {}.backup_bootstrap_consolidation \;'

# PHASE 3: TEMPLATE MIGRATION COMMANDS
echo ""
echo "🔄 PHASE 3: TEMPLATE MIGRATION HELPERS"
echo "--------------------------------------"

echo "# 3.1 Replace common Tailwind-like classes"
echo "# Manual replacement needed - use these patterns:"

echo ""
echo "# Flexbox replacements:"
echo 'sed -i.bak "s/flex items-center/d-flex align-items-center/g" templates/*.html'
echo 'sed -i.bak "s/flex justify-between/d-flex justify-content-between/g" templates/*.html'  
echo 'sed -i.bak "s/flex justify-center/d-flex justify-content-center/g" templates/*.html'

echo ""
echo "# Visibility replacements:"
echo 'sed -i.bak "s/hidden md:flex/d-none d-md-flex/g" templates/*.html'
echo 'sed -i.bak "s/md:hidden/d-md-none/g" templates/*.html'

echo ""
echo "# Spacing replacements:"
echo 'sed -i.bak "s/gap-2/gap-2/g" templates/*.html  # Keep gap-2 - will be custom utility'
echo 'sed -i.bak "s/gap-3/gap-3/g" templates/*.html  # Keep gap-3 - will be custom utility'

# PHASE 4: CSS CLEANUP COMMANDS
echo ""
echo "🧹 PHASE 4: CSS CLEANUP"
echo "------------------------"

echo "# 4.1 Find custom Tailwind-like CSS to remove"
echo 'grep -r "\.flex\s*{" static/css/'
echo 'grep -r "\.hidden\s*{" static/css/'
echo 'grep -r "\.items-center\s*{" static/css/'
echo 'grep -r "\.justify-between\s*{" static/css/'

echo ""
echo "# 4.2 Create bootstrap-extensions.css"
echo "# This will be created manually with custom utilities"

# PHASE 5: VALIDATION COMMANDS  
echo ""
echo "✅ PHASE 5: VALIDATION & TESTING"
echo "---------------------------------"

echo "# 5.1 Check for remaining Tailwind-like classes"
echo 'grep -r "class=.*\b(flex|hidden|items-|justify-)" templates/ | grep -v "d-flex\|d-none"'

echo ""
echo "# 5.2 Validate Bootstrap classes"
echo 'grep -r "class=.*\b(d-flex|align-items|justify-content)" templates/ | wc -l'

echo ""
echo "# 5.3 Check for CSS conflicts"
echo 'grep -r "!important" static/css/ | grep -v "backup\|vendor"'

echo ""
echo "# 5.4 Validate HTML structure"
echo 'find templates/ -name "*.html" -exec htmlhint {} \; 2>/dev/null | grep -i error'

# PHASE 6: CLEANUP COMMANDS
echo ""
echo "🗑️  PHASE 6: CLEANUP"
echo "--------------------"

echo "# 6.1 Remove backup files (after testing)"
echo 'find . -name "*.backup_bootstrap_consolidation" -delete'

echo ""
echo "# 6.2 Remove temporary audit files"
echo 'rm -f tailwind_classes_audit.txt bootstrap_classes_audit.txt conflicts_audit.txt usage_stats.txt'

# UTILITY COMMANDS
echo ""
echo "🔧 UTILITY COMMANDS"
echo "-------------------"

echo "# Check current Bootstrap CDN status"
echo 'curl -s -I https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css | head -5'

echo ""
echo "# Count total classes per template"
echo 'for file in templates/*.html; do echo "=== $file ==="; grep -o "class=\"[^\"]*\"" "$file" | wc -l; done'

echo ""
echo "# Find templates with most Tailwind-like usage"
echo 'grep -c "flex\|gap-\|rounded-" templates/*.html | sort -t: -k2 -nr'

echo ""
echo "# Validate CSS syntax"
echo 'find static/css/ -name "*.css" -exec csslint {} \; 2>/dev/null | grep -i error'

echo ""
echo "🎯 EXECUTION NOTES:"
echo "==================="
echo "1. Run audit commands first to understand current state"
echo "2. Create backups before any modifications"
echo "3. Migrate templates one by one, testing each"
echo "4. Create bootstrap-extensions.css for missing utilities"
echo "5. Test thoroughly before cleanup"
echo "6. Keep backups until migration fully validated"

echo ""
echo "⚠️  IMPORTANT: This is a helper script. Review each command before execution!"
echo "🚀 Ready to start Bootstrap consolidation migration!"
