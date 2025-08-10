from flask import Flask, request, render_template, url_for
import os
import subprocess
import uuid
from datetime import datetime
import glob

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'

TEX_TEMPLATE = r"""
\documentclass[12pt,border=10pt]{standalone}
\usepackage{fontspec}
\usepackage{polyglossia}
\setdefaultlanguage{vietnamese}
\usepackage{amsmath,amssymb}
\usepackage{tikz}
\usepackage{tkz-tab}
\usetikzlibrary{calc,positioning,shapes}
\begin{document}
%s
\end{document}
"""

def get_svg_files():
    """Lấy danh sách các file SVG trong thư mục static"""
    svg_files = []
    static_dir = app.config['UPLOAD_FOLDER']
    if os.path.exists(static_dir):
        for file in glob.glob(os.path.join(static_dir, "*.svg")):
            filename = os.path.basename(file)
            file_path = os.path.join(static_dir, filename)
            file_size = os.path.getsize(file_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
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
            
            svg_files.append({
                'filename': filename,
                'url': f"/static/{filename}",
                'size': file_size,
                'created_time': created_time,
                'file_time': file_time
            })
    
    # Sắp xếp theo thời gian tạo mới nhất
    svg_files.sort(key=lambda x: x['file_time'], reverse=True)
    return svg_files

@app.route("/", methods=["GET", "POST"])
def index():
    svg_url = None
    svg_full_url = None
    svg_content = None
    tikz_code = ""
    file_info = None

    if request.method == "POST":
        tikz_code = request.form.get("code", "")

        # Tạo tên file theo định dạng hhmmssddmmyy.svg
        now = datetime.now()
        svg_filename = now.strftime("%H%M%S%d%m%y") + ".svg"
        
        file_id = str(uuid.uuid4())
        work_dir = f"/tmp/{file_id}"
        os.makedirs(work_dir, exist_ok=True)

        tex_path = os.path.join(work_dir, "tikz.tex")
        pdf_path = os.path.join(work_dir, "tikz.pdf")
        svg_path_tmp = os.path.join(work_dir, "tikz.svg")
        svg_path_final = os.path.join(app.config['UPLOAD_FOLDER'], svg_filename)

        # Ghi file TeX
        with open(tex_path, "w") as f:
            f.write(TEX_TEMPLATE % tikz_code)

        try:
            subprocess.run(["lualatex", "-interaction=nonstopmode", "tikz.tex"],
                           cwd=work_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            subprocess.run(["pdf2svg", pdf_path, svg_path_tmp],
                           cwd=work_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            os.rename(svg_path_tmp, svg_path_final)
            svg_url = f"/static/{svg_filename}"
            svg_full_url = url_for('static', filename=svg_filename, _external=True)
            
            # Thông tin file
            file_size = os.path.getsize(svg_path_final)
            file_info = {
                'filename': svg_filename,
                'size': file_size,
                'created_time': now.strftime("%H:%M:%S - %d/%m/%Y")
            }
            
            # Đọc nội dung SVG để hiển thị code
            try:
                with open(svg_path_final, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
            except Exception as e:
                svg_content = f"Không thể đọc nội dung SVG: {str(e)}"

        except subprocess.CalledProcessError:
            svg_url = "Lỗi khi biên dịch hoặc chuyển đổi SVG."

    # Lấy danh sách các file SVG đã tạo
    svg_files = get_svg_files()

    return render_template("index.html",
                           tikz_code=tikz_code,
                           svg_url=svg_url,
                           svg_full_url=svg_full_url,
                           svg_content=svg_content,
                           file_info=file_info,
                           svg_files=svg_files)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
