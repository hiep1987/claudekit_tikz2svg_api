#!/bin/bash

# Script setup Identity Verification System
# Chạy script này để setup database cho hệ thống xác thực danh tính

echo "🔐 Setting up Identity Verification System..."
echo "=============================================="

# Kiểm tra file SQL
if [ ! -f "identity_verification_setup.sql" ]; then
    echo "❌ Error: File identity_verification_setup.sql không tồn tại!"
    exit 1
fi

# Lấy thông tin database từ environment
DB_HOST=${DB_HOST:-"localhost"}
DB_USER=${DB_USER:-"hiep1987"}
DB_NAME=${DB_NAME:-"tikz2svg"}

echo "📊 Database Info:"
echo "   Host: $DB_HOST"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo ""

# Backup database trước khi thay đổi
echo "💾 Creating backup..."
BACKUP_FILE="backup_before_identity_verification_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -h "$DB_HOST" -u "$DB_USER" -p "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup created: $BACKUP_FILE"
else
    echo "⚠️  Warning: Could not create backup (this is okay for development)"
fi

echo ""

# Chạy SQL setup
echo "🚀 Running SQL setup..."
mysql -h "$DB_HOST" -u "$DB_USER" -p "$DB_NAME" < identity_verification_setup.sql

if [ $? -eq 0 ]; then
    echo "✅ SQL setup completed successfully!"
else
    echo "❌ Error: SQL setup failed!"
    exit 1
fi

echo ""

# Kiểm tra cấu trúc database
echo "🔍 Verifying database structure..."
mysql -h "$DB_HOST" -u "$DB_USER" -p "$DB_NAME" -e "DESCRIBE user;" | grep -E "(identity_verified|identity_verification)"

if [ $? -eq 0 ]; then
    echo "✅ Database structure verified!"
else
    echo "⚠️  Warning: Could not verify database structure"
fi

echo ""

# Kiểm tra các file cần thiết
echo "📁 Checking required files..."

FILES_TO_CHECK=(
    "templates/profile_verification.html"
    "templates/emails/identity_verification.html"
    "static/identity-verification-icon.svg"
    "app.py"
    "email_service.py"
    "email_config.py"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

echo ""

echo "🎉 Setup completed!"
echo "=============================================="
echo "📋 Next steps:"
echo "1. Restart your Flask application"
echo "2. Test the verification system:"
echo "   - Go to /profile/{user_id}/settings"
echo "   - Click 'Xác thực tài khoản'"
echo "   - Follow the verification process"
echo "3. Check email functionality"
echo ""
echo "📚 For more details, see: IDENTITY_VERIFICATION_SETUP.md"
