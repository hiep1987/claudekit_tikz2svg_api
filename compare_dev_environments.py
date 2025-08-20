#!/usr/bin/env python3
"""
Script so sánh môi trường DEV trên Mac và VPS
Kiểm tra các tệp, dependencies, và cấu hình
"""

import os
import sys
import hashlib
import subprocess
import json
from datetime import datetime
from pathlib import Path

def get_file_hash(filepath):
    """Tính hash MD5 của file"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_system_info():
    """Lấy thông tin hệ thống"""
    info = {
        'platform': sys.platform,
        'python_version': sys.version,
        'current_dir': os.getcwd(),
        'timestamp': datetime.now().isoformat()
    }
    
    # Thêm thông tin hệ điều hành
    try:
        if sys.platform == "darwin":  # macOS
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
            info['uname'] = result.stdout.strip()
        elif sys.platform.startswith('linux'):  # Linux
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
            info['uname'] = result.stdout.strip()
    except Exception as e:
        info['uname'] = f"ERROR: {str(e)}"
    
    return info

def get_python_packages():
    """Lấy danh sách packages Python đã cài"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return f"ERROR: {result.stderr}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def scan_project_files(project_dir):
    """Quét tất cả files trong project"""
    files_info = {}
    ignore_patterns = {
        '__pycache__', '.git', '.venv', 'venv', 'node_modules',
        '.DS_Store', '*.pyc', '*.log', '*.tmp', '*.swp'
    }
    
    for root, dirs, files in os.walk(project_dir):
        # Bỏ qua các thư mục không cần thiết
        dirs[:] = [d for d in dirs if d not in ignore_patterns]
        
        for file in files:
            # Bỏ qua các file không cần thiết
            if any(pattern in file for pattern in ignore_patterns):
                continue
                
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, project_dir)
            
            try:
                stat = os.stat(filepath)
                files_info[rel_path] = {
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'hash': get_file_hash(filepath)
                }
            except Exception as e:
                files_info[rel_path] = {
                    'error': str(e)
                }
    
    return files_info

def compare_environments(mac_info, vps_info):
    """So sánh hai môi trường"""
    comparison = {
        'system_differences': {},
        'package_differences': {},
        'file_differences': {},
        'summary': {}
    }
    
    # So sánh thông tin hệ thống
    for key in set(mac_info['system'].keys()) | set(vps_info['system'].keys()):
        if key not in mac_info['system']:
            comparison['system_differences'][key] = f"Missing in MAC: {vps_info['system'][key]}"
        elif key not in vps_info['system']:
            comparison['system_differences'][key] = f"Missing in VPS: {mac_info['system'][key]}"
        elif mac_info['system'][key] != vps_info['system'][key]:
            comparison['system_differences'][key] = {
                'mac': mac_info['system'][key],
                'vps': vps_info['system'][key]
            }
    
    # So sánh packages
    mac_packages = {pkg['name']: pkg['version'] for pkg in mac_info['packages'] if isinstance(pkg, dict)}
    vps_packages = {pkg['name']: pkg['version'] for pkg in vps_info['packages'] if isinstance(pkg, dict)}
    
    for pkg in set(mac_packages.keys()) | set(vps_packages.keys()):
        if pkg not in mac_packages:
            comparison['package_differences'][pkg] = f"Missing in MAC: {vps_packages[pkg]}"
        elif pkg not in vps_packages:
            comparison['package_differences'][pkg] = f"Missing in VPS: {mac_packages[pkg]}"
        elif mac_packages[pkg] != vps_packages[pkg]:
            comparison['package_differences'][pkg] = {
                'mac': mac_packages[pkg],
                'vps': vps_packages[pkg]
            }
    
    # So sánh files
    for file_path in set(mac_info['files'].keys()) | set(vps_info['files'].keys()):
        if file_path not in mac_info['files']:
            comparison['file_differences'][file_path] = "Missing in MAC"
        elif file_path not in vps_info['files']:
            comparison['file_differences'][file_path] = "Missing in VPS"
        else:
            mac_file = mac_info['files'][file_path]
            vps_file = vps_info['files'][file_path]
            
            if mac_file.get('hash') != vps_file.get('hash'):
                comparison['file_differences'][file_path] = {
                    'mac_hash': mac_file.get('hash'),
                    'vps_hash': vps_file.get('hash'),
                    'mac_size': mac_file.get('size'),
                    'vps_size': vps_file.get('size')
                }
    
    # Tóm tắt
    comparison['summary'] = {
        'total_system_diffs': len(comparison['system_differences']),
        'total_package_diffs': len(comparison['package_differences']),
        'total_file_diffs': len(comparison['file_differences']),
        'mac_files_count': len(mac_info['files']),
        'vps_files_count': len(vps_info['files'])
    }
    
    return comparison

def generate_report(comparison, output_file='dev_comparison_report.json'):
    """Tạo báo cáo so sánh"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Báo cáo đã được lưu vào: {output_file}")
    print(f"📈 Tóm tắt:")
    print(f"   - Khác biệt hệ thống: {comparison['summary']['total_system_diffs']}")
    print(f"   - Khác biệt packages: {comparison['summary']['total_package_diffs']}")
    print(f"   - Khác biệt files: {comparison['summary']['total_file_diffs']}")
    print(f"   - Files trên MAC: {comparison['summary']['mac_files_count']}")
    print(f"   - Files trên VPS: {comparison['summary']['vps_files_count']}")

def main():
    """Hàm chính"""
    print("🔍 Bắt đầu quét môi trường DEV hiện tại...")
    
    # Quét môi trường hiện tại
    current_env = {
        'system': get_system_info(),
        'packages': get_python_packages(),
        'files': scan_project_files('.')
    }
    
    # Lưu thông tin môi trường hiện tại
    env_file = f"dev_environment_{current_env['system']['platform']}.json"
    with open(env_file, 'w', encoding='utf-8') as f:
        json.dump(current_env, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Đã lưu thông tin môi trường hiện tại vào: {env_file}")
    print(f"📋 Thông tin hệ thống:")
    print(f"   - Platform: {current_env['system']['platform']}")
    print(f"   - Python: {current_env['system']['python_version'].split()[0]}")
    print(f"   - Thư mục: {current_env['system']['current_dir']}")
    print(f"📦 Số packages: {len(current_env['packages']) if isinstance(current_env['packages'], list) else 'ERROR'}")
    print(f"📁 Số files: {len(current_env['files'])}")
    
    print("\n📝 Hướng dẫn:")
    print("1. Chạy script này trên VPS:")
    print(f"   python3 {sys.argv[0]}")
    print("2. Copy file JSON từ VPS về MAC")
    print("3. Chạy script so sánh:")
    print("   python3 compare_dev_environments.py --compare mac_file.json vps_file.json")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        if len(sys.argv) != 4:
            print("❌ Usage: python3 compare_dev_environments.py --compare mac_file.json vps_file.json")
            sys.exit(1)
        
        # So sánh hai file
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            mac_info = json.load(f)
        with open(sys.argv[3], 'r', encoding='utf-8') as f:
            vps_info = json.load(f)
        
        comparison = compare_environments(mac_info, vps_info)
        generate_report(comparison)
    else:
        main()


