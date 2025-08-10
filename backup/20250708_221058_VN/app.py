from flask import Flask, request, render_template, url_for, send_file, jsonify, session, redirect, flash # THÊM flash
import os
import subprocess
import uuid
from datetime import datetime
import glob
import cairosvg
from PIL import Image
import re
import traceback
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import mysql.connector

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
app.config['DEBUG'] = True # THÊM DÒNG NÀY

# Cấu hình bảo mật session cookie
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Thêm dòng debug này VÀO app.py để xem lỗi
print("DEBUG: Google OAuth blueprint being created with scope:")
print(f"DEBUG Scope: {['openid', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']}")

TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{{standalone}}
\usepackage{{fontspec}}
\usepackage{{polyglossia}}
\setdefaultlanguage{{vietnamese}}
\usepackage{{amsmath,amssymb}}
\usepackage{{tikz,tikz-3dplot,pgfplots,tkz-tab,tkz-euclide}}
\usepackage{{xcolor}}
\usetikzlibrary {{math}}
\usetikzlibrary{{calc,angles,intersections,shapes.geometric,arrows,decorations.markings,arrows.meta,patterns.meta,patterns,quotes}}
\usetikzlibrary{{hobby}}
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
    """Lấy danh sách các file SVG trong thư mục static"""
    svg_files = []
    static_dir = app.config['UPLOAD_FOLDER']
    if os.path.exists(static_dir):
        for file in glob.glob(os.path.join(static_dir, "*.svg")):
            filename = os.path.basename(file)
            file_path = os.path.join(static_dir, filename)
            file_size = os.path.getsize(file_path)
            file_size_kb = round(file_size / 1024, 2)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path), tz_vn)

            # Parse tên file để lấy thông tin thời gian
            try:
                if len(filename) == 12 and filename.endswith('.svg'):  # hhmmssddmmyy.svg
                    time_str = filename[:-4]  # Bỏ .svg
                    hour = time_str[:2]
                    minute = time_str[2:4]
                    second = time_str[4:6]
                    day = time_str[6:8]
                    month = time_str[8:10]
                    year = "20" + time_str[10:12]
                    created_time = f"{hour}:{minute}:{second} - {day}/{month}/{year}"
                else:
                    created_time = file_time.strftime("%H:%M:%S - %d/%m/%Y")
            except:
                created_time = file_time.strftime("%H:%M:%S - %d/%m/%Y")

            # Đọc code TikZ gốc nếu có
            tikz_orig_filename = filename.replace('.svg', '.orig.tex')
            tikz_code = None
            tikz_orig_path = os.path.join(static_dir, tikz_orig_filename)
            if os.path.exists(tikz_orig_path):
                try:
                    with open(tikz_orig_path, 'r', encoding='utf-8') as f:
                        tikz_code = f.read()
                except Exception:
                    tikz_code = None

            # 💡 TÍNH TOÁN display_name
            display_name = filename
            if '_' in filename:
                google_id_part = filename.split('_')[0]
                if google_id_part.isdigit():
                    try:
                        conn = mysql.connector.connect(
                            host=os.environ.get('DB_HOST', 'localhost'),
                            user=os.environ.get('DB_USER', 'hiep1987'),
                            password=os.environ.get('DB_PASSWORD', ''),
                            database=os.environ.get('DB_NAME', 'tikz2svg')
                        )
                        cursor = conn.cursor()
                        cursor.execute("SELECT username FROM user WHERE google_id = %s", (google_id_part,))
                        result = cursor.fetchone()
                        if result and result[0]:
                            display_name = f"Người tạo: {result[0]}"
                        cursor.close()
                        conn.close()
                    except Exception as e:
                        print(f"[WARN] DB error while resolving google_id {google_id_part}: {e}", flush=True)

            svg_files.append({
                'filename': filename,
                'display_name': display_name,
                'url': f"/static/{filename}",
                'size': file_size_kb,
                'created_time': created_time,
                'file_time': file_time,
                'tikz_code': tikz_code
            })

    # Sắp xếp theo thời gian tạo mới nhất
    svg_files.sort(key=lambda x: x['file_time'], reverse=True)
    return svg_files


def clean_control_chars(text):
    return re.sub(r'[\x00-\x08\x0B-\x1F\x7F]', '', text)

# --- Thêm secret_key và Google OAuth blueprint ---
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secret-key')
# --- Thêm secret_key và Google OAuth blueprint ---
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'GOOGLE_CLIENT_SECRET'),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ],
    reprompt_select_account=True
)



