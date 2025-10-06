#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/hieplequoc/web/work/tikz2svg_api"
cd "$PROJECT_DIR" || { echo "Không tìm thấy: $PROJECT_DIR"; exit 1; }

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

echo "[LOCAL DEV] http://127.0.0.1:5173/ | DB: ${DB_NAME}"
exec flask --app app:app --debug run --host 127.0.0.1 --port 5173
