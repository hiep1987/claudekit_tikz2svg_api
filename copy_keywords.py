import mysql.connector
import os
import re
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

# Kết nối MySQL
conn = mysql.connector.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', ''),
    database=os.environ.get('DB_NAME', 'tikz2svg')
)
cursor = conn.cursor(dictionary=True)

# 1. Đọc tất cả svg_image có keywords
cursor.execute("SELECT id, keywords FROM svg_image WHERE keywords IS NOT NULL AND keywords != ''")
images = cursor.fetchall()

print(f"✅ Found {len(images)} svg_image rows with keywords.")

for img in images:
    svg_image_id = img['id']
    keywords_raw = img['keywords']
    
    if not keywords_raw.strip():
        continue

    # Tách danh sách từ khóa
    words = re.split(r'[;,|]', keywords_raw)
    cleaned_words = set(w.strip().lower() for w in words if w.strip())

    for word in cleaned_words:
        if not word:
            continue

        # Tìm keyword_id trong bảng keyword
        cursor.execute("SELECT id FROM keyword WHERE word = %s", (word,))
        keyword_row = cursor.fetchone()
        if not keyword_row:
            print(f"❗ Warning: Keyword '{word}' không có trong bảng keyword. Bỏ qua.")
            continue
        keyword_id = keyword_row['id']

        # Kiểm tra xem đã có liên kết chưa để tránh duplicate
        cursor.execute("""
            SELECT id FROM svg_image_keyword 
            WHERE svg_image_id = %s AND keyword_id = %s
        """, (svg_image_id, keyword_id))
        exists = cursor.fetchone()
        if exists:
            print(f"⚠️  Link exists: svg_image_id={svg_image_id}, keyword_id={keyword_id}")
            continue

        # Insert liên kết
        cursor.execute("""
            INSERT INTO svg_image_keyword (svg_image_id, keyword_id)
            VALUES (%s, %s)
        """, (svg_image_id, keyword_id))
        print(f"✅ Linked svg_image_id={svg_image_id} to keyword_id={keyword_id}")

conn.commit()
cursor.close()
conn.close()
print("🎉 All links created successfully.")