# Thêm route này để điều khiển điểm vào cho /login/google
# @google_bp.route("/authorized")
# def after_auth():
#     print("DEBUG: Entering /login/google/authorized", flush=True)
#     try:
#         resp = google.get("/oauth2/v2/userinfo")
#         if not resp.ok:
#             print(f"DEBUG: Google API response not OK: {resp.status_code} {resp.text}", flush=True)
#             flash("Đăng nhập thất bại.", category="error")
#             clear_oauth_session()
#             return redirect(url_for("index"))

#         info = resp.json()
#         user_email = info.get("email")
#         google_id = info.get("id")
#         if not user_email or not google_id:
#             flash("Không thể lấy thông tin người dùng từ Google.", "danger")
#             clear_oauth_session()
#             return redirect(url_for("index"))

#         print(f"DEBUG: Got userinfo email={user_email}, google_id={google_id}", flush=True)
#         print(f"DEBUG: user_exists = {user_exists}", flush=True)

#         conn = mysql.connector.connect(
#             host=os.environ.get('DB_HOST', 'localhost'),
#             user=os.environ.get('DB_USER', 'hiep1987'),
#             password=os.environ.get('DB_PASSWORD', ''),
#             database=os.environ.get('DB_NAME', 'tikz2svg')
#         )
#         cursor = conn.cursor()
#         cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
#         user_exists = cursor.fetchone()

#         if not user_exists:
#             default_username = re.sub(r'[^a-zA-Z0-9_-]', '_', user_email.split('@')[0])
#             cursor.execute(
#                 "INSERT INTO user (email, google_id, username) VALUES (%s, %s, %s)",
#                 (user_email, google_id, default_username)
#             )
#             conn.commit()
#             print(f"DEBUG: User {user_email} INSERTED.", flush=True)
#         else:
#             print(f"DEBUG: User {user_email} already exists.", flush=True)

#         cursor.close()
#         conn.close()

#         session["user_email"] = user_email
#         session["google_id"] = google_id
#         session.modified = True

#         flash(f"Chào mừng, {user_email}!", category="success")
#         return redirect(url_for("index"))

#     except Exception as e:
#         print(f"ERROR in after_auth: {e}", flush=True)
#         traceback.print_exc()
#         flash("Lỗi trong quá trình đăng nhập. Vui lòng thử lại.", "danger")
#         clear_oauth_session()
#         return redirect(url_for("index"))
app.register_blueprint(google_bp, url_prefix="/login")
print("### DEBUG: APP URL MAP ###", flush=True)
print(app.url_map, flush=True)
@app.route("/force_logout_dance")
def force_logout_dance():
    print("DEBUG: Force logout Dance endpoint accessed.", flush=True)
    if hasattr(google, 'token'):
        print("DEBUG: Deleting google.token.", flush=True)
        del google.token
    else:
        print("DEBUG: google.token not found.", flush=True)

    if 'user_email' in session:
        print(f"DEBUG: Popping user_email: {session['user_email']}.", flush=True)
        session.pop('user_email')
    if 'google_id' in session:
        print(f"DEBUG: Popping google_id: {session['google_id']}.", flush=True)
        session.pop('google_id')

    session.clear() # Đảm bảo toàn bộ session được dọn dẹp
    session.modified = True # Đảm bảo Flask lưu thay đổi
    print("DEBUG: Session cleared completely.", flush=True)
    flash("Tất cả session và token Flask-Dance đã được xóa. Vui lòng đăng nhập lại.", "info")
    return redirect(url_for("index"))

def clear_oauth_session():
    session.clear()
    session.modified = True
    try:
        del google.token
        print("DEBUG: Google OAuth token deleted (google.token).", flush=True)
    except Exception as e:
        print(f"DEBUG: Error deleting google.token: {e}", flush=True)
    try:
        google_bp.token = None
        print("DEBUG: google_bp.token set to None.", flush=True)
    except Exception as e:
        print(f"DEBUG: Error clearing google_bp.token: {e}", flush=True)
    try:
        google_bp.storage.delete(google_bp)
        print("DEBUG: Google OAuth token deleted (blueprint storage).", flush=True)
    except KeyError:
        print("DEBUG: No google_oauth_token in session to delete (blueprint storage).", flush=True)
    except Exception as e:
        print(f"DEBUG: Error deleting blueprint storage: {e}", flush=True)





