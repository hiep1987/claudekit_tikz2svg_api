#!/usr/bin/env python3
"""
Script tạo các kích thước favicon khác nhau từ file logo.svg
Sử dụng SVG để có chất lượng tốt nhất
"""

from PIL import Image
import os
import cairosvg
import io

def create_favicons_from_svg():
    """Tạo các kích thước favicon khác nhau từ SVG"""
    
    # Đường dẫn file gốc
    source_file = "static/logo.svg"
    
    # Kiểm tra file gốc có tồn tại không
    if not os.path.exists(source_file):
        print(f"❌ Không tìm thấy file {source_file}")
        return
    
    print(f"✅ Đã tìm thấy file SVG: {source_file}")
    
    # Định nghĩa các kích thước cần tạo
    sizes = {
        "favicon-16x16.png": (16, 16),
        "favicon-32x32.png": (32, 32),
        "favicon-48x48.png": (48, 48),
        "apple-touch-icon.png": (180, 180),
        "android-chrome-192x192.png": (192, 192),
        "android-chrome-512x512.png": (512, 512)
    }
    
    # Tạo từng kích thước
    for filename, size in sizes.items():
        try:
            # Chuyển đổi SVG sang PNG với kích thước cụ thể
            png_data = cairosvg.svg2png(
                url=source_file,
                output_width=size[0],
                output_height=size[1]
                # Bỏ background_color để có nền trong suốt
            )
            
            # Lưu file
            output_path = f"static/{filename}"
            with open(output_path, 'wb') as f:
                f.write(png_data)
            
            file_size = os.path.getsize(output_path)
            print(f"✅ Đã tạo: {filename} ({size[0]}x{size[1]}px, {file_size} bytes)")
            
        except Exception as e:
            print(f"❌ Lỗi khi tạo {filename}: {e}")
    
    print("\n🎉 Hoàn thành! Các file favicon đã được tạo từ SVG với nền trong suốt!")
    print("\n📋 Danh sách file đã tạo:")
    for filename in sizes.keys():
        filepath = f"static/{filename}"
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"   - {filename} ({file_size} bytes)")

def create_favicon_ico_from_svg():
    """Tạo file favicon.ico từ SVG"""
    
    source_file = "static/logo.svg"
    
    if not os.path.exists(source_file):
        print(f"❌ Không tìm thấy file {source_file}")
        return
    
    try:
        # Tạo ảnh với nhiều kích thước cho ICO
        sizes = [(16, 16), (32, 32), (48, 48)]
        images = []
        
        for size in sizes:
            # Chuyển đổi SVG sang PNG
            png_data = cairosvg.svg2png(
                url=source_file,
                output_width=size[0],
                output_height=size[1]
                # Bỏ background_color để có nền trong suốt
            )
            
            # Chuyển bytes thành PIL Image
            image = Image.open(io.BytesIO(png_data))
            images.append(image)
        
        # Lưu file ICO
        output_path = "static/favicon.ico"
        images[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        
        file_size = os.path.getsize(output_path)
        print(f"✅ Đã tạo: favicon.ico ({file_size} bytes)")
        print(f"   Bao gồm các kích thước: {[f'{img.width}x{img.height}' for img in images]}")
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo favicon.ico: {e}")

if __name__ == "__main__":
    print("🚀 Bắt đầu tạo favicons từ SVG với nền trong suốt...")
    
    # Kiểm tra cairosvg
    try:
        import cairosvg
        print("✅ Thư viện cairosvg đã sẵn sàng")
    except ImportError:
        print("❌ Cần cài đặt cairosvg: pip install cairosvg")
        exit(1)
    
    create_favicons_from_svg()
    create_favicon_ico_from_svg()
