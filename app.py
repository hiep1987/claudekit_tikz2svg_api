from flask import Flask, request, render_template, url_for, send_file, jsonify, session, redirect, flash, make_response, send_from_directory, render_template_string
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import subprocess
import uuid
from datetime import datetime, timezone, timedelta
import time
import glob
import cairosvg
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Tắt giới hạn decompression bomb
import re
import traceback
import random
import string
import json
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import mysql.connector
from typing import Iterable
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_service import init_email_service, get_email_service

load_dotenv()


# --- Static storage root (shared across releases) ---
STATIC_ROOT = os.environ.get('TIKZ_SVG_DIR', os.path.join(os.getcwd(), 'static'))
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(os.path.join(STATIC_ROOT, 'avatars'), exist_ok=True)
os.makedirs(os.path.join(STATIC_ROOT, 'images'), exist_ok=True)

app = Flask(__name__, static_folder=STATIC_ROOT)

# Health check route
@app.route("/health")
def health():
    return {"status": "ok"}, 200

app.config['UPLOAD_FOLDER'] = STATIC_ROOT
app.config['DEBUG'] = False # Tắt debug mode cho production

# ✅ FLASK-LOGIN SETUP
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'google.login'
login_manager.login_message = "Bạn cần đăng nhập để truy cập trang này."

# ✅ USER CLASS
class User(UserMixin):
    def __init__(self, id, email, username=None, avatar=None, bio=None, identity_verified=False):
        self.id = id
        self.email = email
        self.username = username
        self.avatar = avatar
        self.bio = bio
        self.identity_verified = identity_verified
    
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
        cursor.execute("SELECT id, email, username, avatar, bio, identity_verified FROM user WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                avatar=user_data['avatar'],
                bio=user_data['bio'],
                identity_verified=bool(user_data.get('identity_verified', 0))
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
                            try:
                                import shutil
                                shutil.rmtree(folder_path)
                            except Exception as e:
                                print(f"[CLEANUP] Error removing {folder_path}: {e}", flush=True)
        except Exception as e:
            print(f"[CLEANUP] Error in cleanup: {e}", flush=True)
        time.sleep(300)  # Chạy mỗi 5 phút

cleanup_thread = threading.Thread(target=cleanup_tmp_folder, daemon=True)
cleanup_thread.start()

# Session config
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

print("DEBUG: Google OAuth blueprint being created...")

# 1) Khai báo allowlist (có thể mở rộng dần)
SAFE_PACKAGES = {
    # nền tảng
    "fontspec", "polyglossia", "xcolor", "graphicx", "geometry", "setspace",
    # toán
    "amsmath", "amssymb", "amsfonts", "mathtools", "physics", "siunitx", "cancel", "cases",
          # tikz/pgf
      "tikz", "pgfplots", "tikz-3dplot", "tkz-euclide", "tkz-tab", "pgf", "pgfkeys", "pgfornament",
    # chuyên biệt
    "circuitikz", "tikz-timing", "tikz-cd", "tikz-network", "tikzpeople", "tikzmark",
    # bổ sung
    "array", "booktabs", "multirow", "colortbl", "longtable", "tabularx",
}

# (tuỳ chọn) allowlist cho \usetikzlibrary và \usepgfplotslibrary
SAFE_TIKZ_LIBS = {
    "calc","math","positioning","arrows.meta","intersections","angles","quotes",
    "decorations.markings","decorations.pathreplacing","decorations.text",
    "patterns","patterns.meta","shadings","hobby","spy","backgrounds",
    "shapes.geometric","shapes.symbols","shapes.arrows","shapes.multipart",
    "fit","matrix","chains","automata","petri","mindmap","trees",
    "graphs","graphdrawing","lindenmayersystems","fadings","shadows",
    "external","datavisualization","datavisualization.formats.files",
    "datavisualization.formats.files.csv","datavisualization.formats.files.json"
}
SAFE_PGFPLOTS_LIBS = {
    "polar","statistics","dateplot","fillbetween","colorbrewer",
    "groupplots","ternary","smithchart","units"
}

_pkg_re = re.compile(r"^[A-Za-z0-9\-_.]+$")

def _sanitize_name(name: str, *, kind: str, allowed: set[str]) -> str:
    name = (name or "").strip()
    if not _pkg_re.match(name):
        raise ValueError(f"{kind} không hợp lệ: {name!r}")
    if name not in allowed:
        raise ValueError(f"{kind} '{name}' không trong danh sách cho phép")
    return name

def _lines_for_usepackage(pkgs: Iterable[str]) -> str:
    if not pkgs: return ""
    safe = [_sanitize_name(p, kind="Gói", allowed=SAFE_PACKAGES) for p in pkgs]
    # gom các gói phổ biến theo nhóm để gọn, phần còn lại nạp từng cái
    groups = {"ams": {"amsmath","amssymb","amsfonts"}}
    out = []
    ams_in = [p for p in safe if p in groups["ams"]]
    others = [p for p in safe if p not in groups["ams"]]
    if ams_in:
        out.append(r"\usepackage{amsmath,amssymb,amsfonts}")
    for p in others:
        out.append(fr"\usepackage{{{p}}}")
    return "\n".join(dict.fromkeys(out))  # dedupe, giữ thứ tự

def _lines_for_tikz_libs(libs: Iterable[str]) -> str:
    if not libs: return ""
    safe = [_sanitize_name(l, kind="Thư viện TikZ", allowed=SAFE_TIKZ_LIBS) for l in libs]
    return "\n".join(fr"\usetikzlibrary{{{lib}}}" for lib in dict.fromkeys(safe))

def _lines_for_pgfplots_libs(libs: Iterable[str]) -> str:
    if not libs: return ""
    safe = [_sanitize_name(l, kind="Thư viện pgfplots", allowed=SAFE_PGFPLOTS_LIBS) for l in libs]
    return "\n".join(fr"\usepgfplotslibrary{{{l}}}" for l in dict.fromkeys(safe))

# 2) Template FULL (double braces), giữ nguyên {tikz_code}
TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}

% Unicode & ngôn ngữ
\usepackage{fontspec}

% Toán & đồ hoạ
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{xcolor}
\usepackage{graphicx}

% Hệ sinh thái TikZ/PGF
\usepackage{tikz}
\usepackage{tikz-3dplot}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\usepackage{tkz-euclide}
\usepackage{tkz-tab}

% Thư viện TikZ mặc định
\usetikzlibrary{calc}
\usetikzlibrary{math}
\usetikzlibrary{positioning}
\usetikzlibrary{arrows.meta}
\usetikzlibrary{intersections}
\usetikzlibrary{angles}
\usetikzlibrary{quotes}
\usetikzlibrary{decorations.markings}
\usetikzlibrary{decorations.pathreplacing}
\usetikzlibrary{decorations.text}
\usetikzlibrary{patterns}
\usetikzlibrary{patterns.meta}
\usetikzlibrary{shadings}
\usetikzlibrary{hobby}
\usetikzlibrary{spy}
\usetikzlibrary{backgrounds}

% Thư viện pgfplots mặc định
\usepgfplotslibrary{polar}

% ==== EXTRA AUTO-INJECT START ====
% (Sẽ được chèn thêm ở đây)
% ==== EXTRA AUTO-INJECT END ====

