#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/hieplequoc/web/work/tikz2svg_api"
cd "$PROJECT_DIR" || { echo "Không tìm thấy: $PROJECT_DIR"; exit 1; }

# Start required services
echo "🚀 Starting local development services..."

# Start MySQL
echo "📊 Starting MySQL..."
if ! brew services list | grep mysql | grep -q started; then
    brew services start mysql
    sleep 2
fi

# Start Apache for phpMyAdmin
echo "🌐 Starting Apache..."
if ! brew services list | grep httpd | grep -q started; then
    brew services start httpd
    sleep 2
fi

echo "✅ Services ready!"

# Load environment variables từ .env nếu có
if [[ -f ".env" ]]; then
	set -a
	source .env
	set +a
	echo "[CONFIG] Using DB: ${DB_HOST}/${DB_NAME}"
else
	echo "[WARNING] No .env found, using defaults"
fi

# Kích hoạt virtual environment
if [[ -f ".venv/bin/activate" ]]; then
	source .venv/bin/activate
else
	echo "[SETUP] Tạo virtual environment..."
	python3 -m venv .venv
	source .venv/bin/activate
	pip install -U pip wheel
	pip install -r requirements.txt
fi

# Test database connection
python3 -c "
import mysql.connector, os
try:
	conn = mysql.connector.connect(
		host=os.environ.get('DB_HOST', 'localhost'),
		user=os.environ.get('DB_USER', 'hiep1987'),
		password=os.environ.get('DB_PASSWORD', ''),
		database=os.environ.get('DB_NAME', 'tikz2svg')
	)
	conn.close()
	print('✅ Database OK')
except Exception as e:
	print(f'❌ DB Error: {e}')
	exit(1)
"

echo ""
echo "🎉 Development environment ready!"
echo "📱 App: http://127.0.0.1:5173/"
echo "🗄️  phpMyAdmin: http://localhost:8080/phpmyadmin/"
echo "📊 Database: ${DB_NAME}"
echo ""
echo "Database login info:"
echo "Username: hiep1987"
echo "Password: (empty or your password)"
echo ""
exec flask --app app:app --debug run --host 127.0.0.1 --port 5173
