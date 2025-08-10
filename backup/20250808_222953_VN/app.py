from flask import Flask, request, render_template, url_for, send_file, jsonify, session, redirect, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import subprocess
import uuid
from datetime import datetime, timezone
import time
import glob
import cairosvg
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Tắt giới hạn decompression bomb
import re
import traceback
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import mysql.connector

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['DEBUG'] = False # Tắt debug mode cho production

# ✅ FLASK-LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'google.login'
login_manager.login_message = "Bạn cần đăng nhập để truy cập trang này."

# ✅ USER CLASS
class User(UserMixin):
    def __init__(self, id, email, username=None, avatar=None, bio=None):
        self.id = id
        self.email = email
        self.username = username
        self.avatar = avatar
        self.bio = bio
    
    def get_id(self):
        return str(self.id)

# ✅ USER LOADER
@login_manager.user_loader
def load_user(user_id):
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, username, avatar, bio FROM user WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                avatar=user_data['avatar'],
                bio=user_data['bio']
            )
        return None
    except Exception as e:
        print(f"Error loading user: {e}", flush=True)
        return None

# Cleanup thread
import threading
import time

def cleanup_tmp_folder():
    while True:
        try:
            now = time.time()
            tmp_root = '/tmp'
            for folder in os.listdir(tmp_root):
                folder_path = os.path.join(tmp_root, folder)
                if os.path.isdir(folder_path):
                    if len(folder) >= 30 and '-' in folder:
                        mtime = os.path.getmtime(folder_path)
                        if now - mtime > 600:  # hơn 10 phút
                            print(f"[CLEANUP] Removing old tmp folder: {folder_path}", flush=True)
                            import shutil
                            shutil.rmtree(folder_path, ignore_errors=True)
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}", flush=True)
        time.sleep(300)  # chạy lại mỗi 5 phút

threading.Thread(target=cleanup_tmp_folder, daemon=True).start()

# Session config
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

print("DEBUG: Google OAuth blueprint being created...")

TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{{standalone}}
\usepackage{{fontspec}}
\usepackage{{polyglossia}}
\setdefaultlanguage{{vietnamese}}
\usepackage{{amsmath,amssymb}}
\usepackage{{tikz,tikz-3dplot,pgfplots,tkz-tab,tkz-euclide}}
\usepackage{{xcolor}}
\usetikzlibrary{{math}}
\usetikzlibrary{{calc,angles,intersections,shapes.geometric,arrows,decorations.markings,arrows.meta,patterns.meta,patterns,quotes}}
\usetikzlibrary{{hobby,shadings,positioning}}
\usepgfplotslibrary{{polar}}
\begin{{document}}
{tikz_code}
\end{{document}}
"""

try:
    from zoneinfo import ZoneInfo
    tz_vn = ZoneInfo("Asia/Ho_Chi_Minh")
except ImportError:
    from pytz import timezone
    tz_vn = timezone('Asia/Ho_Chi_Minh')

ERROR_TIKZ_DIR = 'error_tikz'
if not os.path.exists(ERROR_TIKZ_DIR):
    os.makedirs(ERROR_TIKZ_DIR)

def get_svg_files():
    """Lấy danh sách các SVG đã lưu trong MySQL"""
    svg_files = []
    current_user_id = current_user.id if current_user.is_authenticated else None
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # ✅ Query đúng với cấu trúc database
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.keywords, 
                s.created_at, 
                u.id as owner_id, 
                u.username, 
                u.email as owner_email,
                COUNT(sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            LEFT JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, u.id, u.username, u.email, user_like.id
            ORDER BY s.created_at DESC
            LIMIT 100
        """, (current_user_id,))
        
        rows = cursor.fetchall()
        for row in rows:
            try:
                static_dir = app.config['UPLOAD_FOLDER']
                filepath = os.path.join(static_dir, row['filename'])
                if os.path.exists(filepath):
                    file_size_kb = round(os.path.getsize(filepath) / 1024, 2)
                else:
                    file_size_kb = None
            except Exception:
                file_size_kb = None
                
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'display_name': f"Người tạo: {row['username']}" if row.get('username') else row['filename'],
                'url': url_for('static', filename=row['filename']),
                'size': file_size_kb,
                'created_time': format_time_vn(row['created_at']),
                'file_time': row['created_at'] if row['created_at'] else datetime.now(),
                'tikz_code': row['tikz_code'] or "",
                'owner_id': row.get('owner_id'),
                'owner_email': row.get('owner_email'),
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
            })
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] get_svg_files(): {e}", flush=True)
    return svg_files

def clean_control_chars(text):
    return re.sub(r'[\x00-\x08\x0B-\x1F\x7F]', '', text)

def format_time_vn(dt):
    """Format thời gian theo múi giờ Việt Nam"""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    vn_time = dt.astimezone(tz_vn)
    return vn_time.strftime("%H:%M:%S - %d/%m/%Y")

# Secret key và Google OAuth blueprint
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secret-key')

google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'GOOGLE_CLIENT_SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ],
    reprompt_select_account=True,
    redirect_to="login_success"
)

app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/login_success")
def login_success():
    """Xử lý sau khi đăng nhập thành công"""
    # Redirect về trang được lưu trong session hoặc trang chủ
    next_url = session.get('next_url')
    if next_url:
        session.pop('next_url', None)  # Xóa sau khi sử dụng
        return redirect(next_url)
    else:
        return redirect(url_for("index"))

@app.route("/set_next_url")
def set_next_url():
    """Lưu URL hiện tại để redirect sau khi đăng nhập"""
    next_url = request.args.get('url')
    if next_url and next_url.startswith('/'):
        session['next_url'] = next_url
    return redirect(url_for("google.login"))


@app.route("/force_logout_dance")
def force_logout_dance():
    print("DEBUG: Force logout Dance endpoint accessed.", flush=True)
    if hasattr(google, 'token'):
        del google.token

    logout_user()  # ✅ Flask-Login logout
    session.clear()
    session.modified = True
    flash("Tất cả session và token Flask-Dance đã được xóa. Vui lòng đăng nhập lại.", "info")
    return redirect(url_for("index"))

def clear_oauth_session():
    session.clear()
    session.modified = True
    logout_user()  # ✅ Flask-Login logout
    
    try:
        del google.token
    except:
        pass

def is_logged_in():
    return google.authorized