# --- Hàm kiểm tra đăng nhập Google ---
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
                except Exception as e:
                    print(f"ERROR inserting user into DB: {e}", flush=True)
                finally:
                    try:
                        cursor.close()
                        conn.close()
                    except:
                        pass




@app.route("/", methods=["GET", "POST"])
def index():
    print(f"DEBUG: Index route accessed - method: {request.method}")
    logged_in = 'user_email' in session
    user_email = session.get('user_email')
    svg_url = None
    svg_full_url = None
    svg_content = None
    file_info = None
    error = None
    svg_temp_url = None
    svg_temp_id = None
    tikz_code = ""
    error_log_full = None
    # --- Chặn biên dịch nếu chưa đăng nhập ---
    if request.method == "POST" and not logged_in:
        return redirect(url_for("google.login"))
        #return redirect(url_for("google.login"))
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
                # Lưu log lỗi nếu có
                log_path = os.path.join(work_dir, "tikz.log")
                if os.path.exists(log_path):
                    error_log = os.path.join(ERROR_TIKZ_DIR, f'{timestamp}_{file_id}.log')
                    with open(log_path, 'r', encoding='utf-8') as src, open(error_log, 'w', encoding='utf-8') as dst:
                        log_content = src.read()
                        dst.write(log_content)
                        error_log_full = log_content
                error = "Lỗi khi biên dịch hoặc chuyển đổi SVG."
                # Đọc stderr của lualatex
                if hasattr(ex, 'stderr') and ex.stderr:
                    error += f"<br><br><b>Chi tiết lỗi từ LaTeX:</b><pre>{ex.stderr}</pre>"
                # Đọc log lỗi chi tiết để hiển thị cho user
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
                           logged_in=logged_in)

@app.route('/temp_svg/<file_id>')
def serve_temp_svg(file_id):
    svg_path = f"/tmp/{file_id}/tikz.svg"
    if os.path.exists(svg_path):
        return send_file(svg_path, mimetype='image/svg+xml')
    return "Not found", 404

@app.route('/save_svg', methods=['POST'])
def save_svg():
    data = request.json
    file_id = data.get('file_id')
    tikz_code = data.get('tikz_code', '')
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
    with open(svg_path_tmp, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    with open(svg_path_final, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    # Lưu code TikZ gốc vào file .orig.tex
    tikz_orig_filename = svg_filename.replace('.svg', '.orig.tex')
    tikz_orig_path_final = os.path.join(app.config['UPLOAD_FOLDER'], tikz_orig_filename)
    with open(tikz_orig_path_final, 'w', encoding='utf-8') as f:
        f.write(tikz_code)
    # Tự động convert SVG sang PNG thumbnail (căn giữa, giữ tỷ lệ, nền hồng)
    try:
        import io
        from PIL import Image
        with open(svg_path_final, 'rb') as fsvg:
            svg_data = fsvg.read()
        # Bước 1: Lấy kích thước SVG gốc
        import re
        m = re.search(r'width=["\'](\d+)', svg_content)
        n = re.search(r'height=["\'](\d+)', svg_content)
        if m and n:
            width_svg = int(m.group(1))
            height_svg = int(n.group(1))
        else:
            # fallback: dùng 1000x1000 nếu không có width/height
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
        # Bước 2: Render SVG ra PNG nhỏ hơn khung
        png_bytes = cairosvg.svg2png(bytestring=svg_data, output_width=out_w, output_height=out_h, dpi=300, background_color=None)
        # Bước 3: Tạo ảnh nền hồng và dán PNG SVG vào giữa
        bg = Image.new("RGB", (max_w, max_h), (255, 230, 240))
        fg = Image.open(io.BytesIO(png_bytes))
        x = (max_w - out_w) // 2
        y = (max_h - out_h) // 2
        bg.paste(fg, (x, y), fg if fg.mode == "RGBA" else None)
        png_path_final = svg_path_final.replace('.svg', '.png')
        bg.save(png_path_final)
    except Exception as e:
        print(f"[WARN] Không thể convert SVG sang PNG: {e}", flush=True)
    # Xóa thư mục tạm
    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)
    return jsonify({"success": True, "filename": svg_filename, "url": f"/static/{svg_filename}"})

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
    print("DEBUG /convert data:", data, flush=True)
    filename = data.get('filename')
    fmt = data.get('fmt', 'png')
    width = data.get('width')
    height = data.get('height')
    dpi = data.get('dpi')

    if not filename or fmt not in ('png', 'jpeg'):
        print("DEBUG /convert: thiếu tham số hoặc định dạng không hợp lệ", flush=True)
        return jsonify({'error': 'Tham số không hợp lệ!'}), 400

    svg_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"DEBUG /convert: svg_path={svg_path}", flush=True)
    if not os.path.exists(svg_path):
        print("DEBUG /convert: Không tìm thấy file SVG!", flush=True)
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
        url = f"/static/{out_name}"
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': f'Lỗi chuyển đổi: {str(e)}'}), 500