\begin{document}
{tikz_code}
\end{document}
"""

# 3) Hàm tạo nguồn LaTeX, chèn động \usepackage / \usetikzlibrary / \usepgfplotslibrary
def generate_latex_source(
    tikz_code: str,
    extra_packages: Iterable[str] = (),
    extra_tikz_libs: Iterable[str] = (),
    extra_pgfplots_libs: Iterable[str] = (),
    base_template: str = TEX_TEMPLATE,
) -> str:
    # Loại bỏ các dòng %!<...> khỏi TikZ code trước khi chèn vào template
    import re
    cleaned_tikz_code = "\n".join([
        line for line in tikz_code.split('\n') 
        if not re.match(r'^%!<.*>$', line.strip())
    ])
    
    pkg_lines   = _lines_for_usepackage(extra_packages)
    tikz_lines  = _lines_for_tikz_libs(extra_tikz_libs)
    pgfl_lines  = _lines_for_pgfplots_libs(extra_pgfplots_libs)

    inject = "\n".join([s for s in (pkg_lines, tikz_lines, pgfl_lines) if s])
    if inject:
        full = base_template.replace(
            "% (Sẽ được chèn thêm ở đây)",
            "% (Sẽ được chèn thêm ở đây)\n" + inject
        )
    else:
        full = base_template
    return full.replace("{tikz_code}", cleaned_tikz_code)

# 4) Hàm helper để tự động phát hiện packages cần thiết từ TikZ code
def detect_required_packages(tikz_code: str) -> tuple[list[str], list[str], list[str]]:
    """
    Tự động phát hiện packages, tikz libraries và pgfplots libraries cần thiết từ code TikZ
    Hỗ trợ cú pháp thủ công: %!<...> để chỉ định packages
    Returns: (packages, tikz_libs, pgfplots_libs)
    """
    code_lower = tikz_code.lower()
    
    # Phát hiện packages từ cú pháp thủ công %!<...>
    manual_packages = []
    manual_tikz_libs = []
    manual_pgfplots_libs = []
    
    # Tìm tất cả các dòng bắt đầu bằng %!<
    import re
    manual_pattern = r'^%!<(.*?)>'
    for line in tikz_code.split('\n'):
        match = re.match(manual_pattern, line.strip())
        if match:
            manual_content = match.group(1)
            # Phân tích nội dung trong %!<...>
            for item in manual_content.split(','):
                item = item.strip()
                if item.startswith('\\usepackage{'):
                    # Trích xuất tên package
                    pkg_match = re.search(r'\\usepackage\{([^}]+)\}', item)
                    if pkg_match:
                        pkg_name = pkg_match.group(1).strip()
                        manual_packages.append(pkg_name)
                elif item.startswith('\\usetikzlibrary{'):
                    # Trích xuất tên tikz library
                    lib_match = re.search(r'\\usetikzlibrary\{([^}]+)\}', item)
                    if lib_match:
                        lib_name = lib_match.group(1).strip()
                        manual_tikz_libs.append(lib_name)
                elif item.startswith('\\usepgfplotslibrary{'):
                    # Trích xuất tên pgfplots library
                    lib_match = re.search(r'\\usepgfplotslibrary\{([^}]+)\}', item)
                    if lib_match:
                        lib_name = lib_match.group(1).strip()
                        manual_pgfplots_libs.append(lib_name)
    
    # Phát hiện packages tự động
    packages = []
    
    # siunitx - cho đơn vị đo lường
    if any(cmd in tikz_code for cmd in ["\\si{", "\\SI{", "\\num{", "\\ang{", "\\unit{"]):
        packages.append("siunitx")
    
    # circuitikz - cho mạch điện
    if any(cmd in tikz_code for cmd in ["\\ohm", "\\volt", "\\ampere", "\\resistor", "\\capacitor", "\\inductor", "\\battery", "\\lamp"]):
        packages.append("circuitikz")
    
    # tikz-timing - cho timing diagrams
    if any(cmd in tikz_code for cmd in ["\\timing", "\\timingD{", "\\timingL{", "\\timingH{", "\\timingX{"]):
        packages.append("tikz-timing")
    
    # physics - cho ký hiệu vật lý
    if any(cmd in tikz_code for cmd in ["\\vec{", "\\abs{", "\\norm{", "\\order{", "\\qty{", "\\mrm{"]):
        packages.append("physics")
    
    # mathtools - cho toán học nâng cao
    if any(cmd in tikz_code for cmd in ["\\DeclarePairedDelimiter", "\\DeclareMathOperator", "\\mathclap", "\\mathllap", "\\mathrlap"]):
        packages.append("mathtools")
    
    # tikz-cd - cho commutative diagrams
    if any(cmd in tikz_code for cmd in ["\\begin{tikzcd}", "\\arrow[", "\\arrow{r}", "\\arrow{d}"]):
        packages.append("tikz-cd")
    
    # tikz-network - cho network diagrams
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[network]", "\\Vertex[", "\\Edge[", "\\tikzstyle{VertexStyle}"]):
        packages.append("tikz-network")
    
    # tikzpeople - cho people diagrams
    if any(cmd in tikz_code for cmd in ["\\person[", "\\tikzstyle{PersonStyle}", "\\begin{tikzpicture}[person"]):
        packages.append("tikzpeople")
    
    # tikzmark - cho annotations
    if any(cmd in tikz_code for cmd in ["\\tikzmark{", "\\tikzmarkin{", "\\tikzmarkend{"]):
        packages.append("tikzmark")
    
    # pgfornament - cho ornaments
    if any(cmd in tikz_code for cmd in ["\\pgfornament{", "\\pgfornament[", "\\pgfornament["]):
        packages.append("pgfornament")
    
    # Phát hiện tikz libraries
    tikz_libs = []
    
    # decorations
    if any(cmd in tikz_code for cmd in ["\\draw[decorate", "\\draw[decoration", "\\decorate", "\\decoration{"]):
        tikz_libs.extend(["decorations.markings", "decorations.pathreplacing"])
    
    # patterns
    if any(cmd in tikz_code for cmd in ["\\draw[pattern", "\\pattern", "\\fill[pattern"]):
        tikz_libs.append("patterns")
    
    # shadings
    if any(cmd in tikz_code for cmd in ["\\draw[shade", "\\shade", "\\shadedraw", "\\shading"]):
        tikz_libs.append("shadings")
    
    # hobby curves
    if any(cmd in tikz_code for cmd in ["\\draw[hobby", "\\hobby", "\\curve{"]):
        tikz_libs.append("hobby")
    
    # spy (magnifying glass)
    if "\\spy" in tikz_code:
        tikz_libs.append("spy")
    
    # backgrounds
    if any(cmd in tikz_code for cmd in ["\\begin{scope}[on background layer]", "\\begin{background}", "\\background"]):
        tikz_libs.append("backgrounds")
    
    # intersections
    if any(cmd in tikz_code for cmd in ["\\path[name intersections", "\\coordinate[name intersections", "\\draw[name intersections"]):
        tikz_libs.append("intersections")
    
    # angles
    if any(cmd in tikz_code for cmd in ["\\pic[angle", "\\angle", "\\draw pic[angle"]):
        tikz_libs.append("angles")
    
    # quotes
    if any(cmd in tikz_code for cmd in ["\\draw[quotes", "\\quotes", "\\draw[quotes="]):
        tikz_libs.append("quotes")
    
    # positioning
    if any(cmd in tikz_code for cmd in ["\\node[above", "\\node[below", "\\node[left", "\\node[right", "\\node[above left", "\\node[above right", "\\node[below left", "\\node[below right"]):
        tikz_libs.append("positioning")
    
    # arrows.meta
    if any(cmd in tikz_code for cmd in ["\\draw[-{", "\\draw[->{", "\\draw[<->{", "\\draw[arrows="]):
        tikz_libs.append("arrows.meta")
    
    # shapes.geometric
    if any(cmd in tikz_code for cmd in ["\\draw[regular polygon", "\\draw[star", "\\draw[diamond", "\\draw[ellipse", "\\draw[circle"]):
        tikz_libs.append("shapes.geometric")
    
    # shapes.symbols
    if any(cmd in tikz_code for cmd in ["\\draw[signal", "\\draw[tape", "\\draw[magnifying glass", "\\draw[cloud"]):
        tikz_libs.append("shapes.symbols")
    
    # shapes.arrows
    if any(cmd in tikz_code for cmd in ["\\draw[arrow box", "\\draw[strike out", "\\draw[rounded rectangle"]):
        tikz_libs.append("shapes.arrows")
    
    # fit
    if any(cmd in tikz_code for cmd in ["\\node[fit=", "\\fit{", "\\draw[fit="]):
        tikz_libs.append("fit")
    
    # matrix
    if any(cmd in tikz_code for cmd in ["\\matrix[", "\\matrix of", "\\matrix (", "\\matrix{"]):
        tikz_libs.append("matrix")
    
    # chains
    if any(cmd in tikz_code for cmd in ["\\begin{scope}[start chain", "\\chainin", "\\chainin (", "\\onchain"]):
        tikz_libs.append("chains")
    
    # automata
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[automaton", "\\node[state", "\\path[->] node[state"]):
        tikz_libs.append("automata")
    
    # petri
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[petri", "\\place[", "\\transition[", "\\arc["]):
        tikz_libs.append("petri")
    
    # mindmap
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[mindmap", "\\concept[", "\\concept color="]):
        tikz_libs.append("mindmap")
    
    # trees
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[tree", "\\node[level", "\\child[", "\\child {"]):
        tikz_libs.append("trees")
    
    # graphs
    if any(cmd in tikz_code for cmd in ["\\begin{tikzpicture}[graph", "\\graph[", "\\graph {", "\\graph ("]):
        tikz_libs.append("graphs")
    
    # shadows
    if any(cmd in tikz_code for cmd in ["\\draw[shadow", "\\shadow", "\\shadow{", "\\draw[drop shadow"]):
        tikz_libs.append("shadows")
    
    # fadings
    if any(cmd in tikz_code for cmd in ["\\begin{tikzfadingfrompicture", "\\tikzfading", "\\path[fading="]):
        tikz_libs.append("fadings")
    
    # Phát hiện pgfplots libraries
    pgfplots_libs = []
    
    # fillbetween
    if any(cmd in tikz_code for cmd in ["\\addplot[fill between", "\\addplot[fillbetween", "\\fillbetween"]):
        pgfplots_libs.append("fillbetween")
    
    # statistics
    if any(cmd in tikz_code for cmd in ["\\addplot[statistics", "\\addplot[hist", "\\addplot[boxplot", "\\addplot[error bars"]):
        pgfplots_libs.append("statistics")
    
    # dateplot
    if any(cmd in tikz_code for cmd in ["\\addplot[date coordinates", "\\addplot[dateplot", "\\dateplot"]):
        pgfplots_libs.append("dateplot")
    
    # colorbrewer
    if any(cmd in tikz_code for cmd in ["\\addplot[colorbrewer", "\\colormap[colorbrewer", "\\pgfplotsset{colormap name="]):
        pgfplots_libs.append("colorbrewer")
    
    # groupplots
    if any(cmd in tikz_code for cmd in ["\\begin{groupplot}", "\\nextgroupplot", "\\groupplot[", "\\pgfplotsset{groupplot"]):
        pgfplots_libs.append("groupplots")
    
    # ternary
    if any(cmd in tikz_code for cmd in ["\\begin{ternaryaxis}", "\\ternaryaxis[", "\\addplot3[ternary", "\\ternaryaxis"]):
        pgfplots_libs.append("ternary")
    
    # smithchart
    if any(cmd in tikz_code for cmd in ["\\begin{smithchart}", "\\smithchart[", "\\addplot[smithchart", "\\smithchart"]):
        pgfplots_libs.append("smithchart")
    
    # units
    if any(cmd in tikz_code for cmd in ["\\begin{axis}[x unit=", "\\begin{axis}[y unit=", "\\addplot[unit="]):
        pgfplots_libs.append("units")
    
    # Kết hợp packages tự động và thủ công
    all_packages = list(dict.fromkeys(packages + manual_packages))  # Loại bỏ trùng lặp
    all_tikz_libs = list(dict.fromkeys(tikz_libs + manual_tikz_libs))  # Loại bỏ trùng lặp
    all_pgfplots_libs = list(dict.fromkeys(pgfplots_libs + manual_pgfplots_libs))  # Loại bỏ trùng lặp
    
    return all_packages, all_tikz_libs, all_pgfplots_libs

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
    current_user_id = current_user.id if current_user and current_user.is_authenticated else None
    
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
                
            try:
                url = url_for('static', filename=row['filename'])
            except:
                url = f"/static/{row['filename']}"
                
            svg_files.append({
                'id': row['id'],
                'filename': row['filename'],
                'display_name': f"Người tạo: {row['username']}" if row.get('username') else row['filename'],
                'url': url,
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

def get_svg_files_with_likes(user_id=None):
    """Lấy files với thông tin like cho user đã đăng nhập - Format thống nhất với search_results"""
    svg_files = []
    current_user_id = user_id or (current_user.id if current_user and current_user.is_authenticated else None)
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query tương tự như search_results nhưng cho tất cả files
        cursor.execute("""
            SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 100
        """, (current_user_id or 0,))
        
        rows = cursor.fetchall()
        
        # Format results giống như search_results
        for row in rows:
            row['url'] = f"/static/{row['filename']}"
            row['created_time_vn'] = row['created_at'].strftime('%d/%m/%Y %H:%M') if row['created_at'] else ''
            row['is_liked_by_current_user'] = bool(row['is_liked_by_current_user'])
            svg_files.append(row)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] get_svg_files_with_likes(): {e}", flush=True)
    
    return svg_files

def get_public_svg_files():
    """Lấy public files cho user chưa đăng nhập - Format thống nhất với search_results"""
    svg_files = []
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Query cho public files (không có like info)
        cursor.execute("""
            SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                   0 as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        
        # Format results giống như search_results
        for row in rows:
            row['url'] = f"/static/{row['filename']}"
            row['created_time_vn'] = row['created_at'].strftime('%d/%m/%Y %H:%M') if row['created_at'] else ''
            row['is_liked_by_current_user'] = False  # User chưa đăng nhập
            svg_files.append(row)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] get_public_svg_files(): {e}", flush=True)
    
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
                    
                    # ✅ Gửi email welcome cho user mới
                    try:
                        email_service = get_email_service()
                        if email_service:
                            success = email_service.send_welcome_email(session["user_email"], default_username)
                            if success:
                                print(f"DEBUG: Welcome email sent successfully to {session['user_email']}", flush=True)
                            else:
                                print(f"DEBUG: Failed to send welcome email to {session['user_email']}", flush=True)
                        else:
                            print(f"DEBUG: Email service not available for welcome email to {session['user_email']}", flush=True)
                    except Exception as email_error:
                        print(f"ERROR sending welcome email: {email_error}", flush=True)
                    
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

