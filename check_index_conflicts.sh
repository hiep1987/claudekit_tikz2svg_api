#!/bin/bash

echo "🔍 INDEX PAGE CSS CONFLICTS CHECKER"
echo "=================================="

echo ""
echo "1. 📋 INDEX.CSS vs FOUNDATION CONFLICTS..."
echo "Foundation selectors có thể bị index.css override:"
echo ""
echo "=== FOUNDATION (global-base.css) ==="
grep -n "\.tikz-app h[1-6]\|\.tikz-app input\|\.tikz-app textarea" static/css/foundation/global-base.css | head -10

echo ""
echo "=== INDEX.CSS (components) ==="
grep -n "\.tikz-app.*h[1-6]\|\.tikz-app.*input\|\.tikz-app.*textarea" static/css/index.css

echo ""
echo "2. 🎯 VARIABLES USED IN INDEX.CSS..."
echo "All CSS variables used in index.css:"
grep -o "var(--[^)]*)" static/css/index.css | sort -u | head -20

echo ""
echo "3. ❌ UNDEFINED VARIABLES CHECK..."
echo "Variables used in index.css but not defined in master-variables.css:"
grep -o "var(--[^)]*)" static/css/index.css | sed 's/var(//;s/)//' | sort -u > /tmp/index_vars.txt
grep -o "\-\-[^:;]*" static/css/foundation/master-variables.css | sort -u > /tmp/defined_vars.txt
echo "Missing variables:"
comm -23 /tmp/index_vars.txt /tmp/defined_vars.txt | head -10

echo ""
echo "4. 🔍 SELECTOR SPECIFICITY CHECK..."
echo "Generic selectors in index.css (potential conflicts):"
grep -n "\.tikz-app [a-zA-Z][a-zA-Z]*[^-.].*{" static/css/index.css | head -10

echo ""
echo "5. ✅ CONFLICT RESOLUTION STATUS..."
echo "--- H2 Elements ---"
if grep -q "\.tikz-app h2" static/css/index.css; then
    echo "❌ Generic h2 selector found - CONFLICT!"
    grep -n "\.tikz-app h2" static/css/index.css
else
    echo "✅ No generic h2 conflicts"
fi

if grep -q "\.index-title" static/css/index.css; then
    echo "✅ Using specific .index-title class"
fi

echo ""
echo "--- TEXTAREA Elements ---"
if grep -q "\.tikz-app textarea[^[]" static/css/index.css; then
    echo "❌ Generic textarea selector found - CONFLICT!"
    grep -n "\.tikz-app textarea[^[]" static/css/index.css
else
    echo "✅ No generic textarea conflicts"
fi

if grep -q "\.tikz-code-textarea" static/css/index.css; then
    echo "✅ Using specific .tikz-code-textarea class"
fi

echo ""
echo "--- INPUT Elements ---"
echo "Input-related selectors in index.css:"
grep -n "\.input\|input" static/css/index.css | grep -v "input-preview" | head -5

echo ""
echo "6. 🎨 SEARCH BAR SPECIFIC CHECK..."
echo "Search container styling:"
grep -A5 -B2 "search-container\|\.group\|\.icon" static/css/index.css | head -15

echo ""
echo "🎯 INDEX-SPECIFIC SUMMARY COMPLETE"

# Cleanup
rm -f /tmp/index_vars.txt /tmp/defined_vars.txt