@app.route('/view_svg/<filename>')
def view_svg(filename):
    # Xem SVG với meta og:image động cho Facebook share
    import os
    svg_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    png_path = svg_path.replace('.svg', '.png')
    tikz_code = None
    tikz_orig_path = svg_path.replace('.svg', '.orig.tex')
    if os.path.exists(tikz_orig_path):
        with open(tikz_orig_path, 'r', encoding='utf-8') as f:
            tikz_code = f.read()
    svg_url = f"/static/{filename}"
    png_url = f"/static/{filename.replace('.svg', '.png')}"
    return render_template("view_svg.html", svg_url=svg_url, png_url=png_url, tikz_code=tikz_code, filename=filename)

# @app.route('/login_success')
# def login_success():
#     # session đã có user_email rồi (như bạn đã kiểm tra)
#     user_email_from_session = session.get('user_email')
#     if user_email_from_session:
#         flash(f"Chào mừng, {user_email_from_session}!", category="success")
#     else:
#         flash("Chào mừng!", category="success")
# 
#     # Thay vì redirect trực tiếp, hãy render template chuyển hướng JavaScript
#     return render_template('login_success_redirect.html')



@app.route('/logout')
def logout():
    session.clear()
    next_url = request.args.get('next') or url_for('index')
    return redirect(next_url)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Phải login Google rồi mới cho vào
    if 'user_email' not in session:
        flash("Bạn cần đăng nhập trước.", "error")
        return redirect(url_for('google.login'))

    # Lấy email/Google ID từ session
    user_email = session.get('user_email')
    google_id = session.get('google_id')

    # Kết nối CSDL sử dụng biến môi trường
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'hiep1987'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'tikz2svg')
    )
    cursor = conn.cursor(dictionary=True)

    # Nếu POST -> Cập nhật username + avatar
    if request.method == 'POST':
        new_username = request.form.get('username')
        avatar_file = request.files.get('avatar')

        # Kiểm tra user có tồn tại không, nếu không thì tạo mới
        cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            # Tạo user mới
            cursor.execute("INSERT INTO user (email, google_id, username) VALUES (%s, %s, %s)", 
                         (user_email, google_id, new_username or user_email.split('@')[0]))
            conn.commit()
            flash("Tài khoản đã được tạo.", "success")
        else:
            # Update username nếu có
            if new_username:
                cursor.execute("UPDATE user SET username = %s WHERE email = %s", (new_username, user_email))
                conn.commit()
                session["username"] = new_username

        # Upload avatar
        if avatar_file and avatar_file.filename != '':
            filename = secure_filename(avatar_file.filename)
            save_path = os.path.join('static/avatars', filename)
            avatar_file.save(save_path)
            # Lưu chỉ tên file vào database, không lưu đường dẫn đầy đủ
            cursor.execute("UPDATE user SET avatar = %s WHERE email = %s", (filename, user_email))
            conn.commit()
            session["avatar"] = filename

        flash("Thông tin đã được cập nhật.", "success")
        return redirect(url_for('profile'))

    # Lấy thông tin user hiện tại để hiển thị
    cursor.execute("SELECT username, avatar FROM user WHERE email = %s", (user_email,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    username = user_data["username"] if user_data else None
    avatar = user_data["avatar"] if user_data else None

    return render_template("profile.html",
                           user_email=user_email,
                           username=username,
                           avatar=avatar)

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
    user_email = session.get('user_email')
    if user_email:
        user = get_user_by_email(user_email)
        if user:
            return {
                'user_email': user_email,
                'username': user.get('username', ''),
                'avatar': user.get('avatar', '')  # <-- chỉ là tên file!
            }
    return {
        'user_email': None,
        'username': None,
        'avatar': None
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)


