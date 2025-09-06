#!/usr/bin/env python3
"""
CSS Scoping Script for tikz2svg_api
Automatically adds .tikz-app scope to all CSS selectors
"""

import os
import re
import shutil
from datetime import datetime

def scope_css_file(file_path, scope_class='.tikz-app'):
    """
    Tự động thêm scope class vào tất cả CSS selectors
    """
    if not os.path.exists(file_path):
        print(f"⚠️  File không tồn tại: {file_path}")
        return False
    
    print(f"🔄 Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original file
    backup_path = file_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(file_path, backup_path)
    print(f"📦 Backup created: {backup_path}")
    
    lines = content.split('\n')
    processed_lines = []
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments, empty lines, keyframes, media queries
        if (line.strip().startswith('/*') or 
            line.strip().startswith('*') or 
            line.strip() == '' or
            '@keyframes' in line or
            '@media' in line or
            line.strip().startswith('@')):
            processed_lines.append(line)
            continue
        
        # Process CSS selectors
        if '{' in line and not line.strip().startswith('/*'):
            # Extract selector part
            parts = line.split('{')
            selector_part = parts[0].strip()
            rest = '{'.join(parts[1:])
            
            # Skip if already scoped or is root element
            if (scope_class.replace('.', '') in selector_part or
                selector_part.startswith('html') or
                selector_part.startswith('body') or
                selector_part.startswith('*')):
                processed_lines.append(line)
                continue
            
            # Add scope to selector
            if selector_part:
                # Handle multiple selectors separated by comma
                selectors = [s.strip() for s in selector_part.split(',')]
                scoped_selectors = []
                
                for sel in selectors:
                    if sel.startswith('#') or sel.startswith('.') or sel.startswith('['):
                        scoped_sel = f"{scope_class} {sel}"
                    else:
                        scoped_sel = f"{scope_class} {sel}"
                    scoped_selectors.append(scoped_sel)
                
                new_selector = ', '.join(scoped_selectors)
                new_line = f"{new_selector} {{{rest}"
                processed_lines.append(new_line)
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    # Write processed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_lines))
    
    print(f"✅ Scoped: {file_path}")
    return True

def main():
    """Main function to scope all CSS files"""
    print("🚀 Starting CSS Scoping Process...")
    print("=" * 50)
    
    # CSS files to process
    css_files = [
        'static/css/index.css',
        'static/css/navigation.css', 
        'static/css/file_card.css',
        'static/css/login_modal.css',
        'static/css/profile_settings.css',
        'static/css/bio-editor.css',
        'static/css/profile_followed_posts.css'
    ]
    
    success_count = 0
    total_count = len(css_files)
    
    for css_file in css_files:
        if scope_css_file(css_file):
            success_count += 1
    
    print("=" * 50)
    print(f"🎉 CSS Scoping completed!")
    print(f"✅ Successfully processed: {success_count}/{total_count} files")
    
    if success_count < total_count:
        print("⚠️  Some files were skipped (not found)")
    
    print("\n📋 Next steps:")
    print("1. Update HTML template to add .tikz-app wrapper")
    print("2. Run manual fixes for unscoped selectors")
    print("3. Test all functionality")

if __name__ == "__main__":
    main()
