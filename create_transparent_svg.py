#!/usr/bin/env python3
"""
Script tạo file SVG với background trong suốt rõ ràng
"""

import re

def create_transparent_svg():
    """Tạo file SVG với background trong suốt"""
    
    # Đọc file SVG gốc
    with open('static/logo.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Thêm style để đảm bảo background trong suốt
    # Tìm thẻ <svg> và thêm style
    svg_pattern = r'(<svg[^>]*>)'
    
    def add_style(match):
        svg_tag = match.group(1)
        if 'style=' in svg_tag:
            # Nếu đã có style, thêm background transparent
            svg_tag = re.sub(r'style="([^"]*)"', r'style="\1; background: transparent;"', svg_tag)
        else:
            # Nếu chưa có style, thêm mới
            svg_tag = svg_tag.replace('>', ' style="background: transparent;">')
        return svg_tag
    
    new_svg_content = re.sub(svg_pattern, add_style, svg_content)
    
    # Lưu file mới
    with open('static/logo-transparent.svg', 'w', encoding='utf-8') as f:
        f.write(new_svg_content)
    
    print("✅ Đã tạo file logo-transparent.svg với background trong suốt")
    print("📁 File: static/logo-transparent.svg")

if __name__ == "__main__":
    create_transparent_svg()
