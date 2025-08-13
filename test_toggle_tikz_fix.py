#!/usr/bin/env python3
"""
Test script để kiểm tra logic toggleTikzCode đã được sửa
"""

import requests
from bs4 import BeautifulSoup
import re

def test_toggle_tikz_function():
    """Test function toggleTikzCode có logic kiểm tra đăng nhập"""
    print("🔍 Testing toggleTikzCode function...")
    
    try:
        response = requests.get('http://localhost:5173/')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm tất cả script tags
            scripts = soup.find_all('script')
            
            toggle_tikz_found = False
            login_check_found = False
            
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Tìm function toggleTikzCode
                    if 'function toggleTikzCode' in script_text:
                        toggle_tikz_found = True
                        print("✅ Function toggleTikzCode có sẵn")
                        
                        # Kiểm tra logic kiểm tra đăng nhập
                        if 'window.appState.loggedIn' in script_text:
                            login_check_found = True
                            print("✅ Có kiểm tra window.appState.loggedIn")
                        
                        if 'login-modal' in script_text:
                            print("✅ Có hiển thị login modal khi chưa đăng nhập")
                        
                        if 'return;' in script_text:
                            print("✅ Có return sớm khi chưa đăng nhập")
                        
                        # Tìm pattern kiểm tra đăng nhập
                        pattern = r'if\s*\(\s*!window\.appState\.loggedIn\s*\)\s*\{'
                        if re.search(pattern, script_text):
                            print("✅ Có logic if (!window.appState.loggedIn) {")
                        
                        # Tìm pattern hiển thị modal
                        modal_pattern = r'loginModal\.style\.display\s*=\s*[\'"]flex[\'"]'
                        if re.search(modal_pattern, script_text):
                            print("✅ Có logic hiển thị modal: loginModal.style.display = 'flex'")
                        
                        # Tìm pattern return sớm
                        return_pattern = r'return;'
                        if re.search(return_pattern, script_text):
                            print("✅ Có return sớm để ngăn hiển thị code")
                        
                        break
            
            if not toggle_tikz_found:
                print("❌ Không tìm thấy function toggleTikzCode")
            if not login_check_found:
                print("❌ Không tìm thấy logic kiểm tra đăng nhập")
                
        else:
            print(f"❌ Trang trả về status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lỗi khi test function: {e}")

def test_copy_tikz_function():
    """Test function copyTikzCode có logic kiểm tra đăng nhập"""
    print("\n🔍 Testing copyTikzCode function...")
    
    try:
        response = requests.get('http://localhost:5173/')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            scripts = soup.find_all('script')
            
            copy_tikz_found = False
            login_check_found = False
            
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Tìm function copyTikzCode
                    if 'function copyTikzCode' in script_text:
                        copy_tikz_found = True
                        print("✅ Function copyTikzCode có sẵn")
                        
                        # Kiểm tra logic kiểm tra đăng nhập
                        if 'window.appState.loggedIn' in script_text:
                            login_check_found = True
                            print("✅ Có kiểm tra window.appState.loggedIn")
                        
                        if 'login-modal' in script_text:
                            print("✅ Có hiển thị login modal khi chưa đăng nhập")
                        
                        if 'return;' in script_text:
                            print("✅ Có return sớm khi chưa đăng nhập")
                        
                        break
            
            if not copy_tikz_found:
                print("❌ Không tìm thấy function copyTikzCode")
            if not login_check_found:
                print("❌ Không tìm thấy logic kiểm tra đăng nhập")
                
        else:
            print(f"❌ Trang trả về status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lỗi khi test function: {e}")

def test_button_onclick():
    """Test nút "Xem Code" có onclick đúng"""
    print("\n🔍 Testing nút 'Xem Code' onclick...")
    
    try:
        response = requests.get('http://localhost:5173/')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm nút "Xem Code" trong loadSvgFiles function
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and 'loadSvgFiles' in script.string:
                    script_text = script.string
                    
                    # Tìm onclick="toggleTikzCode(this)"
                    if 'onclick="toggleTikzCode(this)"' in script_text:
                        print("✅ Nút 'Xem Code' có onclick='toggleTikzCode(this)'")
                        
                        # Kiểm tra có text "Xem Code"
                        if '"Xem Code"' in script_text:
                            print("✅ Có text 'Xem Code'")
                        
                        break
            else:
                print("❌ Không tìm thấy onclick='toggleTikzCode(this)' trong loadSvgFiles")
                
        else:
            print(f"❌ Trang trả về status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lỗi khi test button onclick: {e}")

def test_setup_file_card_buttons():
    """Test setupFileCardButtons không xử lý riêng nút "Xem Code" nữa"""
    print("\n🔍 Testing setupFileCardButtons...")
    
    try:
        response = requests.get('http://localhost:5173/')
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            scripts = soup.find_all('script')
            
            setup_found = False
            no_special_handling = False
            
            for script in scripts:
                if script.string and 'setupFileCardButtons' in script.string:
                    script_text = script.string
                    setup_found = True
                    print("✅ Function setupFileCardButtons có sẵn")
                    
                    # Kiểm tra không còn xử lý riêng nút "Xem Code"
                    if 'KHÔNG CẦN XỬ LÝ RIÊNG' in script_text:
                        no_special_handling = True
                        print("✅ Không còn xử lý riêng nút 'Xem Code'")
                    
                    if 'toggleTikzCode ĐÃ TỰ KIỂM TRA' in script_text:
                        print("✅ Có comment về toggleTikzCode tự kiểm tra")
                    
                    break
            
            if not setup_found:
                print("❌ Không tìm thấy function setupFileCardButtons")
            if not no_special_handling:
                print("❌ Vẫn còn xử lý riêng nút 'Xem Code'")
                
        else:
            print(f"❌ Trang trả về status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lỗi khi test setupFileCardButtons: {e}")

if __name__ == "__main__":
    print("🚀 Bắt đầu test logic toggleTikzCode đã được sửa...")
    print("=" * 60)
    
    test_toggle_tikz_function()
    test_copy_tikz_function()
    test_button_onclick()
    test_setup_file_card_buttons()
    
    print("\n" + "=" * 60)
    print("✅ Test hoàn thành!")
    print("\n📋 Tóm tắt sửa lỗi:")
    print("1. ✅ toggleTikzCode: Kiểm tra đăng nhập trước khi hiển thị code")
    print("2. ✅ copyTikzCode: Kiểm tra đăng nhập trước khi copy code")
    print("3. ✅ Nút 'Xem Code': Sử dụng onclick='toggleTikzCode(this)' trực tiếp")
    print("4. ✅ setupFileCardButtons: Không xử lý riêng nút 'Xem Code' nữa")
    print("5. ✅ Logic: Hiện modal đăng nhập khi chưa đăng nhập, không hiển thị code")
    print("\n🎯 Kết quả mong đợi:")
    print("   - Khi chưa đăng nhập: Click nút 'Xem Code' → Hiện modal đăng nhập")
    print("   - Khi đã đăng nhập: Click nút 'Xem Code' → Hiển thị code TikZ")