@app.before_request
def load_user_info_if_missing():
    # Bỏ qua kiểm tra cho một số route
    if request.path.startswith('/login/google/authorized') or \
       request.path.startswith('/login/google/login') or \
       request.path.startswith('/static/') or \
       request.path.startswith('/temp_svg/') or \
       request.path.startswith('/temp_img/') or \
       request.path.startswith('/logout'): 
        return

    if google.authorized:
        # Nếu session chưa có thông tin user
        if "user_email" not in session:
            print("DEBUG: User authorized but user_email missing from session. Attempting to re-fetch userinfo.", flush=True)
            try:
                resp = google.get("/oauth2/v2/userinfo")
                if resp.ok:
                    info = resp.json()
                    session["user_email"] = info.get("email")
                    session["google_id"] = info.get("id")
                    session.modified = True
                    print(f"DEBUG: Userinfo re-fetched successfully: {session['user_email']}", flush=True)
                else:
                    del google.token
                    print("DEBUG: Failed to re-fetch userinfo. Clearing google.token.", flush=True)
            except Exception as e:
                del google.token
                print(f"DEBUG: Exception during userinfo re-fetch: {e}. Clearing google.token.", flush=True)

        # Nếu session đã có user_email thì đảm bảo có trong DB
        if "user_email" in session:
            if not get_user_by_email(session["user_email"]):
                print(f"DEBUG: User {session['user_email']} not found in DB. Inserting...", flush=True)
                try:
                    conn = mysql.connector.connect(
                        host=os.environ.get('DB_HOST', 'localhost'),
                        user=os.environ.get('DB_USER', 'hiep1987'),
                        password=os.environ.get('DB_PASSWORD', ''),
                        database=os.environ.get('DB_NAME', 'tikz2svg')
                    )
                    cursor = conn.cursor()
                    default_username = re.sub(r'[^a-zA-Z0-9_-]', '_', session['user_email'].split('@')[0])
                    cursor.execute(
                        "INSERT INTO user (email, google_id, username) VALUES (%s, %s, %s)",
                        (session["user_email"], session["google_id"], default_username)
                    )
                    conn.commit()
                    print(f"DEBUG: User {session['user_email']} INSERTED successfully in DB.", flush=True)
                    cursor.close()
                    conn.close()
                except Exception as e:
                    print(f"ERROR inserting user into DB: {e}", flush=True)
                    try:
                        cursor.close()
                        conn.close()
                    except:
                        pass
            
            # ✅ Login user vào Flask-Login nếu chưa login
            if not current_user.is_authenticated:
                user_id = get_user_id_from_session()
                if user_id:
                    user = load_user(user_id)
                    if user:
                        login_user(user, remember=True)
                        print(f"DEBUG: User {user.email} logged into Flask-Login", flush=True)