# Test route for base template
@app.route("/test-base-template")
def test_base_template():
    """Route để test base template với example_using_base.html"""
    logged_in = current_user.is_authenticated
    user_email = current_user.email if logged_in else None
    
    # Tạo app_state giống như trang chủ
    app_state = {
        'loggedIn': logged_in,
        'userEmail': user_email
    }
    
    return render_template('example_using_base.html', 
                         app_state=app_state,
                         logged_in=logged_in,
                         current_user_email=user_email)

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
            
            # Tự động phát hiện packages cần thiết từ TikZ code
            extra_packages, extra_tikz_libs, extra_pgfplots_libs = detect_required_packages(tikz_code)
            
            # Tạo nguồn LaTeX với packages được phát hiện tự động
            try:
                latex_source = generate_latex_source(
                    tikz_code=tikz_code,
                    extra_packages=extra_packages,
                    extra_tikz_libs=extra_tikz_libs,
                    extra_pgfplots_libs=extra_pgfplots_libs
                )
            except ValueError as e:
                # Nếu có package không được phép, chỉ sử dụng template cơ bản
                print(f"[WARN] Package không được phép: {e}", flush=True)
                latex_source = TEX_TEMPLATE.replace("{tikz_code}", tikz_code)
            
            # Ghi file TeX
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_source)
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
                        
    # Lấy danh sách các file SVG đã tạo với format thống nhất
    if logged_in:
        # Private files cho user đã đăng nhập
        svg_files = get_svg_files_with_likes()
    else:
        # Public files cho user chưa đăng nhập
        svg_files = get_public_svg_files()
    
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
    
    # ✅ Sửa đổi: Lấy google_id từ database thay vì session
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT google_id FROM user WHERE id = %s", (current_user.id,))
        row = cursor.fetchone()
        google_id = row[0] if row and row[0] else "anonymous"
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ ERROR getting google_id from DB: {e}", flush=True)
        # Fallback to session if DB query fails
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
        # Khi query rỗng, trả về tất cả keywords (giới hạn 20 từ)
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM keyword ORDER BY word LIMIT 20")
            results = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return jsonify(results)
        except Exception as e:
            print(f"[ERROR] /api/keywords/search (empty query): {e}", flush=True)
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

@app.route('/search')
def search_results():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('index'))
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Search for SVG files that match the keyword
        cursor.execute("""
            SELECT DISTINCT s.*, u.username as creator_username, u.id as creator_id,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id) as like_count,
                   (SELECT COUNT(*) FROM svg_like WHERE svg_image_id = s.id AND user_id = %s) as is_liked_by_current_user
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            JOIN svg_image_keyword sik ON s.id = sik.svg_image_id
            JOIN keyword k ON sik.keyword_id = k.id
            WHERE k.word LIKE %s COLLATE utf8mb4_general_ci
            ORDER BY s.created_at DESC
        """, (get_user_id_from_session() or 0, f"%{query}%"))
        
        search_results = cursor.fetchall()
        
        # Format the results
        for result in search_results:
            result['url'] = f"/static/{result['filename']}"
            result['created_time_vn'] = result['created_at'].strftime('%d/%m/%Y %H:%M') if result['created_at'] else ''
            result['is_liked_by_current_user'] = bool(result['is_liked_by_current_user'])
        
        cursor.close()
        conn.close()
        
        return render_template('search_results.html', 
                             search_query=query,
                             search_results=search_results,
                             results_count=len(search_results),
                             logged_in=current_user.is_authenticated,
                             user_email=current_user.email if current_user.is_authenticated else None,
                             username=current_user.username if current_user.is_authenticated else None,
                             avatar=current_user.avatar if current_user.is_authenticated else None)
        
    except Exception as e:
        print(f"[ERROR] /search: {e}", flush=True)
        return render_template('search_results.html', 
                             search_query=query,
                             search_results=[],
                             results_count=0,
                             logged_in=current_user.is_authenticated,
                             user_email=current_user.email if current_user.is_authenticated else None,
                             username=current_user.username if current_user.is_authenticated else None,
                             avatar=current_user.avatar if current_user.is_authenticated else None)

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

