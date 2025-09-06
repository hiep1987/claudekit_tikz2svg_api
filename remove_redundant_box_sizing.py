#!/usr/bin/env python3
"""
Tool để tìm và xóa redundant box-sizing: border-box trong CSS files
Vì Bootstrap đã có global rule: *, *::before, *::after { box-sizing: border-box; }
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

class RedundantBoxSizingRemover:
    def __init__(self, css_directory="static/css"):
        self.css_directory = css_directory
        self.backup_suffix = f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'redundant_removed': 0,
            'lines_saved': 0
        }
        
    def find_css_files(self):
        """Tìm tất cả CSS files (trừ backup files)"""
        css_files = []
        css_dir = Path(self.css_directory)
        
        if not css_dir.exists():
            print(f"❌ Directory {self.css_directory} không tồn tại")
            return css_files
            
        for css_file in css_dir.glob("*.css"):
            # Skip backup files
            if any(skip in css_file.name for skip in ['.backup', '_backup', '.bak', '_bak']):
                continue
            css_files.append(css_file)
            
        return sorted(css_files)
    
    def analyze_css_content(self, content):
        """Phân tích CSS content để tìm redundant box-sizing"""
        lines = content.split('\n')
        redundant_lines = []
        
        for i, line in enumerate(lines):
            # Pattern để match box-sizing: border-box
            if re.search(r'box-sizing\s*:\s*border-box\s*;', line, re.IGNORECASE):
                # Check if it's inside a comment
                if not self.is_in_comment(line):
                    redundant_lines.append({
                        'line_number': i + 1,
                        'line_content': line.strip(),
                        'full_line': line
                    })
                    
        return redundant_lines
    
    def is_in_comment(self, line):
        """Check if line is inside CSS comment"""
        stripped = line.strip()
        return stripped.startswith('/*') or stripped.startswith('*') or stripped.endswith('*/')
    
    def remove_redundant_box_sizing(self, content):
        """Xóa redundant box-sizing declarations"""
        lines = content.split('\n')
        modified_lines = []
        removed_count = 0
        
        for line in lines:
            # Check if line contains box-sizing: border-box
            if re.search(r'box-sizing\s*:\s*border-box\s*;', line, re.IGNORECASE):
                if not self.is_in_comment(line):
                    # Check if line has other properties
                    cleaned_line = re.sub(r'box-sizing\s*:\s*border-box\s*;?\s*', '', line, flags=re.IGNORECASE)
                    
                    # If line becomes empty or only whitespace, skip it
                    if not cleaned_line.strip():
                        removed_count += 1
                        continue
                    else:
                        # Keep the line but remove box-sizing property
                        modified_lines.append(cleaned_line)
                        removed_count += 1
                else:
                    # Keep commented lines
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
                
        return '\n'.join(modified_lines), removed_count
    
    def create_backup(self, file_path):
        """Tạo backup file"""
        backup_path = file_path.with_suffix(f'.css{self.backup_suffix}')
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def process_file(self, file_path, dry_run=True):
        """Process một CSS file"""
        print(f"\n🔍 Analyzing: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return False
            
        # Analyze content
        redundant_lines = self.analyze_css_content(content)
        
        if not redundant_lines:
            print(f"✅ No redundant box-sizing found")
            return False
            
        print(f"🔴 Found {len(redundant_lines)} redundant box-sizing declarations:")
        for item in redundant_lines:
            print(f"   Line {item['line_number']}: {item['line_content']}")
            
        if dry_run:
            print(f"🔍 DRY RUN - Would remove {len(redundant_lines)} declarations")
            return True
            
        # Remove redundant declarations
        new_content, removed_count = self.remove_redundant_box_sizing(content)
        
        if removed_count > 0:
            # Create backup
            backup_path = self.create_backup(file_path)
            print(f"💾 Backup created: {backup_path.name}")
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"✅ Removed {removed_count} redundant declarations")
            self.stats['redundant_removed'] += removed_count
            self.stats['lines_saved'] += removed_count
            return True
            
        return False
    
    def run(self, dry_run=True, specific_files=None):
        """Chạy tool"""
        print("🧹 REDUNDANT BOX-SIZING REMOVER")
        print("=" * 50)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        else:
            print("⚡ LIVE MODE - Files will be modified")
            
        print(f"📁 CSS Directory: {self.css_directory}")
        
        # Get CSS files
        if specific_files:
            css_files = [Path(self.css_directory) / f for f in specific_files]
            css_files = [f for f in css_files if f.exists()]
        else:
            css_files = self.find_css_files()
            
        if not css_files:
            print("❌ No CSS files found")
            return
            
        print(f"📋 Found {len(css_files)} CSS files")
        
        # Process files
        for css_file in css_files:
            self.stats['files_processed'] += 1
            if self.process_file(css_file, dry_run):
                self.stats['files_modified'] += 1
                
        # Print summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY:")
        print(f"   Files processed: {self.stats['files_processed']}")
        print(f"   Files modified: {self.stats['files_modified']}")
        print(f"   Redundant declarations removed: {self.stats['redundant_removed']}")
        print(f"   Lines saved: {self.stats['lines_saved']}")
        
        if dry_run and self.stats['files_modified'] > 0:
            print(f"\n🚀 Run with --live to actually remove redundant declarations")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove redundant box-sizing: border-box from CSS files")
    parser.add_argument('--live', action='store_true', help='Actually modify files (default is dry run)')
    parser.add_argument('--dir', default='static/css', help='CSS directory (default: static/css)')
    parser.add_argument('--files', nargs='+', help='Specific files to process')
    
    args = parser.parse_args()
    
    remover = RedundantBoxSizingRemover(css_directory=args.dir)
    remover.run(dry_run=not args.live, specific_files=args.files)

if __name__ == "__main__":
    main()