@app.route("/", methods=["GET", "POST"])
def index():
    print(f"DEBUG: Index route accessed - method: {request.method}")
    logged_in = current_user.is_authenticated
    user_email = current_user.email if logged_in else None
    username = current_user.username if logged_in else None  # ✅ THÊM
    avatar = current_user.avatar if logged_in else None      # ✅ THÊM
    svg_url = None
    svg_full_url = None
    svg_content = None
    file_info = None
    error = None
    svg_temp_url = None
    svg_temp_id = None
    tikz_code = ""
    error_log_full = None
    
    # Chặn biên dịch nếu chưa đăng nhập
    if request.method == "POST" and not logged_in:
        return redirect(url_for("google.login"))
        
    if request.method == "POST":
        tikz_code = request.form.get("code", "")
        tikz_code = clean_control_chars(tikz_code)
        if not tikz_code.strip():
            error = "Vui lòng nhập code TikZ!"
        else:
            now = datetime.now(tz_vn)
            file_id = str(uuid.uuid4())
            work_dir = f"/tmp/{file_id}"
            os.makedirs(work_dir, exist_ok=True)
            tex_path = os.path.join(work_dir, "tikz.tex")
            pdf_path = os.path.join(work_dir, "tikz.pdf")
            svg_path_tmp = os.path.join(work_dir, "tikz.svg")
            
            # Ghi file TeX
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(TEX_TEMPLATE.format(tikz_code=tikz_code))
            try:
                lualatex_process = subprocess.run([
                    "lualatex", "-interaction=nonstopmode", "--output-directory=.", "tikz.tex"
                ],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True
                )
                subprocess.run(["pdf2svg", pdf_path, svg_path_tmp],
                               cwd=work_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                svg_temp_url = f"/temp_svg/{file_id}"
                svg_temp_id = file_id
                try:
                    with open(svg_path_tmp, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                except Exception as e:
                    svg_content = f"Không thể đọc nội dung SVG: {str(e)}"
            except subprocess.CalledProcessError as ex:
                # Lưu code TikZ lỗi và log lỗi
                timestamp = now.strftime('%Y%m%d_%H%M%S')
                error_tex = os.path.join(ERROR_TIKZ_DIR, f'{timestamp}_{file_id}.tex')
                with open(error_tex, 'w', encoding='utf-8') as f:
                    f.write(tikz_code)
                    
                log_path = os.path.join(work_dir, "tikz.log")
                if os.path.exists(log_path):
                    error_log = os.path.join(ERROR_TIKZ_DIR, f'{timestamp}_{file_id}.log')
                    with open(log_path, 'r', encoding='utf-8') as src, open(error_log, 'w', encoding='utf-8') as dst:
                        log_content = src.read()
                        dst.write(log_content)
                        error_log_full = log_content
                        
                error = "Lỗi khi biên dịch hoặc chuyển đổi SVG."
                if hasattr(ex, 'stderr') and ex.stderr:
                    error += f"<br><br><b>Chi tiết lỗi từ LaTeX:</b><pre>{ex.stderr}</pre>"
                    
                error_details = []
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r', encoding='utf-8') as log_file:
                            for line in log_file:
                                if line.startswith("!") or 'error' in line.lower():
                                    error_details.append(line.strip())
                            if error_details:
                                error += "<br><br><b>Chi tiết lỗi từ Log:</b><pre>" + "\n".join(error_details) + "</pre>"
                    except Exception:
                        pass
                        
    # Lấy danh sách các file SVG đã tạo
    svg_files = get_svg_files()
    return render_template("index.html",
                           tikz_code=tikz_code,
                           svg_url=svg_url,
                           svg_full_url=svg_full_url,
                           svg_content=svg_content,
                           file_info=file_info,
                           svg_files=svg_files,
                           error=error,
                           svg_temp_url=svg_temp_url,
                           svg_temp_id=svg_temp_id,
                           error_log_full=error_log_full,
                           logged_in=logged_in,
                           user_email=user_email,
                           username=username,   # ✅ THÊM
                           avatar=avatar        # ✅ THÊM
    )

@app.route('/temp_svg/<file_id>')
def serve_temp_svg(file_id):
    svg_path = f"/tmp/{file_id}/tikz.svg"
    if os.path.exists(svg_path):
        return send_file(svg_path, mimetype='image/svg+xml')
    return "Not found", 404

@app.route('/save_svg', methods=['POST'])
@login_required
def save_svg():
    data = request.json
    file_id = data.get('file_id')
    tikz_code = data.get('tikz_code', '')
    keywords_raw = data.get('keywords', '').strip()

    if not file_id:
        return jsonify({"error": "Thiếu file_id"}), 400

    work_dir = f"/tmp/{file_id}"
    svg_path_tmp = os.path.join(work_dir, "tikz.svg")
    if not os.path.exists(svg_path_tmp):
        return jsonify({"error": "Không tìm thấy file tạm"}), 404

    now = datetime.now(tz_vn)
    google_id = session.get("google_id", "anonymous")
    timestamp = now.strftime("%H%M%S%d%m%y")
    svg_filename = f"{google_id}_{timestamp}.svg"
    svg_path_final = os.path.join(app.config['UPLOAD_FOLDER'], svg_filename)

    # Ghi file SVG
    with open(svg_path_tmp, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    with open(svg_path_final, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    # Tự động convert sang PNG
    try:
        import io
        from PIL import Image
        with open(svg_path_final, 'rb') as fsvg:
            svg_data = fsvg.read()

        import re
        m = re.search(r'width=["\'](\d+)', svg_content)
        n = re.search(r'height=["\'](\d+)', svg_content)
        if m and n:
            width_svg = int(m.group(1))
            height_svg = int(n.group(1))
        else:
            width_svg = 1000
            height_svg = 1000

        max_w, max_h = 1200, 630
        ratio_svg = width_svg / height_svg
        ratio_fb = max_w / max_h

        if ratio_svg > ratio_fb:
            out_w = max_w
            out_h = int(max_w / ratio_svg)
        else:
            out_h = max_h
            out_w = int(max_h * ratio_svg)

        png_bytes = cairosvg.svg2png(bytestring=svg_data, output_width=out_w, output_height=out_h, dpi=300)
        bg = Image.new("RGB", (max_w, max_h), (255, 230, 240))
        fg = Image.open(io.BytesIO(png_bytes))
        x = (max_w - out_w) // 2
        y = (max_h - out_h) // 2
        bg.paste(fg, (x, y), fg if fg.mode == "RGBA" else None)
        png_path_final = svg_path_final.replace('.svg', '.png')
        bg.save(png_path_final)

    except Exception as e:
        print(f"[WARN] Không thể convert SVG sang PNG: {e}", flush=True)

    # ✅ Thêm vào CSDL với cấu trúc đúng
    try:
        user_id = current_user.id

        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()

        # ✅ INSERT với cấu trúc database đúng
        cursor.execute("""
            INSERT INTO svg_image (filename, tikz_code, keywords, user_id)
            VALUES (%s, %s, %s, %s)
        """, (svg_filename, tikz_code, keywords_raw, user_id))
        conn.commit()

        svg_image_id = cursor.lastrowid
        print(f"✅ svg_image inserted, id={svg_image_id}")

        # Xử lý keywords
        if keywords_raw:
            keywords_list = [kw.strip() for kw in keywords_raw.split(',') if kw.strip()]
            for kw in keywords_list:
                cursor.execute("SELECT id FROM keyword WHERE word = %s", (kw,))
                row = cursor.fetchone()
                if row:
                    keyword_id = row[0]
                else:
                    cursor.execute("INSERT INTO keyword (word) VALUES (%s)", (kw,))
                    conn.commit()
                    keyword_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO svg_image_keyword (svg_image_id, keyword_id) VALUES (%s, %s)",
                    (svg_image_id, keyword_id)
                )
                conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ ERROR inserting into DB: {e}", flush=True)

    # Xóa thư mục tạm
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)

    return jsonify({"success": True, "filename": svg_filename, "url": f"/static/{svg_filename}"})

@app.route('/api/keywords/search')
def api_search_keywords():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM keyword WHERE word LIKE %s COLLATE utf8mb4_general_ci LIMIT 10", (f"%{q}%",))
        results = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        print(f"[ERROR] /api/keywords/search: {e}", flush=True)
        return jsonify([])

def get_user_id_from_session():
    """Helper function for backward compatibility"""
    if current_user.is_authenticated:
        return current_user.id
    
    # Fallback cho session cũ
    user_email = session.get('user_email')
    if not user_email:
        return None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"ERROR get_user_id_from_session: {e}", flush=True)
        return None

@app.route('/delete_svg', methods=['POST'])
@login_required
def delete_svg():
    # Validate request format
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type phải là application/json"}), 400
    
    data = request.json
    svg_image_id = data.get('svg_image_id')
    
    # Log security event
    print(f"🔍 DELETE_SVG request from user {current_user.id} for SVG {svg_image_id} at {datetime.now()}", flush=True)
    
    # Validate input
    try:
        svg_image_id = int(svg_image_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "ID không hợp lệ"}), 400

    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # ✅ KIỂM TRA FILE VÀ OWNERSHIP với cấu trúc database đúng
        cursor.execute("""
            SELECT filename, user_id 
            FROM svg_image 
            WHERE id = %s
        """, (svg_image_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ File not found: SVG ID {svg_image_id}", flush=True)
            return jsonify({"success": False, "error": f"Không tìm thấy ảnh với ID {svg_image_id}"}), 404
        
        # ✅ KIỂM TRA QUYỀN SỞ HỮU với user_id
        if row['user_id'] != current_user.id:
            print(f"🚨 UNAUTHORIZED DELETE ATTEMPT:", flush=True)
            print(f"   - Attempting User ID: {current_user.id}", flush=True)
            print(f"   - File Owner ID: {row['user_id']}", flush=True)
            print(f"   - SVG ID: {svg_image_id}", flush=True)
            print(f"   - User IP: {request.remote_addr}", flush=True)
            
            return jsonify({
                "success": False,
                "error": "Bạn không có quyền xóa file này!"
            }), 403
            
        filename = row['filename']
        print(f"✅ Authorization passed - User {current_user.id} deleting own file {svg_image_id} ({filename})", flush=True)
        
        # Transaction handling
        if conn.in_transaction:
            conn.rollback()
        
        conn.start_transaction(isolation_level='READ COMMITTED')
        
        # Xóa liên kết keyword
        cursor.execute("DELETE FROM svg_image_keyword WHERE svg_image_id = %s", (svg_image_id,))
        keyword_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {keyword_deleted} liên kết keyword", flush=True)
        
        # Xóa likes
        cursor.execute("DELETE FROM svg_like WHERE svg_image_id = %s", (svg_image_id,))
        likes_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {likes_deleted} likes", flush=True)
        
        # Xóa action logs
        cursor.execute("DELETE FROM svg_action_log WHERE svg_image_id = %s", (svg_image_id,))
        logs_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {logs_deleted} action logs", flush=True)
        
        # Xóa user action logs
        cursor.execute("DELETE FROM user_action_log WHERE target_svg_id = %s", (svg_image_id,))
        user_logs_deleted = cursor.rowcount
        print(f"🗑️ Đã xóa {user_logs_deleted} user action logs", flush=True)
        
        # Xóa bản ghi chính
        cursor.execute("DELETE FROM svg_image WHERE id = %s", (svg_image_id,))
        svg_deleted = cursor.rowcount
        if svg_deleted == 0:
            conn.rollback()
            return jsonify({"success": False, "error": "Không thể xóa bản ghi"}), 500
            
        print(f"🗑️ Đã xóa bản ghi svg_image: id={svg_image_id}", flush=True)
        
        # Commit transaction
        conn.commit()
        print(f"✅ Transaction committed thành công", flush=True)
        
        # Xóa file vật lý
        if filename:
            svg_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            png_filename = filename.replace('.svg', '.png')
            png_file_path = os.path.join(app.config['UPLOAD_FOLDER'], png_filename)
            
            def safe_delete_file(file_path, file_type):
                if not os.path.exists(file_path):
                    return False
                try:
                    os.remove(file_path)
                    print(f"✅ Đã xóa file {file_type}: {file_path}", flush=True)
                    return True
                except Exception as e:
                    print(f"❌ Lỗi xóa file {file_type}: {e}", flush=True)
                    return False
            
            svg_deleted = safe_delete_file(svg_file_path, "SVG")
            png_deleted = safe_delete_file(png_file_path, "PNG")
        
        print(f"✅ File successfully deleted by authorized user {current_user.id}: {filename}", flush=True)
        return jsonify({"success": True, "message": "Đã xóa ảnh thành công"})
        
    except mysql.connector.Error as db_error:
        print(f"❌ Lỗi database: {db_error}", flush=True)
        if conn:
            try:
                if conn.in_transaction:
                    conn.rollback()
            except:
                pass
        return jsonify({"success": False, "error": f"Lỗi database: {str(db_error)}"}), 500
        
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}", flush=True)
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        if conn:
            try:
                if conn.in_transaction:
                    conn.rollback()
            except:
                pass
        return jsonify({"success": False, "error": "Lỗi khi xóa ảnh"}), 500
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

# ✅ API LIKE/UNLIKE
@app.route('/like_svg', methods=['POST'])
@login_required
def like_svg():
    data = request.json
    svg_id = data.get('svg_id')
    action = data.get('action')  # 'like' or 'unlike'
    
    if not svg_id or action not in ['like', 'unlike']:
        return jsonify({"success": False, "message": "Invalid parameters"}), 400
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Kiểm tra SVG tồn tại
        cursor.execute("SELECT id FROM svg_image WHERE id = %s", (svg_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "SVG not found"}), 404
            
        if action == 'like':
            # Thêm like (nếu chưa like)
            cursor.execute("""
                INSERT IGNORE INTO svg_like (user_id, svg_image_id) 
                VALUES (%s, %s)
            """, (current_user.id, svg_id))
            
            # Log action
            cursor.execute("""
                INSERT INTO user_action_log (user_id, target_svg_id, action_type) 
                VALUES (%s, %s, 'like')
            """, (current_user.id, svg_id))
        else:
            # Xóa like
            cursor.execute("""
                DELETE FROM svg_like 
                WHERE user_id = %s AND svg_image_id = %s
            """, (current_user.id, svg_id))
            
            # Log action
            cursor.execute("""
                INSERT INTO user_action_log (user_id, target_svg_id, action_type) 
                VALUES (%s, %s, 'unlike')
            """, (current_user.id, svg_id))
        
        conn.commit()
        
        # Đếm tổng số likes
        cursor.execute("SELECT COUNT(*) as count FROM svg_like WHERE svg_image_id = %s", (svg_id,))
        like_count = cursor.fetchone()['count']
        
        # Kiểm tra user hiện tại đã like chưa
        cursor.execute("""
            SELECT COUNT(*) as count FROM svg_like 
            WHERE user_id = %s AND svg_image_id = %s
        """, (current_user.id, svg_id))
        is_liked = cursor.fetchone()['count'] > 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Successfully {action}d",
            "like_count": like_count,
            "is_liked": is_liked
        })
        
    except Exception as e:
        print(f"Error in like_svg: {e}", flush=True)
        return jsonify({"success": False, "message": "Database error"}), 500