@app.route('/api/public/files')
def api_public_files():
    """API để lấy danh sách SVG files công khai (không cần đăng nhập)"""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'hiep1987'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'tikz2svg')
        )
        cursor = conn.cursor(dictionary=True)
        
        # Lấy tất cả files đã lưu (công khai)
        cursor.execute("""
            SELECT 
                s.id, 
                s.filename, 
                s.tikz_code, 
                s.created_at,
                u.id as creator_id,
                u.username as creator_username,
                COUNT(sl.id) as like_count
            FROM svg_image s
            JOIN user u ON s.user_id = u.id
            LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
            GROUP BY s.id, s.filename, s.tikz_code, s.created_at, u.id, u.username
            ORDER BY s.created_at DESC
            LIMIT 50
        """)
        
        files = []
        for row in cursor.fetchall():
            try:
                static_dir = app.config['UPLOAD_FOLDER']
                filepath = os.path.join(static_dir, row['filename'])
                if os.path.exists(filepath):
                    file_size_kb = round(os.path.getsize(filepath) / 1024, 2)
                else:
                    file_size_kb = None
            except Exception:
                file_size_kb = None
                
            try:
                url = url_for('static', filename=row['filename'])
            except:
                url = f"/static/{row['filename']}"
                
            files.append({
                'id': row['id'],
                'filename': row['filename'],
                'tikz_code': row['tikz_code'],
                'url': url,
                'display_name': f"Người tạo: {row['creator_username']}" if row.get('creator_username') else row['filename'],
                'size': file_size_kb,
                'created_time': format_time_vn(row['created_at']),
                'creator_id': row['creator_id'],
                'creator_username': row['creator_username'],
                'like_count': row['like_count'] or 0,
                'is_liked_by_current_user': False  # Mặc định là False cho người chưa đăng nhập
            })
        
        cursor.close()
        conn.close()
        return jsonify({'files': files})
        
    except Exception as e:
        print(f"Error in api_public_files: {e}", flush=True)
        return jsonify({'files': []}), 500

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

        # Add file size and actual image dimensions similar to /convert endpoint
        file_size = os.path.getsize(out_path) if os.path.exists(out_path) else None
        actual_size = None
        if os.path.exists(out_path):
            try:
                with Image.open(out_path) as im:
                    actual_size = f"{im.size[0]}x{im.size[1]} pixels"
            except Exception:
                actual_size = None

        return jsonify({'url': url, 'file_size': file_size, 'actual_size': actual_size})
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

        # Redirect đến trang profile SVG files (trang chính)
        return redirect(url_for('profile_svg_files', user_id=user_id))
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
            # Kiểm tra xem có phải là hủy bỏ xác thực không
            if request.form.get("cancel_verification"):
                # Xóa thông tin xác thực
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = NULL,
                        profile_verification_expires_at = NULL,
                        pending_profile_changes = NULL,
                        profile_verification_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
                flash("Đã hủy bỏ thay đổi đang chờ xác thực.", "info")
                return redirect(url_for('profile_settings', user_id=user_id))
            
            # Kiểm tra xem có phải là xác thực không
            verification_code = request.form.get("verification_code", "").strip()
            
            if verification_code:
                # Xử lý xác thực
                return handle_profile_verification(user_id, verification_code, cursor, conn)
            
            # Xử lý thay đổi profile
            new_username = request.form.get("username", "").strip()
            new_bio = request.form.get("bio", "").strip()
            avatar_file = request.files.get('avatar')
            avatar_cropped_data = request.form.get('avatar_cropped')

            # Lấy thông tin hiện tại để so sánh
            cursor.execute("SELECT username, bio, avatar, email FROM user WHERE id = %s", (user_id,))
            current_data = cursor.fetchone()
            
            # Tạo tóm tắt thay đổi
            new_data = {
                'username': new_username,
                'bio': new_bio,
                'avatar': current_data['avatar']  # Giữ nguyên avatar cũ cho đến khi xác thực
            }
            
            # Kiểm tra thay đổi avatar
            has_avatar_change = bool(avatar_cropped_data and avatar_cropped_data.startswith('data:image'))
            print(f"🔍 DEBUG: has_avatar_change = {has_avatar_change}", flush=True)
            print(f"🔍 DEBUG: avatar_cropped_data exists = {bool(avatar_cropped_data)}", flush=True)
            if avatar_cropped_data:
                print(f"🔍 DEBUG: avatar_cropped_data starts with data:image = {avatar_cropped_data.startswith('data:image')}", flush=True)
            
            changes_summary = get_profile_changes_summary(current_data, new_data, has_avatar_change)
            print(f"🔍 DEBUG: changes_summary = {changes_summary}", flush=True)
            
            # Nếu có thay đổi, gửi email xác thực
            if changes_summary:
                # Tạo mã xác thực
                verification_code = generate_verification_code(6)
                expires_at = datetime.now() + timedelta(hours=24)
                
                # Lưu thay đổi tạm thời và mã xác thực
                pending_changes = {
                    'username': new_username,
                    'bio': new_bio,
                    'avatar_file': None,
                    'avatar_cropped_data': avatar_cropped_data
                }
                
                cursor.execute("""
                    UPDATE user SET 
                        profile_verification_code = %s,
                        profile_verification_expires_at = %s,
                        pending_profile_changes = %s,
                        profile_verification_attempts = 0
                    WHERE id = %s
                """, (verification_code, expires_at, json.dumps(pending_changes), user_id))
                
                conn.commit()
                
                # Gửi email xác thực
                email_service = get_email_service()
                print(f"🔍 DEBUG: Email service = {email_service}", flush=True)
                
                if email_service:
                    print(f"🔍 DEBUG: Sending email to {current_data['email']} with code {verification_code}", flush=True)
                    try:
                        result = email_service.send_profile_settings_verification_email(
                            email=current_data['email'],
                            username=current_data['username'] or 'Người dùng',
                            verification_code=verification_code,
                            changes_summary=changes_summary,
                            user_id=user_id
                        )
                        print(f"🔍 DEBUG: Email send result = {result}", flush=True)
                    except Exception as e:
                        print(f"❌ DEBUG: Email send error = {e}", flush=True)
                        import traceback
                        print(f"❌ DEBUG: Email error traceback = {traceback.format_exc()}", flush=True)
                else:
                    print(f"❌ DEBUG: Email service is None!", flush=True)
                
                flash("Đã gửi mã xác thực đến email của bạn. Vui lòng kiểm tra email và nhập mã để hoàn tất thay đổi.", "success")
                return redirect(url_for('profile_settings', user_id=user_id))
            else:
                flash("Không có thay đổi nào được thực hiện.", "info")
                return redirect(url_for('profile_settings', user_id=user_id))
            
            # Avatar sẽ được xử lý trong hàm xác thực

        cursor.execute("""
            SELECT id, username, avatar, bio, email, 
                   profile_verification_code, profile_verification_expires_at,
                   pending_profile_changes, profile_verification_attempts,
                   identity_verified
            FROM user WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            return "User not found", 404

        # Kiểm tra xem có thay đổi đang chờ xác thực không
        has_pending_verification = (
            user['profile_verification_code'] is not None and 
            user['profile_verification_expires_at'] is not None and
            datetime.now() < user['profile_verification_expires_at']
        )

        return render_template("profile_settings.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            email_verified=True,
            identity_verified=user.get('identity_verified', False),
            is_owner=is_owner,
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None,
            has_pending_verification=has_pending_verification,
            verification_attempts=user.get('profile_verification_attempts', 0)
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

        # Fetch followed posts data for server-side rendering
        followed_posts = []
        if is_owner:  # Only fetch for owner
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
            
            for row in cursor.fetchall():
                followed_posts.append({
                    'id': row['id'],
                    'filename': row['filename'],
                    'tikz_code': row['tikz_code'],
                    'url': url_for('static', filename=row['filename']),
                    'creator_id': row['creator_id'],
                    'creator_username': row['creator_username'],
                    'created_time_vn': format_time_vn(row['created_at']) if 'format_time_vn' in globals() else str(row['created_at']),
                    'created_time': str(row['created_at']),
                    'like_count': row['like_count'] or 0,
                    'is_liked_by_current_user': bool(row['is_liked_by_current_user'])
                })

        cursor.close()
        conn.close()
        
        return render_template("profile_followed_posts.html",
            username=user["username"],
            avatar=user["avatar"],
            bio=user["bio"],
            user_email=user["email"],
            user_id=user_id,
            is_owner=is_owner,
            followed_posts=followed_posts,
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
            'current_avatar': current_user.avatar,
            'current_identity_verified': getattr(current_user, 'identity_verified', False)
        }
    return {
        'current_user_email': None,
        'current_username': None,
        'current_avatar': None,
        'current_identity_verified': False
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

@app.route('/api/check_login_status')
def api_check_login_status():
    """API để kiểm tra trạng thái đăng nhập hiện tại"""
    return jsonify({
        'logged_in': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None
    })

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

@app.route('/compile_with_packages', methods=['POST'])
@login_required
def compile_with_packages():
    """API endpoint để biên dịch TikZ với packages tùy chỉnh"""
    data = request.json
    tikz_code = data.get('tikz_code', '').strip()
    extra_packages = data.get('extra_packages', [])
    extra_tikz_libs = data.get('extra_tikz_libs', [])
    extra_pgfplots_libs = data.get('extra_pgfplots_libs', [])
    
    if not tikz_code:
        return jsonify({"error": "Vui lòng nhập code TikZ!"}), 400
    
    tikz_code = clean_control_chars(tikz_code)
    
    try:
        # Tạo workspace tạm
        now = datetime.now(tz_vn)
        file_id = str(uuid.uuid4())
        work_dir = f"/tmp/{file_id}"
        os.makedirs(work_dir, exist_ok=True)
        tex_path = os.path.join(work_dir, "tikz.tex")
        pdf_path = os.path.join(work_dir, "tikz.pdf")
        svg_path_tmp = os.path.join(work_dir, "tikz.svg")
        
        # Tạo nguồn LaTeX với packages tùy chỉnh
        try:
            latex_source = generate_latex_source(
                tikz_code=tikz_code,
                extra_packages=extra_packages,
                extra_tikz_libs=extra_tikz_libs,
                extra_pgfplots_libs=extra_pgfplots_libs
            )
        except ValueError as e:
            return jsonify({"error": f"Package không hợp lệ: {str(e)}"}), 400
        
        # Ghi file TeX
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)
        
        # Biên dịch
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
        
        # Đọc SVG content
        with open(svg_path_tmp, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        return jsonify({
            "success": True,
            "file_id": file_id,
            "svg_url": f"/temp_svg/{file_id}",
            "svg_content": svg_content
        })
        
    except subprocess.CalledProcessError as ex:
        # Xử lý lỗi biên dịch
        log_path = os.path.join(work_dir, "tikz.log")
        error_details = []
        
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as log_file:
                    for line in log_file:
                        if line.startswith("!") or 'error' in line.lower():
                            error_details.append(line.strip())
            except Exception:
                pass
        
        return jsonify({
            "error": "Lỗi khi biên dịch TikZ",
            "details": error_details,
            "stderr": ex.stderr if hasattr(ex, 'stderr') else None
        }), 400
        
    except Exception as e:
        return jsonify({"error": f"Lỗi không xác định: {str(e)}"}), 500

@app.route('/api/available_packages')
def api_available_packages():
    """API endpoint để lấy danh sách packages có sẵn"""
    return jsonify({
        "packages": list(SAFE_PACKAGES),
        "tikz_libraries": list(SAFE_TIKZ_LIBS),
        "pgfplots_libraries": list(SAFE_PGFPLOTS_LIBS)
    })

# ✅ EMAIL SYSTEM ROUTES
def create_hosted_logo():
    """Tạo logo PNG được host trên server"""
    try:
        # Kiểm tra xem logo đã tồn tại chưa
        logo_path = os.path.join(STATIC_ROOT, 'images', 'email_logo.png')
        if os.path.exists(logo_path):
            print(f"✅ Logo đã tồn tại: {logo_path}")
            return True
        
        # Đọc SVG
        svg_path = os.path.join(STATIC_ROOT, 'logo.svg')
        if not os.path.exists(svg_path):
            print(f"❌ Không tìm thấy file SVG: {svg_path}")
            return False
            
        with open(svg_path, 'r') as f:
            svg_content = f.read()
        
        # Chuyển đổi SVG thành PNG với kích thước lớn hơn
        png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=120, output_height=120)
        
        # Lưu PNG vào static/images
        with open(logo_path, 'wb') as f:
            f.write(png_data)
        
        print(f"✅ Logo PNG created: {len(png_data)} bytes -> {logo_path}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo logo: {e}")
        return False

def send_email(to_email, subject, html_content):
    """Gửi email"""
    try:
        smtp_server = os.getenv('ZOHO_SMTP_SERVER', 'smtp.zoho.com')
        smtp_port = int(os.getenv('ZOHO_SMTP_PORT', '587'))
        email = os.getenv('ZOHO_EMAIL', 'support@tikz2svg.com')
        password = os.getenv('ZOHO_APP_PASSWORD')
        
        if not password:
            return False, "Thiếu ZOHO_APP_PASSWORD trong .env"
        
        # Đảm bảo encoding đúng cho subject và content
        try:
            # Encode subject nếu cần
            if isinstance(subject, str):
                subject = subject.encode('utf-8').decode('utf-8')
            
            # Encode HTML content nếu cần
            if isinstance(html_content, str):
                html_content = html_content.encode('utf-8').decode('utf-8')
        except UnicodeError as ue:
            print(f"Unicode encoding error: {ue}", flush=True)
            # Fallback: encode as utf-8
            subject = subject.encode('utf-8', errors='ignore').decode('utf-8')
            html_content = html_content.encode('utf-8', errors='ignore').decode('utf-8')
        
        msg = MIMEMultipart('alternative')
        
        # Encode subject an toàn
        try:
            msg['Subject'] = subject
        except UnicodeEncodeError:
            safe_subject = subject.encode('utf-8', errors='ignore').decode('utf-8')
            msg['Subject'] = safe_subject
        
        msg['From'] = email
        msg['To'] = to_email
        
        # Sử dụng encoding rõ ràng và đảm bảo content an toàn
        try:
            html_part = MIMEText(html_content, 'html', 'utf-8')
        except UnicodeEncodeError:
            # Fallback: encode content trước khi tạo MIMEText
            safe_html_content = html_content.encode('utf-8', errors='ignore').decode('utf-8')
            html_part = MIMEText(safe_html_content, 'html', 'utf-8')
        
        msg.attach(html_part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email, password)
        
        # Encode message string với UTF-8
        message_string = msg.as_string()
        try:
            # Thử encode với UTF-8
            message_bytes = message_string.encode('utf-8')
            server.sendmail(email, to_email, message_bytes)
        except UnicodeEncodeError:
            # Fallback: encode với ascii và ignore errors
            message_bytes = message_string.encode('ascii', errors='ignore')
            server.sendmail(email, to_email, message_bytes)
        server.quit()
        
        return True, "Email đã được gửi thành công!"
    except Exception as e:
        print(f"Email send error: {e}", flush=True)
        import traceback
        print(f"Email error traceback: {traceback.format_exc()}", flush=True)
        return False, f"Lỗi: {str(e)}"

@app.route('/static/images/<path:filename>')
def serve_logo(filename):
    """Serve logo files"""
    return send_from_directory(os.path.join(STATIC_ROOT, 'images'), filename)

@app.route('/email-test')
@login_required
def email_test_page():
    """Trang test email cho admin với xác thực mã"""
    # Kiểm tra mã xác thực từ session
    if not session.get('email_test_verified'):
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Xác thực - Test Email System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
                input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; text-align: center; letter-spacing: 2px; }
                button { background: #e74c3c; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
                button:hover { background: #c0392b; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin-bottom: 20px; display: none; }
                .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Xác thực Truy cập</h1>
                    <p>Nhập mã xác thực để truy cập Email Test System</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Cảnh báo:</strong> Đây là trang quản trị nội bộ. Chỉ admin mới được phép truy cập.
                </div>
                
                <div class="error" id="error">
                    <strong>❌ Mã xác thực không đúng!</strong>
                </div>
                
                <form id="authForm">
                    <div class="form-group">
                        <label for="authCode">Mã xác thực:</label>
                        <input type="text" id="authCode" name="authCode" required placeholder="Nhập mã 6 chữ số" maxlength="6" pattern="[0-9]{6}">
                    </div>
                    
                    <button type="submit">🔓 Xác thực & Truy cập</button>
                </form>
            </div>
            
            <script>
                document.getElementById('authForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const authCode = document.getElementById('authCode').value;
                    const error = document.getElementById('error');
                    
                    if (authCode === '964454') {
                        // Gửi request để set session
                        try {
                            const response = await fetch('/api/verify-email-test', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ authCode: authCode })
                            });
                            
                            if (response.ok) {
                                window.location.reload();
                            } else {
                                error.style.display = 'block';
                            }
                        } catch (error) {
                            error.style.display = 'block';
                        }
                    } else {
                        error.style.display = 'block';
                        document.getElementById('authCode').value = '';
                        document.getElementById('authCode').focus();
                    }
                });
                
                // Auto-focus vào input
                document.getElementById('authCode').focus();
            </script>
        </body>
        </html>
        ''')
    
    # Nếu đã xác thực, hiển thị trang email test
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Email System - TikZ2SVG</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
            input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
            button { background: #0984e3; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #74b9ff; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .loading { display: none; text-align: center; color: #666; }
            .logo-preview { text-align: center; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .logo-preview img { width: 60px; height: 60px; border-radius: 8px; }
            .logout-btn { background: #e74c3c; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; float: right; }
            .logout-btn:hover { background: #c0392b; }
            .status-bar { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <button class="logout-btn" onclick="logout()">🚪 Thoát</button>
                <h1>📧 Test Email System</h1>
                <p>Gửi email test với logo TikZ2SVG (hosted trên server)</p>
            </div>
            
            <div class="status-bar">
                <strong>✅ Đã xác thực:</strong> Bạn đã nhập đúng mã xác thực và được phép truy cập.
            </div>
            
            <div class="logo-preview">
                <h3>🎨 Logo Preview (Production):</h3>
                <img src="https://tikz2svg.mathlib.io.vn/static/images/email_logo.png" alt="TikZ2SVG Logo" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" style="width: 60px; height: 60px;">
                <p style="display:none; color: #999;">Logo sẽ được tải từ production server</p>
                <p>Logo được host trên production server: <code>https://tikz2svg.mathlib.io.vn/static/images/email_logo.png</code></p>
            </div>
            
            <form id="emailForm">
                <div class="form-group">
                    <label for="email">Email nhận:</label>
                    <input type="email" id="email" name="email" required placeholder="your@email.com">
                </div>
                
                <div class="form-group">
                    <label for="template">Loại email:</label>
                    <select id="template" name="template">
                        <option value="welcome">Welcome Email</option>
                        <option value="verification">Verification Email</option>
                        <option value="svg_verification">SVG Verification Email</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="username">Tên người dùng:</label>
                    <input type="text" id="username" name="username" placeholder="Tên người dùng">
                </div>
                
                <button type="submit">🚀 Gửi Email Test</button>
            </form>
            
            <div class="loading" id="loading">
                <p>⏳ Đang gửi email...</p>
            </div>
            
            <div class="result" id="result" style="display: none;"></div>
        </div>
        
        <script>
            function logout() {
                fetch('/api/logout-email-test', { method: 'POST' })
                    .then(() => window.location.reload());
            }
            
            document.getElementById('emailForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                
                loading.style.display = 'block';
                result.style.display = 'none';
                
                const formData = new FormData(this);
                
                try {
                    const response = await fetch('/api/send-test-email', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    result.className = 'result ' + (data.success ? 'success' : 'error');
                    result.innerHTML = '<strong>' + (data.success ? '✅' : '❌') + '</strong> ' + data.message;
                    result.style.display = 'block';
                } catch (error) {
                    result.className = 'result error';
                    result.innerHTML = '<strong>❌</strong> Lỗi kết nối: ' + error.message;
                    result.style.display = 'block';
                } finally {
                    loading.style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/api/verify-email-test', methods=['POST'])
@login_required
def verify_email_test():
    """Xác thực mã để truy cập email test"""
    try:
        data = request.get_json()
        auth_code = data.get('authCode')
        
        if auth_code == '964454':
            session['email_test_verified'] = True
            return jsonify({'success': True, 'message': 'Xác thực thành công'})
        else:
            return jsonify({'success': False, 'message': 'Mã xác thực không đúng'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/logout-email-test', methods=['POST'])
@login_required
def logout_email_test():
    """Đăng xuất khỏi email test"""
    session.pop('email_test_verified', None)
    return jsonify({'success': True, 'message': 'Đã đăng xuất'})

@app.route('/api/send-test-email', methods=['POST'])
@login_required
def send_test_email_api():
    """API gửi email test - yêu cầu xác thực"""
    # Kiểm tra xác thực email test
    if not session.get('email_test_verified'):
        return jsonify({'success': False, 'message': 'Chưa xác thực truy cập email test'}), 403
    try:
        email = request.form.get('email')
        template = request.form.get('template', 'welcome')
        username = request.form.get('username', 'User')
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            if not create_hosted_logo():
                return jsonify({'success': False, 'message': 'Không thể tạo logo'})
        
        # Sử dụng email service thay vì hàm send_email cũ
        email_service = get_email_service()
        if not email_service:
            return jsonify({'success': False, 'message': 'Email service không khả dụng'})
        
        try:
            # Bypass rate limit cho email-test page
            bypass_rate_limit = True
            
            if template == 'welcome':
                success = email_service.send_email(email, 'welcome', context={'username': username, 'email': email}, bypass_rate_limit=bypass_rate_limit)
                message = "Email chào mừng đã được gửi thành công!" if success else "Không thể gửi email chào mừng"
            elif template == 'verification':
                verification_code = "123456"  # Trong thực tế sẽ tạo ngẫu nhiên
                success = email_service.send_email(email, 'account_verification', context={'username': username, 'email': email, 'verification_code': verification_code}, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực đã được gửi thành công!" if success else "Không thể gửi email xác thực"
            elif template == 'account_verification':
                verification_code = "123456"  # Trong thực tế sẽ tạo ngẫu nhiên
                success = email_service.send_email(email, 'account_verification', context={'username': username, 'email': email, 'verification_code': verification_code}, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực tài khoản đã được gửi thành công!" if success else "Không thể gửi email xác thực tài khoản"
            else:  # svg_verification
                success = email_service.send_email(email, 'svg_verification', context={
                    'username': username, 
                    'email': email, 
                    'verification_code': '123456', 
                    'svg_name': 'test.svg',
                    'svg_width': 800,
                    'svg_height': 600,
                    'svg_size': 2048,
                    'daily_limit': 10,
                    'verification_url': f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/svg/verification"
                }, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực SVG đã được gửi thành công!" if success else "Không thể gửi email xác thực SVG"
            
            return jsonify({'success': success, 'message': message})
        except Exception as e:
            print(f"Email service error: {e}", flush=True)
            return jsonify({'success': False, 'message': f'Lỗi email service: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/send-welcome-email', methods=['POST'])
def send_welcome_email_api():
    """API gửi email chào mừng cho user mới"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username', 'User')
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            create_hosted_logo()
        
        subject = f"Chào mừng bạn đến với TikZ2SVG, {username}!"
        html_content = create_welcome_email(username)
        
        success, message = send_email(email, subject, html_content)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/test-email-direct', methods=['POST'])
def test_email_direct_api():
    """API test email trực tiếp - không cần authentication"""
    try:
        data = request.json or request.form
        email = data.get('email')
        template = data.get('template', 'welcome')
        username = data.get('username', 'User')
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            if not create_hosted_logo():
                return jsonify({'success': False, 'message': 'Không thể tạo logo'})
        
        # Sử dụng email service với bypass rate limit
        email_service = get_email_service()
        if not email_service:
            return jsonify({'success': False, 'message': 'Email service không khả dụng'})
        
        try:
            # Bypass rate limit cho test
            bypass_rate_limit = True
            
            if template == 'welcome':
                success = email_service.send_email(email, 'welcome', context={'username': username, 'email': email}, bypass_rate_limit=bypass_rate_limit)
                message = "Email chào mừng đã được gửi thành công!" if success else "Không thể gửi email chào mừng"
            elif template == 'account_verification':
                verification_code = "123456"  # Test code
                success = email_service.send_email(email, 'account_verification', context={'username': username, 'email': email, 'verification_code': verification_code}, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực tài khoản đã được gửi thành công!" if success else "Không thể gửi email xác thực tài khoản"
            elif template == 'notification':
                success = email_service.send_email(email, 'notification', context={'title': 'Test Notification', 'message': f'Đây là email test cho {username}'}, bypass_rate_limit=bypass_rate_limit)
                message = "Email thông báo đã được gửi thành công!" if success else "Không thể gửi email thông báo"
            elif template == 'svg_verification':
                success = email_service.send_email(email, 'svg_verification', context={
                    'username': username, 
                    'email': email, 
                    'verification_code': '123456', 
                    'svg_name': 'test.svg',
                    'svg_width': 800,
                    'svg_height': 600,
                    'svg_size': 2048,
                    'daily_limit': 10,
                    'verification_url': f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/svg/verification"
                }, bypass_rate_limit=bypass_rate_limit)
                message = "Email xác thực SVG đã được gửi thành công!" if success else "Không thể gửi email xác thực SVG"
            else:
                return jsonify({'success': False, 'message': f'Template {template} không được hỗ trợ'})
            
            return jsonify({'success': success, 'message': message})
        except Exception as e:
            print(f"Email service error: {e}", flush=True)
            return jsonify({'success': False, 'message': f'Lỗi email service: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/send-verification-email', methods=['POST'])
def send_verification_email_api():
    """API gửi email xác thực tài khoản"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username', 'User')
        verification_code = data.get('verification_code')
        
        if not email or not verification_code:
            return jsonify({'success': False, 'message': 'Thiếu email hoặc mã xác thực'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            create_hosted_logo()
        
        subject = f"Xác thực tài khoản - TikZ2SVG"
        html_content = create_verification_email(username, verification_code)
        
        success, message = send_email(email, subject, html_content)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/send-svg-verification-email', methods=['POST'])
def send_svg_verification_email_api():
    """API gửi email xác thực khi lưu nhiều SVG"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username', 'User')
        svg_count = data.get('svg_count', 10)
        
        if not email:
            return jsonify({'success': False, 'message': 'Thiếu email'})
        
        # Tạo logo nếu chưa có
        if not os.path.exists('static/images/email_logo.png'):
            create_hosted_logo()
        
        subject = f"Xác thực lưu SVG - TikZ2SVG"
        html_content = create_svg_verification_email(username, svg_count)
        
        success, message = send_email(email, subject, html_content)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

def create_welcome_email(username):
    """Tạo email chào mừng với hosted logo"""
    # Đảm bảo username được encode đúng
    safe_username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Chào mừng đến với TikZ2SVG</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 10px;">
            <div style="display: inline-block; background: white; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <img src="https://tikz2svg.mathlib.io.vn/static/images/email_logo.png" alt="TikZ2SVG Logo" style="width: 60px; height: 60px;">
            </div>
            <h1 style="color: white; margin: 0; font-size: 24px;">TikZ2SVG</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Chuyển đổi TikZ thành SVG</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #333; margin-top: 0;">🎉 Chào mừng {safe_username}!</h2>
            <p style="color: #666; line-height: 1.6;">
                Cảm ơn bạn đã đăng ký sử dụng TikZ2SVG. Chúng tôi rất vui mừng chào đón bạn!
            </p>
            <p style="color: #666; line-height: 1.6;">
                Với TikZ2SVG, bạn có thể dễ dàng chuyển đổi các file TikZ thành SVG một cách nhanh chóng và chính xác.
            </p>
        </div>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1976d2; margin-top: 0;">🚀 Bắt đầu ngay:</h3>
            <ul style="color: #666; line-height: 1.6;">
                <li>Tải lên file TikZ của bạn</li>
                <li>Chọn định dạng SVG mong muốn</li>
                <li>Tải xuống kết quả ngay lập tức</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© 2024 TikZ2SVG. All rights reserved.</p>
            <p>Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    '''

def create_verification_email(username, verification_code):
    """Tạo email xác thực với hosted logo"""
    # Đảm bảo username được encode đúng
    safe_username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Xác thực tài khoản - TikZ2SVG</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 10px;">
            <div style="display: inline-block; background: white; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <img src="https://tikz2svg.mathlib.io.vn/static/images/email_logo.png" alt="TikZ2SVG Logo" style="width: 60px; height: 60px;">
            </div>
            <h1 style="color: white; margin: 0; font-size: 24px;">TikZ2SVG</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Xác thực tài khoản</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #333; margin-top: 0;">🔐 Xác thực tài khoản</h2>
            <p style="color: #666; line-height: 1.6;">
                Xin chào {safe_username}, vui lòng sử dụng mã xác thực sau để hoàn tất việc đăng ký tài khoản:
            </p>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <h3 style="color: #856404; margin-top: 0;">Mã xác thực:</h3>
                <div style="font-size: 32px; font-weight: bold; color: #856404; letter-spacing: 5px; font-family: monospace;">
                    {verification_code}
                </div>
            </div>
            
            <p style="color: #666; margin-top: 15px; font-size: 14px;">Mã này có hiệu lực trong 24 giờ</p>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h4 style="color: #856404; margin-top: 0;">⚠️ Lưu ý bảo mật:</h4>
            <ul style="color: #856404; margin: 0; padding-left: 20px;">
                <li>Không chia sẻ mã này với bất kỳ ai</li>
                <li>Mã chỉ có hiệu lực trong 24 giờ</li>
                <li>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© 2024 TikZ2SVG. All rights reserved.</p>
            <p>Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    '''

def create_svg_verification_email(username, svg_count):
    """Tạo email xác thực khi lưu nhiều SVG"""
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Xác thực lưu SVG - TikZ2SVG</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 10px;">
            <div style="display: inline-block; background: white; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                <img src="https://tikz2svg.mathlib.io.vn/static/images/email_logo.png" alt="TikZ2SVG Logo" style="width: 60px; height: 60px;">
            </div>
            <h1 style="color: white; margin: 0; font-size: 24px;">TikZ2SVG</h1>
            <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">Xác thực lưu SVG</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #333; margin-top: 0;">📊 Thông báo lưu SVG</h2>
            <p style="color: #666; line-height: 1.6;">
                Xin chào {username}, chúng tôi nhận thấy bạn đã lưu {svg_count} file SVG trong ngày hôm nay.
            </p>
            <p style="color: #666; line-height: 1.6;">
                Đây là một thông báo xác thực để đảm bảo tài khoản của bạn an toàn.
            </p>
        </div>
        
        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <h3 style="color: #2e7d32; margin-top: 0;">✅ Hoạt động bình thường</h3>
            <p style="color: #2e7d32; line-height: 1.6;">
                Nếu đây là bạn, không cần thực hiện thêm hành động nào.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
            <p>© 2024 TikZ2SVG. All rights reserved.</p>
            <p>Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    '''

def generate_verification_code(length=6):
    """Tạo mã xác thực ngẫu nhiên"""
    return ''.join(random.choices(string.digits, k=length))

def get_profile_changes_summary(old_data, new_data, has_avatar_change=False):
    """Tạo tóm tắt thay đổi profile"""
    changes = []
    
    if old_data.get('username') != new_data.get('username'):
        changes.append(f"Tên hiển thị: '{old_data.get('username', '')}' → '{new_data.get('username', '')}'")
    
    if old_data.get('bio') != new_data.get('bio'):
        old_bio = old_data.get('bio', '') or 'Không có'
        new_bio = new_data.get('bio', '') or 'Không có'
        if len(new_bio) > 50:
            new_bio = new_bio[:50] + '...'
        changes.append(f"Mô tả: '{old_bio}' → '{new_bio}'")
    
    # Kiểm tra thay đổi avatar - ưu tiên has_avatar_change nếu được truyền vào
    print(f"🔍 DEBUG: Checking avatar change - has_avatar_change={has_avatar_change}, old_avatar={old_data.get('avatar')}, new_avatar={new_data.get('avatar')}", flush=True)
    if has_avatar_change or old_data.get('avatar') != new_data.get('avatar'):
        print(f"🔍 DEBUG: Avatar change detected!", flush=True)
        if has_avatar_change or new_data.get('avatar'):
            changes.append("Ảnh đại diện: Thay đổi")
        else:
            changes.append("Ảnh đại diện: Xóa")
    
    return changes

def handle_profile_verification(user_id, verification_code, cursor, conn):
    """Xử lý xác thực thay đổi profile"""
    try:
        # Kiểm tra mã xác thực
        cursor.execute("""
            SELECT profile_verification_code, profile_verification_expires_at, 
                   pending_profile_changes, profile_verification_attempts
            FROM user WHERE id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            flash("Không tìm thấy thông tin xác thực.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        stored_code = result['profile_verification_code']
        expires_at = result['profile_verification_expires_at']
        pending_changes = json.loads(result['pending_profile_changes']) if result['pending_profile_changes'] else {}
        attempts = result['profile_verification_attempts']
        
        # Kiểm tra thời gian hết hạn
        if expires_at and datetime.now() > expires_at:
            # Xóa thông tin xác thực hết hạn
            cursor.execute("""
                UPDATE user SET 
                    profile_verification_code = NULL,
                    profile_verification_expires_at = NULL,
                    pending_profile_changes = NULL,
                    profile_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("Mã xác thực đã hết hạn. Vui lòng thực hiện lại thay đổi.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Kiểm tra số lần thử sai
        if attempts >= 5:
            # Xóa thông tin xác thực khi đạt giới hạn thử sai
            cursor.execute("""
                UPDATE user SET 
                    profile_verification_code = NULL,
                    profile_verification_expires_at = NULL,
                    pending_profile_changes = NULL,
                    profile_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("Bạn đã nhập sai mã quá nhiều lần (5 lần). Thay đổi đã bị hủy bỏ. Vui lòng thực hiện lại thay đổi.", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Kiểm tra mã xác thực
        if verification_code != stored_code:
            # Tăng số lần thử sai
            cursor.execute("""
                UPDATE user SET profile_verification_attempts = %s WHERE id = %s
            """, (attempts + 1, user_id))
            conn.commit()
            remaining_attempts = 5 - attempts - 1
            if remaining_attempts > 0:
                flash(f"Mã xác thực không đúng. Còn {remaining_attempts} lần thử.", "error")
            else:
                flash("Mã xác thực không đúng. Đây là lần thử cuối cùng!", "error")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        # Xác thực thành công - áp dụng thay đổi
        new_username = pending_changes.get('username', '')
        new_bio = pending_changes.get('bio', '')
        avatar_cropped_data = pending_changes.get('avatar_cropped_data')
        
        # Cập nhật username và bio
        cursor.execute("UPDATE user SET username = %s, bio = %s WHERE id = %s", 
                      (new_username, new_bio, user_id))
        
        # Xử lý avatar nếu có
        if avatar_cropped_data and avatar_cropped_data.startswith('data:image'):
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
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', old_avatar)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except Exception as e:
                                print(f"[WARN] Không thể xóa avatar cũ: {e}", flush=True)
                    
                    # Tạo tên file random
                    unique_id = uuid.uuid4().hex
                    filename = f"avatar_{unique_id}.{ext}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
                    
                    # Decode và lưu
                    with open(save_path, 'wb') as f:
                        f.write(base64.b64decode(b64_data))
                    
                    # Update DB
                    cursor.execute("UPDATE user SET avatar = %s WHERE id = %s", (filename, user_id))
            except Exception as e:
                print(f"[WARN] Error saving cropped avatar: {e}", flush=True)
                flash("Có lỗi khi lưu ảnh đại diện đã cắt.", "error")
        
        # Xóa thông tin xác thực
        cursor.execute("""
            UPDATE user SET 
                profile_verification_code = NULL,
                profile_verification_expires_at = NULL,
                pending_profile_changes = NULL,
                profile_verification_attempts = 0
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        flash("✅ Xác thực thành công! Hồ sơ đã được cập nhật.", "success")
        return redirect(url_for('profile_settings', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error in handle_profile_verification: {e}", flush=True)
        flash("Có lỗi xảy ra trong quá trình xác thực.", "error")
        return redirect(url_for('profile_settings', user_id=user_id))

@app.route('/profile/verification', methods=['GET', 'POST'])
@login_required
def profile_verification():
    """Trang xác thực danh tính tài khoản"""
    user_id = current_user.id
    
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
            # Kiểm tra xem có phải là hủy bỏ xác thực không
            if request.form.get("cancel_verification"):
                # Xóa thông tin xác thực
                cursor.execute("""
                    UPDATE user SET 
                        identity_verification_code = NULL,
                        identity_verification_expires_at = NULL,
                        identity_verification_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
                flash("Đã hủy bỏ quá trình xác thực danh tính.", "info")
                return redirect(url_for('profile_settings', user_id=user_id))
            
            # Kiểm tra xem có phải là xác thực không
            verification_code = request.form.get("verification_code", "").strip()
            
            if verification_code:
                # Xử lý xác thực danh tính
                return handle_identity_verification(user_id, verification_code, cursor, conn)
            
            # Nếu không có mã xác thực, gửi email xác thực
            # Tạo mã xác thực
            verification_code = generate_verification_code(6)
            expires_at = datetime.now() + timedelta(hours=24)
            
            # Lưu mã xác thực
            cursor.execute("""
                UPDATE user SET 
                    identity_verification_code = %s,
                    identity_verification_expires_at = %s,
                    identity_verification_attempts = 0
                WHERE id = %s
            """, (verification_code, expires_at, user_id))
            
            conn.commit()
            
            # Gửi email xác thực
            email_service = get_email_service()
            if email_service:
                try:
                    result = email_service.send_identity_verification_email(
                        email=current_user.email,
                        username=current_user.username or current_user.email.split('@')[0],
                        verification_code=verification_code
                    )
                    if result:
                        flash("📧 Mã xác thực đã được gửi đến email của bạn. Vui lòng kiểm tra và nhập mã để hoàn tất xác thực.", "info")
                    else:
                        flash("❌ Có lỗi khi gửi email xác thực. Vui lòng thử lại.", "error")
                except Exception as e:
                    print(f"❌ Error sending identity verification email: {e}", flush=True)
                    flash("❌ Có lỗi khi gửi email xác thực. Vui lòng thử lại.", "error")
            else:
                flash("❌ Dịch vụ email không khả dụng. Vui lòng thử lại sau.", "error")
            
            return redirect(url_for('profile_verification'))
        
        # GET request - hiển thị trang
        # Lấy thông tin xác thực hiện tại
        cursor.execute("""
            SELECT identity_verified, identity_verification_code, 
                   identity_verification_expires_at, identity_verification_attempts
            FROM user WHERE id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        
        identity_verified = user_data.get('identity_verified', False) if user_data else False
        has_pending_verification = bool(user_data and user_data.get('identity_verification_code'))
        verification_attempts = user_data.get('identity_verification_attempts', 0) if user_data else 0
        
        # Nếu đã xác thực, redirect về profile settings
        if identity_verified:
            flash("✅ Tài khoản của bạn đã được xác thực danh tính.", "success")
            return redirect(url_for('profile_settings', user_id=user_id))
        
        return render_template("profile_verification.html",
                             user_id=user_id,
                             has_pending_verification=has_pending_verification,
                             verification_attempts=verification_attempts)
        
    except Exception as e:
        print(f"❌ Error in profile_verification: {e}", flush=True)
        flash("Có lỗi xảy ra. Vui lòng thử lại.", "error")
        return redirect(url_for('profile_settings', user_id=user_id))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def handle_identity_verification(user_id, verification_code, cursor, conn):
    """Xử lý xác thực danh tính"""
    try:
        # Lấy thông tin xác thực
        cursor.execute("""
            SELECT identity_verification_code, identity_verification_expires_at, 
                   identity_verification_attempts
            FROM user WHERE id = %s
        """, (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data or not user_data['identity_verification_code']:
            flash("❌ Không tìm thấy mã xác thực. Vui lòng thử lại.", "error")
            return redirect(url_for('profile_verification'))
        
        stored_code = user_data['identity_verification_code']
        expires_at = user_data['identity_verification_expires_at']
        attempts = user_data['identity_verification_attempts']
        
        # Kiểm tra thời gian hết hạn
        if expires_at and datetime.now() > expires_at:
            # Xóa mã hết hạn
            cursor.execute("""
                UPDATE user SET 
                    identity_verification_code = NULL,
                    identity_verification_expires_at = NULL,
                    identity_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("❌ Mã xác thực đã hết hạn. Vui lòng thử lại.", "error")
            return redirect(url_for('profile_verification'))
        
        # Kiểm tra số lần thử
        if attempts >= 5:
            # Xóa thông tin xác thực
            cursor.execute("""
                UPDATE user SET 
                    identity_verification_code = NULL,
                    identity_verification_expires_at = NULL,
                    identity_verification_attempts = 0
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            flash("❌ Bạn đã nhập sai mã quá nhiều lần (5 lần). Vui lòng thử lại.", "error")
            return redirect(url_for('profile_verification'))
        
        # Kiểm tra mã xác thực
        if verification_code != stored_code:
            # Tăng số lần thử sai
            cursor.execute("""
                UPDATE user SET identity_verification_attempts = %s WHERE id = %s
            """, (attempts + 1, user_id))
            conn.commit()
            remaining_attempts = 5 - attempts - 1
            if remaining_attempts > 0:
                flash(f"❌ Mã xác thực không đúng. Còn {remaining_attempts} lần thử.", "error")
            else:
                flash("❌ Mã xác thực không đúng. Đây là lần thử cuối cùng!", "error")
            return redirect(url_for('profile_verification'))
        
        # Xác thực thành công
        cursor.execute("""
            UPDATE user SET 
                identity_verified = TRUE,
                identity_verification_code = NULL,
                identity_verification_expires_at = NULL,
                identity_verification_attempts = 0
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        flash("✅ Xác thực danh tính thành công! Tài khoản của bạn đã được xác thực.", "success")
        return redirect(url_for('profile_settings', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error in handle_identity_verification: {e}", flush=True)
        flash("Có lỗi xảy ra trong quá trình xác thực.", "error")
        return redirect(url_for('profile_verification'))

# Khởi tạo email service ngay khi import app
try:
    init_email_service(app)
    print("✅ Email service initialized successfully", flush=True)
except Exception as e:
    print(f"❌ Failed to initialize email service: {e}", flush=True)
    import traceback
    print(f"❌ Email service init error: {traceback.format_exc()}", flush=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)