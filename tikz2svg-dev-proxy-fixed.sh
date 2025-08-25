#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/hieplequoc/web/work/tikz2svg_api"
VPS="h2cloud-hiep1987"

# Cổng DB local để forward (mặc định 3306)
LOCAL_PORT="${LOCAL_PORT:-3306}"
STATIC_DIR="${PROJECT_DIR}/static"

# Development files cần bảo vệ
DEV_FILES=(
    "js/file_card.js"
    "css/file_card.css"
)

cleanup() {
  # Đóng tunnel nếu còn
  if lsof -ti tcp:${LOCAL_PORT} >/dev/null 2>&1; then
    kill -9 $(lsof -ti tcp:${LOCAL_PORT}) || true
  fi
}
trap cleanup EXIT

# 1) đảm bảo không ai chiếm cổng
cleanup

# 2) thử SSH non-interactive trước
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${VPS}" "echo ok" >/dev/null 2>&1; then
  echo "[!] SSH không sẵn sàng (cần host key hoặc passphrase)."
  echo "    Hãy chạy: ssh ${VPS}    rồi thử lại."
  exit 1
fi

# 3) mở tunnel và buộc fail nếu không forward được
ssh \
  -fN \
  -L ${LOCAL_PORT}:127.0.0.1:3306 \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -o StrictHostKeyChecking=accept-new \
  "${VPS}"

# 4) xác nhận đã listen
if ! lsof -iTCP:${LOCAL_PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[!] Không mở được tunnel trên cổng ${LOCAL_PORT}"
  exit 1
fi
echo "[OK] Tunnel đang mở: 127.0.0.1:${LOCAL_PORT} -> ${VPS}:3306"

# 5) Backup development files trước khi sync
echo "[BACKUP] Backup development files..."
mkdir -p "${STATIC_DIR}/js" "${STATIC_DIR}/css"
for file in "${DEV_FILES[@]}"; do
    if [[ -f "${STATIC_DIR}/${file}" ]]; then
        cp "${STATIC_DIR}/${file}" "${STATIC_DIR}/${file}.backup" 2>/dev/null || true
        echo "  ✓ Backup: ${file}"
    fi
done

# 6) Đồng bộ static từ VPS -> Mac (KHÔNG dùng --delete)
mkdir -p "${STATIC_DIR}"
echo "[SYNC] Đồng bộ static từ VPS (không xóa files local)..."
set +e
rsync -avz --ignore-errors \
  "${VPS}:/var/www/tikz2svg_api/shared/static/" \
  "${STATIC_DIR}/"
rc=$?
set -e

# rsync trả 0 (ok), 24 (file vanished), hoặc 23 (partial transfer) vẫn coi là OK
if [[ $rc -eq 0 || $rc -eq 24 || $rc -eq 23 ]]; then
  echo "[SYNC] Hoàn tất (rc=${rc})."
else
  echo "[!] rsync lỗi (rc=${rc}). Tiếp tục chạy DEV không đồng bộ."
fi

# 7) Khôi phục development files nếu bị mất
echo "[RESTORE] Khôi phục development files..."
for file in "${DEV_FILES[@]}"; do
    if [[ ! -f "${STATIC_DIR}/${file}" ]] && [[ -f "${STATIC_DIR}/${file}.backup" ]]; then
        cp "${STATIC_DIR}/${file}.backup" "${STATIC_DIR}/${file}"
        echo "  ✓ Restore: ${file}"
    fi
done

# 8) Xóa backup files
for file in "${DEV_FILES[@]}"; do
    rm -f "${STATIC_DIR}/${file}.backup" 2>/dev/null || true
done

# 9) chạy app DEV
cd "$PROJECT_DIR" || { echo "Not found: $PROJECT_DIR"; exit 1; }
if [[ -f ".venv/bin/activate" ]]; then
  source .venv/bin/activate
  # Cài đặt dependencies nếu thiếu
  echo "[DEPS] Kiểm tra dependencies..."
  pip install -r requirements.txt --quiet
else
  echo "[!] Không thấy .venv, tạo nhanh…"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -U pip wheel
  pip install -r requirements.txt
fi

# Thiết lập biến môi trường cho DEV
export FLASK_ENV=development
export FLASK_DEBUG=1
export DB_HOST="${DB_HOST:-127.0.0.1}"

# QUAN TRỌNG: ép ghi file vào static local, tránh ghi vào /var/www
export TIKZ_SVG_DIR="${STATIC_DIR}"

echo "[DEV] Khởi động Flask ở http://127.0.0.1:5173/"
exec flask --app app:app --debug run --host 127.0.0.1 --port 5173