# ✅ API FOLLOW/UNFOLLOW
@app.route('/follow/<int:followee_id>', methods=['POST'])
@login_required
def follow_user(followee_id):
    if followee_id == current_user.id:
        return jsonify({"success": False, "message": "Cannot follow yourself"}), 400
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        
        # Kiểm tra user tồn tại
        cursor.execute("SELECT id FROM user WHERE id = %s", (followee_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Thêm follow
        cursor.execute("""
            INSERT IGNORE INTO user_follow (follower_id, followee_id) 
            VALUES (%s, %s)
        """, (current_user.id, followee_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO user_action_log (user_id, target_user_id, action_type) 
            VALUES (%s, %s, 'follow')
        """, (current_user.id, followee_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Successfully followed"})
        
    except Exception as e:
        print(f"Error in follow_user: {e}", flush=True)
        return jsonify({"success": False, "message": "Database error"}), 500

@app.route('/unfollow/<int:followee_id>', methods=['POST'])
@login_required
def unfollow_user(followee_id):
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        
        # Xóa follow
        cursor.execute("""
            DELETE FROM user_follow 
            WHERE follower_id = %s AND followee_id = %s
        """, (current_user.id, followee_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO user_action_log (user_id, target_user_id, action_type) 
            VALUES (%s, %s, 'unfollow')
        """, (current_user.id, followee_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Successfully unfollowed"})
        
    except Exception as e:
        print(f"Error in unfollow_user: {e}", flush=True)
        return jsonify({"success": False, "message": "Database error"}), 500

# ✅ API FOLLOWED POSTS
@app.route('/api/followed_posts')
@login_required
def api_followed_posts():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Lấy posts từ người user đang follow
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.created_at,
                u.id as creator_id,
                u.username as creator_username,
                COUNT(sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            JOIN user_follow uf ON u.id = uf.followee_id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            WHERE uf.follower_id = %s
            GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username, user_like.id
            ORDER BY s.created_at DESC
            LIMIT 50
        """, (current_user.id, current_user.id))
        
        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row['id'],
                'filename': row['filename'],
                'tikz_code': row['tikz_code'],
                'url': url_for('static', filename=row['filename']),
                'creator_id': row['creator_id'],
                'creator_username': row['creator_username'],
                'created_time_vn': format_time_vn(row['created_at']),
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
            })
        
        cursor.close()
        conn.close()
        return jsonify(posts)
        
    except Exception as e:
        print(f"Error in api_followed_posts: {e}", flush=True)
        return jsonify([]), 500

@app.route('/api/files')
@login_required
def api_files():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Lấy tất cả files đã lưu
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.created_at,
                u.id as creator_id,
                u.username as creator_username,
                COUNT(sl.id) as like_count,
                CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
            GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username, user_like.id
            ORDER BY s.created_at DESC
            LIMIT 50
        """, (current_user.id,))
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'id': row['id'],
                'filename': row['filename'],
                'tikz_code': row['tikz_code'],
                'url': url_for('static', filename=row['filename']),
                'creator_id': row['creator_id'],
                'creator_username': row['creator_username'],
                'created_time_vn': format_time_vn(row['created_at']),
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
            })
        
        cursor.close()
        conn.close()
        return jsonify(files)
        
    except Exception as e:
        print(f"Error in api_files: {e}", flush=True)
        return jsonify([]), 500

@app.route('/delete_temp_svg', methods=['POST'])
def delete_temp_svg():
    data = request.json
    file_id = data.get('file_id')
    if not file_id:
        return jsonify({"error": "Thiếu file_id"}), 400
    work_dir = f"/tmp/{file_id}"
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)
    return jsonify({"success": True})

@app.route('/temp_convert', methods=['POST'])
def temp_convert():
    data = request.json
    file_id = data.get('file_id')
    fmt = data.get('fmt', 'png')
    width = data.get('width')
    height = data.get('height')
    dpi = data.get('dpi')
    if not file_id or fmt not in ('png', 'jpeg'):
        return jsonify({'error': 'Tham số không hợp lệ!'}), 400
    work_dir = f"/tmp/{file_id}"
    svg_path = os.path.join(work_dir, "tikz.svg")
    if not os.path.exists(svg_path):
        return jsonify({'error': 'Không tìm thấy file SVG tạm!'}), 404
    out_name = f"tikz.{fmt}"
    out_path = os.path.join(work_dir, out_name)
    try:
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        cairosvg_args = {}
        if width: cairosvg_args['output_width'] = int(width)
        if height: cairosvg_args['output_height'] = int(height)
        if dpi: cairosvg_args['dpi'] = int(dpi)
        if fmt == 'png':
            cairosvg.svg2png(bytestring=svg_data, write_to=out_path, **cairosvg_args)
        elif fmt == 'jpeg':
            tmp_png = out_path + '.tmp.png'
            cairosvg.svg2png(bytestring=svg_data, write_to=tmp_png, **cairosvg_args)
            with Image.open(tmp_png) as im:
                if im.mode == 'RGBA':
                    background = Image.new('RGB', im.size, (255, 255, 255))
                    background.paste(im, mask=im.split()[3])
                else:
                    background = im.convert('RGB')
                background.save(out_path, 'JPEG', quality=95)
            os.remove(tmp_png)
        url = f"/temp_img/{file_id}/{out_name}"
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': f'Lỗi chuyển đổi: {str(e)}'}), 500

@app.route('/temp_img/<file_id>/<filename>')
def serve_temp_img(file_id, filename):
    img_path = f"/tmp/{file_id}/{filename}"
    if os.path.exists(img_path):
        if filename.endswith('.png'):
            return send_file(img_path, mimetype='image/png')
        elif filename.endswith('.jpeg') or filename.endswith('.jpg'):
            return send_file(img_path, mimetype='image/jpeg')
    return "Not found", 404

@app.route('/convert', methods=['POST'])
def convert_svg():
    data = request.json
    filename = data.get('filename')
    fmt = data.get('fmt', 'png')
    width = data.get('width')
    height = data.get('height')
    dpi = data.get('dpi')

    if not filename or fmt not in ('png', 'jpeg'):
        return jsonify({'error': 'Tham số không hợp lệ!'}), 400

    # Validation kích thước ảnh
    max_pixels = 60000000  # 60MP giới hạn
    
    # Kiểm tra nếu có width và height
    if width and height:
        total_pixels = int(width) * int(height)
        if total_pixels > max_pixels:
            return jsonify({'error': f'Kích thước ảnh quá lớn! Tối đa {max_pixels//1000000}MP (hiện tại: {total_pixels//1000000}MP)'}), 400
    
    # Kiểm tra DPI quá cao
    if dpi and int(dpi) > 2000:
        return jsonify({'error': f'DPI quá cao! Tối đa 2000 DPI (hiện tại: {dpi} DPI)'}), 400

    svg_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(svg_path):
        return jsonify({'error': 'Không tìm thấy file SVG!'}), 404

    out_name = f"tikz.{fmt}"
    out_path = os.path.join(app.config['UPLOAD_FOLDER'], out_name)
    try:
        with open(svg_path, 'rb') as f:
            svg_data = f.read()
        

        cairosvg_args = {}
        if width: cairosvg_args['output_width'] = int(width)
        if height: cairosvg_args['output_height'] = int(height)
        if dpi: cairosvg_args['dpi'] = int(dpi)
        
        if fmt == 'png':
            cairosvg.svg2png(bytestring=svg_data, write_to=out_path, **cairosvg_args)
            # Kiểm tra kích thước ảnh PNG
            try:
                with Image.open(out_path) as im:
                    actual_pixels = im.size[0] * im.size[1]
                    if actual_pixels > max_pixels:
                        os.remove(out_path)
                        # Tính toán dung lượng ước tính
                        estimated_size_mb = (actual_pixels * 4) / (1024 * 1024)
                        return jsonify({
                            'error': f'Kích thước ảnh quá lớn! Tối đa {max_pixels//1000000}MP (hiện tại: {actual_pixels//1000000}MP)',
                            'estimated_size_mb': f'{estimated_size_mb:.1f}MB',
                            'note': 'Dung lượng thực tế có thể nhỏ hơn do nén'
                        }), 400
            except Exception as img_error:
                if os.path.exists(out_path):
                    os.remove(out_path)
                raise img_error
        elif fmt == 'jpeg':
            tmp_png = out_path + '.tmp.png'
            cairosvg.svg2png(bytestring=svg_data, write_to=tmp_png, **cairosvg_args)
            
            try:
                with Image.open(tmp_png) as im:
                    # Kiểm tra kích thước ảnh sau khi convert
                    actual_pixels = im.size[0] * im.size[1]
                    if actual_pixels > max_pixels:
                        os.remove(tmp_png)
                        # Tính toán dung lượng ước tính
                        estimated_size_mb = (actual_pixels * 4) / (1024 * 1024)
                        return jsonify({
                            'error': f'Kích thước ảnh quá lớn! Tối đa {max_pixels//1000000}MP (hiện tại: {actual_pixels//1000000}MP)',
                            'estimated_size_mb': f'{estimated_size_mb:.1f}MB',
                            'note': 'Dung lượng thực tế có thể nhỏ hơn do nén'
                        }), 400
                    
                    if im.mode == 'RGBA':
                        background = Image.new('RGB', im.size, (255, 255, 255))
                        background.paste(im, mask=im.split()[3])
                    else:
                        background = im.convert('RGB')
                    background.save(out_path, 'JPEG', quality=95)
            except Exception as img_error:
                if os.path.exists(tmp_png):
                    os.remove(tmp_png)
                raise img_error
            finally:
                if os.path.exists(tmp_png):
                    os.remove(tmp_png)
                    
        url = f"/static/{out_name}"
        
        # Lấy thông tin dung lượng file
        file_size = os.path.getsize(out_path) if os.path.exists(out_path) else None
        
        # Lấy thông tin kích thước ảnh thực tế
        actual_size = None
        if os.path.exists(out_path):
            try:
                with Image.open(out_path) as im:
                    actual_size = f"{im.size[0]}x{im.size[1]} pixels"
            except:
                pass
        
        return jsonify({
            'url': url,
            'file_size': file_size,
            'actual_size': actual_size
        })
    except Exception as e:
        # Cleanup file tạm nếu có lỗi
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except:
                pass
        return jsonify({'error': f'Lỗi chuyển đổi: {str(e)}'}), 500

@app.route('/view_svg/<filename>')
def view_svg(filename):
    svg_url = f"/static/{filename}"
    png_url = f"/static/{filename.replace('.svg', '.png')}"

    tikz_code = None
    display_name = filename

    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT tikz_code, user_id 
            FROM svg_image 
            WHERE filename = %s 
            LIMIT 1
        """, (filename,))
        row = cursor.fetchone()

        if row:
            tikz_code = row['tikz_code']
            user_id = row['user_id']

            if user_id:
                cursor.execute("SELECT username FROM user WHERE id = %s", (user_id,))
                user_row = cursor.fetchone()
                if user_row and user_row['username']:
                    display_name = f"Người tạo: {user_row['username']}"

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] in /view_svg DB lookup: {e}", flush=True)

    # Lấy thông tin user hiện tại
    user_email = current_user.email if current_user.is_authenticated else None
    username = current_user.username if current_user.is_authenticated else None
    avatar = current_user.avatar if current_user.is_authenticated else None

    return render_template(
        "view_svg.html",
        svg_url=svg_url,
        png_url=png_url,
        tikz_code=tikz_code,
        filename=filename,
        display_name=display_name,
        user_email=user_email,
        username=username,
        avatar=avatar
    )

@app.route('/logout')
def logout():
    print("DEBUG: Logout called")
    logout_user()
    session.clear()
    next_url = request.args.get('next') or url_for('index')
    resp = make_response(redirect(next_url))
    print("DEBUG: About to clear cookies")
    resp.set_cookie('session', '', expires=0)
    resp.set_cookie('remember_token', '', expires=0)
    print("DEBUG: Logout finished, returning response")
    return resp

@app.route('/profile/me')
@login_required
def profile_me_redirect():
    return redirect(url_for('profile_user', user_id=current_user.id))

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile_user(user_id):
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        if is_owner and request.method == 'POST':
            new_username = request.form.get("username", "").strip()
            new_bio = request.form.get("bio", "").strip()
            cursor.execute("UPDATE user SET username=%s, bio=%s WHERE id=%s", (new_username, new_bio, user_id))
            conn.commit()
            flash("Đã cập nhật hồ sơ!", "success")
            # Redirect để reload trang và cập nhật tên mới
            return redirect(url_for('profile_user', user_id=user_id))

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # Lấy danh sách SVG với cấu trúc database đúng
        if current_user_id:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id, user_like.id
                ORDER BY s.created_at DESC
            """, (current_user_id, user_id))
        else:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    0 as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id
                ORDER BY s.created_at DESC
            """, (user_id,))
        
        svg_rows = cursor.fetchall()

        svg_files = []
        for row in svg_rows:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
            file_size_kb = round(os.path.getsize(filepath) / 1024, 2) if os.path.exists(filepath) else None
            
            like_count = row.get('like_count', 0) or 0
            is_liked = bool(row.get('is_liked_by_current_user', False))
            
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'url': url_for('static', filename=row['filename']),
                'tikz_code': row['tikz_code'] or '',
                'created_time': format_time_vn(row['created_at']),
                'size': file_size_kb,
                'like_count': like_count,
                'is_liked_by_current_user': is_liked,
                'creator_id': row['user_id']  # ✅ Dùng user_id làm creator_id
            })

        # Follow logic
        is_followed = False
        follower_count = 0
        
        # Luôn tính follower_count bất kể đăng nhập hay không
        cursor.execute("SELECT COUNT(*) as count FROM user_follow WHERE followee_id=%s", (user_id,))
        follower_count = cursor.fetchone()['count']
        
        # Chỉ kiểm tra is_followed nếu đã đăng nhập và không phải owner
        if current_user_id and not is_owner:
            cursor.execute("SELECT 1 FROM user_follow WHERE follower_id=%s AND followee_id=%s", (current_user_id, user_id))
            is_followed = cursor.fetchone() is not None

        return render_template("profile.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            email_verified=True,
            svg_files=svg_files,
            is_owner=is_owner,
            is_followed=is_followed,
            follower_count=follower_count,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None
        )
    except Exception as e:
        print(f"❌ General error in profile_user: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

# ✅ Thêm 3 routes mới cho các trang profile đã tách

@app.route('/profile/<int:user_id>/settings', methods=['GET', 'POST'])
def profile_settings(user_id):
    """Trang cài đặt profile - chỉ owner mới có thể truy cập"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)
    
    # Chỉ owner mới có thể truy cập trang settings
    if not is_owner:
        return redirect(url_for('profile_user', user_id=user_id))

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            new_username = request.form.get("username", "").strip()
            new_bio = request.form.get("bio", "").strip()
            avatar_file = request.files.get('avatar')
            avatar_cropped_data = request.form.get('avatar_cropped')

            # Cập nhật username và bio
            cursor.execute("UPDATE user SET username=%s, bio=%s WHERE id=%s", (new_username, new_bio, user_id))
            
            # ✅ Xử lý avatar upload - File trực tiếp
            if avatar_file and avatar_file.filename != '':
                # Xoá avatar cũ
                cursor.execute("SELECT avatar FROM user WHERE id = %s", (user_id,))
                old_avatar_row = cursor.fetchone()
                old_avatar = old_avatar_row['avatar'] if old_avatar_row else None
                if old_avatar:
                    old_path = os.path.join('static/avatars', old_avatar)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"[WARN] Không thể xóa avatar cũ: {e}", flush=True)

                # Lưu file mới
                filename = secure_filename(avatar_file.filename)
                save_path = os.path.join('static/avatars', filename)
                avatar_file.save(save_path)

                cursor.execute("UPDATE user SET avatar = %s WHERE id = %s", (filename, user_id))

            # ✅ Xử lý avatar upload - Base64 cropped
            elif avatar_cropped_data and avatar_cropped_data.startswith('data:image'):
                try:
                    match = re.match(r'data:image/(png|jpeg|jpg|gif);base64,(.*)', avatar_cropped_data)
                    if match:
                        ext = match.group(1)
                        b64_data = match.group(2)

                        # Xoá avatar cũ
                        cursor.execute("SELECT avatar FROM user WHERE id = %s", (user_id,))
                        old_avatar_row = cursor.fetchone()
                        old_avatar = old_avatar_row['avatar'] if old_avatar_row else None
                        if old_avatar:
                            old_path = os.path.join('static/avatars', old_avatar)
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                except Exception as e:
                                    print(f"[WARN] Không thể xóa avatar cũ: {e}", flush=True)

                        # Tạo tên file random
                        unique_id = uuid.uuid4().hex
                        filename = f"avatar_{unique_id}.{ext}"
                        save_path = os.path.join('static/avatars', filename)

                        # Decode và lưu
                        import base64
                        with open(save_path, 'wb') as f:
                            f.write(base64.b64decode(b64_data))

                        # Update DB
                        cursor.execute("UPDATE user SET avatar = %s WHERE id = %s", (filename, user_id))
                except Exception as e:
                    print(f"[WARN] Error saving cropped avatar: {e}", flush=True)
                    flash("Có lỗi khi lưu ảnh đại diện đã cắt.", "error")

            conn.commit()
            flash("Đã cập nhật hồ sơ!", "success")
            return redirect(url_for('profile_settings', user_id=user_id))

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        return render_template("profile_settings.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            email_verified=True,
            is_owner=is_owner,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None
        )
    except Exception as e:
        print(f"❌ General error in profile_settings: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

@app.route('/profile/<int:user_id>/svg-files')
def profile_svg_files(user_id):
    """Trang hiển thị các file SVG của user"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # Lấy danh sách SVG với cấu trúc database đúng
        if current_user_id:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id, user_like.id
                ORDER BY s.created_at DESC
            """, (current_user_id, user_id))
        else:
            cursor.execute("""
                SELECT 
                    s.id, 
                    s.filename, 
                    s.tikz_code, 
                    s.keywords, 
                    s.created_at,
                    s.user_id,
                    COUNT(sl.id) as like_count,
                    0 as is_liked_by_current_user
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                WHERE s.user_id = %s
                GROUP BY s.id, s.filename, s.tikz_code, s.keywords, s.created_at, s.user_id
                ORDER BY s.created_at DESC
            """, (user_id,))
        
        svg_rows = cursor.fetchall()

        svg_files = []
        for row in svg_rows:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
            file_size_kb = round(os.path.getsize(filepath) / 1024, 2) if os.path.exists(filepath) else None
            
            like_count = row.get('like_count', 0) or 0
            is_liked = bool(row.get('is_liked_by_current_user', False))
            
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'url': url_for('static', filename=row['filename']),
                'tikz_code': row['tikz_code'] or '',
                'created_time': format_time_vn(row['created_at']),
                'size': file_size_kb,
                'like_count': like_count,
                'is_liked_by_current_user': is_liked,
                'creator_id': row['user_id']
            })

        # Follow logic
        is_followed = False
        follower_count = 0
        
        # Luôn tính follower_count bất kể đăng nhập hay không
        cursor.execute("SELECT COUNT(*) as count FROM user_follow WHERE followee_id=%s", (user_id,))
        follower_count = cursor.fetchone()['count']
        
        # Chỉ kiểm tra is_followed nếu đã đăng nhập và không phải owner
        if current_user_id and not is_owner:
            cursor.execute("SELECT 1 FROM user_follow WHERE follower_id=%s AND followee_id=%s", (current_user_id, user_id))
            is_followed = cursor.fetchone() is not None

        return render_template("profile_svg_files.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            email_verified=True,
            svg_files=svg_files,
            is_owner=is_owner,
            is_followed=is_followed,
            follower_count=follower_count,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None
        )
    except Exception as e:
        print(f"❌ General error in profile_svg_files: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

@app.route('/profile/<int:user_id>/followed-posts')
@login_required
def profile_followed_posts(user_id):
    """Trang hiển thị bài đăng theo dõi - chỉ owner mới có thể truy cập"""
    current_user_id = current_user.id if current_user.is_authenticated else None
    is_owner = (user_id == current_user_id)
    
    # Chỉ owner mới có thể truy cập trang followed posts
    if not is_owner:
        return redirect(url_for('profile_user', user_id=user_id))

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, username, avatar, bio, email FROM user WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        return render_template("profile_followed_posts.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            is_owner=is_owner,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None
        )
    except Exception as e:
        print(f"❌ General error in profile_followed_posts: {e}", flush=True)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", flush=True)
        return f"Error: {str(e)}", 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass

def get_user_by_email(email):
    """Lấy thông tin user từ database theo email"""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, avatar FROM user WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return user_data
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None

@app.context_processor
def inject_user_info():
    """Context processor để truyền thông tin user ra mọi template"""
    if current_user.is_authenticated:
        return {
            'current_user_email': current_user.email,
            'current_username': current_user.username,
            'current_avatar': current_user.avatar
        }
    return {
        'current_user_email': None,
        'current_username': None,
        'current_avatar': None
    }

@app.route('/api/like_counts', methods=['POST'])
def api_like_counts():
    data = request.get_json()
    svg_ids = data.get('ids', [])
    filenames = data.get('filenames', [])
    
    # Hỗ trợ cả ids và filenames
    if not isinstance(svg_ids, list) and not isinstance(filenames, list):
        return jsonify({"error": "Invalid input"}), 400

    # ✅ Trả về cả like count và trạng thái like của user hiện tại
    result = {}
    current_user_id = current_user.id if current_user.is_authenticated else None
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Xử lý filenames nếu có
        if filenames:
            format_strings = ','.join(['%s'] * len(filenames))
            
            # Query để lấy like count theo filename
            cursor.execute(f"""
                SELECT 
                    s.filename,
                    COUNT(sl.id) as like_count
                FROM svg_image s
                LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                WHERE s.filename IN ({format_strings})
                GROUP BY s.filename
            """, tuple(filenames))
            
            for row in cursor.fetchall():
                filename = row['filename']
                result[filename] = {
                    'like_count': row['like_count']
                }
            
            # Đảm bảo trả về cho tất cả filenames, kể cả không có like
            for filename in filenames:
                if filename not in result:
                    result[filename] = {
                        'like_count': 0
                    }
        
        # Xử lý svg_ids nếu có (giữ nguyên logic cũ)
        if svg_ids:
            format_strings = ','.join(['%s'] * len(svg_ids))
            
            # ✅ Query để lấy cả like count và trạng thái like của user hiện tại
            if current_user_id:
                cursor.execute(f"""
                    SELECT 
                        s.id as svg_image_id,
                        COUNT(sl.id) as like_count,
                        CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
                    FROM svg_image s
                    LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                    LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = %s
                    WHERE s.id IN ({format_strings})
                    GROUP BY s.id, user_like.id
                """, (current_user_id,) + tuple(svg_ids))
            else:
                cursor.execute(f"""
                    SELECT 
                        s.id as svg_image_id,
                        COUNT(sl.id) as like_count,
                        0 as is_liked_by_current_user
                    FROM svg_image s
                    LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
                    WHERE s.id IN ({format_strings})
                    GROUP BY s.id
                """, tuple(svg_ids))
            
            for row in cursor.fetchall():
                svg_id = str(row['svg_image_id'])
                result[svg_id] = {
                    'like_count': row['like_count'],
                    'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
                }
            
            # ✅ Đảm bảo trả về cho tất cả svg_ids, kể cả không có like
            for svg_id in svg_ids:
                if str(svg_id) not in result:
                    result[str(svg_id)] = {
                        'like_count': 0,
                        'is_liked_by_current_user': False
                    }
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error in api_like_counts: {e}", flush=True)
        return jsonify({"error": "Database error"}), 500

    return jsonify(result)

@app.route('/api/follower_count/<int:user_id>', methods=['GET'])
def api_follower_count(user_id):
    """API endpoint để lấy số follower count của một user"""
    print(f"🔄 API called: /api/follower_count/{user_id}")
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query để lấy số follower count
        cursor.execute("""
            SELECT COUNT(*) as follower_count
            FROM user_follow
            WHERE followee_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        follower_count = result['follower_count'] if result else 0
        
        print(f"🔄 Database result for user {user_id}: {follower_count} followers")
        
        cursor.close()
        conn.close()
        
        response_data = {
            "success": True,
            "follower_count": follower_count
        }
        print(f"🔄 API response: {response_data}")
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in api_follower_count: {e}")
        return jsonify({
            "success": False,
            "error": "Database error"
        }), 500

@app.route('/api/follow_status/<int:user_id>', methods=['GET'])
def api_follow_status(user_id):
    """API endpoint để lấy trạng thái follow của current user với user_id"""
    print(f"🔄 API called: /api/follow_status/{user_id}")
    
    # Kiểm tra đăng nhập
    if not current_user.is_authenticated:
        return jsonify({
            "success": False,
            "error": "Not logged in"
        }), 401
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query để kiểm tra trạng thái follow
        cursor.execute("""
            SELECT COUNT(*) as is_following
            FROM user_follow
            WHERE follower_id = %s AND followee_id = %s
        """, (current_user.id, user_id))
        
        result = cursor.fetchone()
        is_following = result['is_following'] > 0 if result else False
        
        print(f"🔄 Follow status for user {user_id}: {is_following}")
        
        cursor.close()
        conn.close()
        
        response_data = {
            "success": True,
            "is_following": is_following
        }
        print(f"🔄 API response: {response_data}")
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in api_follow_status: {e}")
        return jsonify({
            "success": False,
            "error": "Database error"
        }), 500



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)