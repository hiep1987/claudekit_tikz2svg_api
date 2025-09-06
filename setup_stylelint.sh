#!/bin/bash

# Setup Stylelint for TikZ2SVG project
echo "🎨 Setting up Stylelint for CSS linting..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Install Stylelint and config
echo "📦 Installing Stylelint..."
npm install --save-dev stylelint@^16.0.0 stylelint-config-standard@^36.0.0

if [ $? -eq 0 ]; then
    echo "✅ Stylelint installed successfully!"
else
    echo "❌ Failed to install Stylelint"
    exit 1
fi

# Create .stylelintignore if not exists
if [ ! -f .stylelintignore ]; then
    echo "📝 Creating .stylelintignore file..."
    cat > .stylelintignore << EOF
# Dependencies
node_modules/
venv/

# Minified files
**/*.min.css

# Vendor files
**/vendor/**/*.css

# Backup files
**/*.backup*
older/**/*.css

# Build output
dist/
build/
EOF
    echo "✅ .stylelintignore created"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Available commands:"
echo "  npm run lint:css          - Lint all CSS files"
echo "  npm run lint:css:fix      - Lint and auto-fix CSS files"
echo "  npm run lint:css:report   - Generate JSON report"
echo ""
echo "🔧 Manual commands:"
echo "  npx stylelint static/css/**/*.css"
echo "  npx stylelint static/css/**/*.css --fix"
echo ""
echo "🎯 Key rules enabled:"
echo "  ✅ No duplicate selectors"
echo "  ✅ No duplicate properties"
echo "  ⚠️  !important usage warnings"
echo "  ⚠️  High specificity warnings"
echo "  ⚠️  Deep nesting warnings"
echo ""
echo "Ready to lint! 🚀"
