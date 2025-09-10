#!/bin/bash

echo "🔍 CSS CONFLICTS CHECKER - TIKZ2SVG_API"
echo "========================================"

echo ""
echo "1. 📋 CHECKING FOUNDATION vs COMPONENT CONFLICTS..."
echo "Foundation selectors that might be overridden:"
grep -n "\.tikz-app [a-zA-Z][^.]*{" static/css/foundation/global-base.css | head -20

echo ""
echo "2. 🚨 DUPLICATE SELECTORS ACROSS FILES..."
echo "Same selectors in multiple files (excluding backups):"
grep -rn "\.tikz-app h[1-6]\|\.tikz-app input[^-]\|\.tikz-app textarea[^[]" static/css/ | grep -v backup | grep -v foundation | cut -d: -f1-2 | sort

echo ""
echo "3. 🔍 SPECIFICITY CONFLICTS..."
echo "Generic vs Specific selectors:"
echo "=== GENERIC (Foundation) ==="
grep -n "\.tikz-app h[1-6][^.]" static/css/foundation/global-base.css || echo "No generic selectors found"
echo "=== SPECIFIC (Components) ==="
grep -rn "\.tikz-app.*h[1-6]" static/css/ | grep -v backup | grep -v foundation | head -10

echo ""
echo "4. 📊 VARIABLE USAGE CHECK..."
echo "Undefined CSS variables:"
grep -ro "var(--[^)]*)" static/css/index.css | sort -u > /tmp/used_vars.txt
grep -o "--[^:]*:" static/css/foundation/master-variables.css | sed 's/:$//' | sort -u > /tmp/defined_vars.txt
echo "Variables used but not defined:"
comm -23 /tmp/used_vars.txt /tmp/defined_vars.txt | head -10

echo ""
echo "5. 🎯 INDEX.CSS SPECIFIC ANALYSIS..."
echo "Potential conflicts in index.css:"
echo "--- h2 selectors ---"
grep -n "h2" static/css/index.css || echo "No h2 conflicts"
echo "--- textarea selectors ---"
grep -n "textarea" static/css/index.css || echo "No textarea conflicts"
echo "--- input selectors ---"
grep -n "\.input" static/css/index.css | head -5

echo ""
echo "6. ✅ RESOLUTION STATUS..."
if grep -q "\.index-title" static/css/index.css; then
    echo "✅ h2 conflict resolved (using .index-title)"
else
    echo "❌ h2 conflict still exists"
fi

if grep -q "\.tikz-code-textarea" static/css/index.css; then
    echo "✅ textarea conflict resolved (using .tikz-code-textarea)"
else
    echo "❌ textarea conflict still exists"
fi

echo ""
echo "🎯 SUMMARY COMPLETE - Review conflicts above"

# Cleanup
rm -f /tmp/used_vars.txt /tmp/defined_vars.txt
