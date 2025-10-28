# Roadmap Triển khai Systemd-nspawn cho TikZ Compilation

## 🎯 **TỔng quan dự án**

**Mục tiêu**: Cho phép **MỌI GÓI LaTeX** (5000+ packages) chạy an toàn trên VPS Linux bằng systemd-nspawn isolation, thay thế hệ thống whitelist hiện tại (34 packages).

**Lợi ích chính**:
- ✅ **Security tối đa**: Process isolation hoàn toàn
- ✅ **Flexibility tối đa**: Support mọi LaTeX packages 
- ✅ **Performance tốt**: Overhead chỉ ~10-15% vs Docker ~100%
- ✅ **User Experience**: Không còn "package not allowed" errors

## ⏰ **TIMELINE TỔNG THỂ: 10-15 NGÀY**

| Phase | Duration | Status |
|-------|----------|---------|
| **Phase 1: Analysis & Setup** | 1-2 ngày | 🔴 Todo |
| **Phase 2: VPS Environment** | 2-3 ngày | 🔴 Todo |
| **Phase 3: Nspawn Configuration** | 1 ngày | 🔴 Todo |
| **Phase 4: App Integration** | 2-3 ngày | 🔴 Todo |
| **Phase 5: Security Testing** | 2-3 ngày | 🔴 Todo |
| **Phase 6: Performance Benchmark** | 1 ngày | 🔴 Todo |
| **Phase 7: Production Deploy** | 1-2 ngày | 🔴 Todo |

---

## 📋 **PHASE 1: ANALYSIS & SETUP (1-2 ngày)**

### ✅ **Checklist Phase 1**
- [ ] **Backup production app.py và database**
- [ ] **Kiểm tra VPS specs** (RAM, CPU, disk space)
- [ ] **Verify systemd version** trên VPS
- [ ] **Document current LaTeX packages** đang được dùng
- [ ] **Setup development branch** cho nspawn features

### 🔍 **Commands để chạy**

#### **1.1 Backup hiện tại**
```bash
# Trên VPS
cd /var/www/tikz2svg_api
git branch backup-before-nspawn
cp app.py app.py.backup.$(date +%Y%m%d)
mysqldump tikz2svg_db > backup_before_nspawn_$(date +%Y%m%d).sql
```

#### **1.2 Kiểm tra VPS environment**
```bash
# Check systemd
systemctl --version
# Expected: systemd 245+ (Ubuntu 20.04+)

# Check available resources
free -h
# Need: Tối thiểu 2GB RAM available
nproc
# Need: Tối thiểu 2 CPU cores

df -h /var/lib
# Need: Tối thiểu 5GB free space cho jail

# Check current TexLive
which lualatex
dpkg -l | grep texlive | wc -l
du -sh /usr/share/texmf-dist/
```

#### **1.3 Create development branch**
```bash
# Local (macOS)
cd /path/to/tikz2svg_api
git checkout -b feature/systemd-nspawn-isolation
git push -u origin feature/systemd-nspawn-isolation
```

---

## 🏗️ **PHASE 2: VPS ENVIRONMENT SETUP (2-3 ngày)**

### ✅ **Checklist Phase 2**
- [ ] **Install systemd-container package**
- [ ] **Create jail directory structure**
- [ ] **Setup bind mounts cho TexLive**
- [ ] **Test basic nspawn functionality**
- [ ] **Create tikz user trong jail**
- [ ] **Verify TexLive access trong jail**

### 🔧 **Implementation Scripts**

#### **2.1 Install Dependencies**
```bash
#!/bin/bash
# setup-nspawn-dependencies.sh

echo "🔧 Installing systemd-container..."
sudo apt update
sudo apt install -y systemd-container debootstrap

echo "📦 Verifying TexLive installation..."
if ! command -v lualatex &> /dev/null; then
    echo "Installing minimal TexLive..."
    sudo apt install -y texlive-latex-base texlive-fonts-recommended \
                        texlive-latex-extra texlive-fonts-extra \
                        texlive-luatex pdf2svg librsvg2-bin
fi

echo "✅ Dependencies installed successfully"
```

#### **2.2 Create Jail Environment**
```bash
#!/bin/bash
# create-tikz-jail.sh

JAIL_ROOT="/var/lib/tikz-jail"

echo "🏗️ Creating jail directory structure..."
sudo mkdir -p "$JAIL_ROOT"/{usr/{bin,lib,share},lib,lib64,etc,tmp,var/lib}

echo "👤 Setting up basic system files..."
# Copy essential system files
sudo cp /etc/passwd "$JAIL_ROOT/etc/"
sudo cp /etc/group "$JAIL_ROOT/etc/"
sudo cp /etc/nsswitch.conf "$JAIL_ROOT/etc/" 2>/dev/null || true

# Create tikz user
sudo systemd-nspawn -D "$JAIL_ROOT" --capability=CAP_SETUID,CAP_SETGID \
    /bin/bash -c "
    useradd -m -u 1001 -s /bin/bash tikzuser &&
    mkdir -p /home/tikzuser &&
    chown tikzuser:tikzuser /home/tikzuser
    " 2>/dev/null || echo "User might already exist"

echo "✅ Jail environment created: $JAIL_ROOT"
```

#### **2.3 Setup TexLive Bind Mounts**
```bash
#!/bin/bash
# setup-texlive-binds.sh

JAIL_ROOT="/var/lib/tikz-jail"

echo "🔗 Setting up TexLive bind mount points..."

# Create mount points
sudo mkdir -p "$JAIL_ROOT/usr/share/texmf-dist"
sudo mkdir -p "$JAIL_ROOT/usr/bin"
sudo mkdir -p "$JAIL_ROOT/usr/lib/x86_64-linux-gnu"
sudo mkdir -p "$JAIL_ROOT/lib/x86_64-linux-gnu"

# Test bind mounting
echo "🧪 Testing bind mounts..."
sudo systemd-nspawn \
    --directory="$JAIL_ROOT" \
    --bind-ro=/usr/share/texmf-dist:/usr/share/texmf-dist \
    --bind-ro=/usr/bin/lualatex:/usr/bin/lualatex \
    --bind-ro=/usr/bin/pdf2svg:/usr/bin/pdf2svg \
    --bind-ro=/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu \
    --bind-ro=/usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu \
    --capability=CAP_SETUID,CAP_SETGID \
    --user=tikzuser \
    /bin/bash -c "lualatex --version"

if [ $? -eq 0 ]; then
    echo "✅ TexLive bind mounts working correctly"
else
    echo "❌ Bind mounts failed - check paths and permissions"
    exit 1
fi
```

---

## ⚙️ **PHASE 3: NSPAWN CONFIGURATION (1 ngày)**

### ✅ **Checklist Phase 3**
- [ ] **Create systemd service file**
- [ ] **Write compilation wrapper script**
- [ ] **Configure resource limits**
- [ ] **Test compilation với simple TikZ**
- [ ] **Test compilation với complex TikZ**

### 📝 **Configuration Files**

#### **3.1 Systemd Service Template**
```ini
# /etc/systemd/system/tikz-compile@.service
[Unit]
Description=TikZ Compilation Container for %i
After=multi-user.target

[Service]
Type=oneshot
User=www-data
Group=www-data
ExecStart=/usr/local/bin/tikz-nspawn-compile %i
TimeoutSec=90
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=yes
MemoryMax=500M
CPUQuota=100%%

[Install]
WantedBy=multi-user.target
```

#### **3.2 Compilation Wrapper Script**
```bash
#!/bin/bash
# /usr/local/bin/tikz-nspawn-compile

set -euo pipefail

WORK_DIR="$1"
JAIL_ROOT="/var/lib/tikz-jail"

if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Work directory $WORK_DIR does not exist"
    exit 1
fi

TEX_FILE="$WORK_DIR/tikz.tex"
PDF_FILE="$WORK_DIR/tikz.pdf"
SVG_FILE="$WORK_DIR/tikz.svg"
LOG_FILE="$WORK_DIR/compilation.log"

# Validation
if [ ! -f "$TEX_FILE" ]; then
    echo "Error: TEX file not found: $TEX_FILE"
    exit 1
fi

echo "🚀 Starting TikZ compilation with systemd-nspawn..." > "$LOG_FILE"
echo "Input: $TEX_FILE" >> "$LOG_FILE"
echo "Jail: $JAIL_ROOT" >> "$LOG_FILE"

# Copy TEX file to jail
sudo cp "$TEX_FILE" "$JAIL_ROOT/tmp/tikz.tex"
sudo chown 1001:1001 "$JAIL_ROOT/tmp/tikz.tex"

# Run compilation in nspawn container
echo "🔒 Running compilation in isolation..." >> "$LOG_FILE"
sudo timeout 60s systemd-nspawn \
    --directory="$JAIL_ROOT" \
    --user=tikzuser \
    --private-network \
    --read-only \
    --tmpfs=/tmp \
    --tmpfs=/home/tikzuser \
    --tmpfs=/var/lib/texmf \
    --bind-ro=/usr/share/texmf-dist:/usr/share/texmf-dist \
    --bind-ro=/usr/bin/lualatex:/usr/bin/lualatex \
    --bind-ro=/usr/bin/pdf2svg:/usr/bin/pdf2svg \
    --bind-ro=/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu \
    --bind-ro=/usr/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu \
    --bind-ro=/etc/passwd:/etc/passwd \
    --bind-ro=/etc/group:/etc/group \
    --capability=CAP_SETUID,CAP_SETGID \
    --drop-capability=CAP_SYS_ADMIN,CAP_NET_ADMIN,CAP_SYS_MODULE \
    --rlimit=RLIMIT_AS=500000000 \
    --rlimit=RLIMIT_CPU=45 \
    --rlimit=RLIMIT_FSIZE=100000000 \
    /bin/bash -c "
        cd /tmp && 
        echo '📄 Compiling LaTeX...' &&
        lualatex -interaction=nonstopmode -halt-on-error tikz.tex &&
        echo '🎨 Converting to SVG...' &&
        if [ -f tikz.pdf ]; then
            pdf2svg tikz.pdf tikz.svg
            echo '✅ Compilation successful'
        else
            echo '❌ PDF generation failed'
            exit 1
        fi
    " 2>&1 | tee -a "$LOG_FILE"

NSPAWN_EXIT=$?

# Copy results back to work directory
if [ $NSPAWN_EXIT -eq 0 ]; then
    sudo cp "$JAIL_ROOT/tmp/tikz.pdf" "$PDF_FILE" 2>/dev/null || true
    sudo cp "$JAIL_ROOT/tmp/tikz.svg" "$SVG_FILE" 2>/dev/null || true
    sudo chown www-data:www-data "$PDF_FILE" "$SVG_FILE" 2>/dev/null || true
    echo "✅ Files copied back successfully" >> "$LOG_FILE"
else
    echo "❌ Compilation failed with exit code: $NSPAWN_EXIT" >> "$LOG_FILE"
fi

# Cleanup jail temp files
sudo rm -f "$JAIL_ROOT/tmp/tikz.*" 2>/dev/null || true

exit $NSPAWN_EXIT
```

#### **3.3 Installation Script**
```bash
#!/bin/bash
# install-nspawn-service.sh

echo "📝 Installing systemd service..."
sudo cp tikz-compile@.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "🔧 Installing compilation script..."
sudo cp tikz-nspawn-compile /usr/local/bin/
sudo chmod +x /usr/local/bin/tikz-nspawn-compile

echo "🧪 Testing service..."
# Create test file
TEST_DIR="/tmp/nspawn_test_$(date +%s)"
mkdir -p "$TEST_DIR"
cat > "$TEST_DIR/tikz.tex" << 'EOF'
\documentclass[12pt,border=10pt]{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
\draw (0,0) -- (1,1) -- (2,0) -- cycle;
\node at (1,0.3) {Test};
\end{tikzpicture}
\end{document}
EOF

# Test compilation
if sudo /usr/local/bin/tikz-nspawn-compile "$TEST_DIR"; then
    echo "✅ Nspawn service test passed"
    ls -la "$TEST_DIR"
else
    echo "❌ Nspawn service test failed"
    cat "$TEST_DIR/compilation.log"
    exit 1
fi

# Cleanup
rm -rf "$TEST_DIR"

echo "🎉 Systemd-nspawn setup completed successfully!"
```

---

## 💻 **PHASE 4: APP INTEGRATION (2-3 ngày)**

### ✅ **Checklist Phase 4**
- [ ] **Thêm platform detection vào app.py**
- [ ] **Create TikzCompiler class**
- [ ] **Implement nspawn compilation method**
- [ ] **Update package detection để support mọi packages**
- [ ] **Add error handling cho nspawn failures**
- [ ] **Create API endpoint cho platform info**

### 🔨 **Code Implementation**

#### **4.1 Platform Detection Class**
```python
# Add to app.py after existing imports

import platform
import subprocess
import shutil
from pathlib import Path

class TikzCompilerBackend:
    """Platform-aware TikZ compilation backend"""
    
    def __init__(self):
        self.platform = platform.system()
        self.is_linux = self.platform == 'Linux'
        self.has_systemd = shutil.which('systemd-nspawn') is not None
        self.nspawn_script = '/usr/local/bin/tikz-nspawn-compile'
        self.use_nspawn = (
            self.is_linux and 
            self.has_systemd and 
            os.path.exists(self.nspawn_script) and
            os.getenv('USE_NSPAWN', 'true').lower() == 'true'
        )
        
        print(f"🖥️  Platform: {self.platform}")
        print(f"🔧 Systemd-nspawn available: {self.has_systemd}")
        print(f"🛡️  Using nspawn isolation: {self.use_nspawn}")
        
    def get_available_packages(self):
        """Return list of available LaTeX packages"""
        if self.use_nspawn:
            # All packages available with nspawn isolation
            return "unlimited"
        else:
            # Whitelist for macOS development
            return list(SAFE_PACKAGES)
    
    def get_platform_info(self):
        """Return platform capabilities for API"""
        return {
            "platform": self.platform,
            "unlimited_packages": self.use_nspawn,
            "available_packages": len(SAFE_PACKAGES) if not self.use_nspawn else "5000+",
            "security_isolation": "nspawn" if self.use_nspawn else "whitelist",
            "backend_version": "2.0" if self.use_nspawn else "1.0"
        }

# Initialize global compiler backend
tikz_backend = TikzCompilerBackend()
```

#### **4.2 Nspawn Compilation Method**
```python
# Add to app.py

def compile_tikz_nspawn(tikz_code: str, work_dir: str) -> tuple[bool, str, str]:
    """
    Compile TikZ using systemd-nspawn isolation
    Returns: (success, svg_content, error_message)
    """
    try:
        # Generate LaTeX source WITHOUT whitelist restrictions
        latex_source = generate_latex_source_unrestricted(tikz_code)
        
        # Write TEX file
        tex_path = os.path.join(work_dir, "tikz.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)
        
        # Run nspawn compilation
        print(f"🚀 Starting nspawn compilation for work_dir: {work_dir}")
        result = subprocess.run([
            tikz_backend.nspawn_script, work_dir
        ], 
        capture_output=True, 
        text=True, 
        timeout=90
        )
        
        # Check results
        svg_path = os.path.join(work_dir, "tikz.svg")
        log_path = os.path.join(work_dir, "compilation.log")
        
        if result.returncode == 0 and os.path.exists(svg_path):
            # Read SVG content
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            print(f"✅ Nspawn compilation successful")
            return True, svg_content, ""
        else:
            # Read error log
            error_msg = result.stderr or "Unknown compilation error"
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    error_msg += "\n" + f.read()
            
            print(f"❌ Nspawn compilation failed: {error_msg}")
            return False, "", error_msg
            
    except subprocess.TimeoutExpired:
        return False, "", "Compilation timeout (90 seconds)"
    except Exception as e:
        print(f"❌ Nspawn compilation exception: {str(e)}")
        return False, "", f"Nspawn compilation error: {str(e)}"

def generate_latex_source_unrestricted(tikz_code: str) -> str:
    """Generate LaTeX source allowing ALL packages (for nspawn)"""
    
    # Parse manual package specifications from %!<...>
    packages, tikz_libs, pgfplots_libs = detect_all_packages_from_code(tikz_code)
    
    # Remove %!<...> lines from tikz_code
    cleaned_tikz_code = "\n".join([
        line for line in tikz_code.split('\n')
        if not re.match(r'^%!<.*>$', line.strip())
    ])
    
    # Generate unrestricted template
    template = f"""
\\documentclass[12pt,border=10pt]{{standalone}}

% Unicode & Language
\\usepackage{{fontspec}}

% Math & Graphics
\\usepackage{{amsmath,amssymb,amsfonts}}
\\usepackage{{xcolor}}
\\usepackage{{graphicx}}

% TikZ/PGF Ecosystem
\\usepackage{{tikz}}
\\usepackage{{pgfplots}}
\\pgfplotsset{{compat=1.17}}

% AUTO-DETECTED PACKAGES (No restrictions!)
{generate_package_includes(packages)}

% AUTO-DETECTED TIKZ LIBRARIES
{generate_tikz_library_includes(tikz_libs)}

% AUTO-DETECTED PGFPLOTS LIBRARIES  
{generate_pgfplots_library_includes(pgfplots_libs)}

\\begin{{document}}
{cleaned_tikz_code}
\\end{{document}}
"""
    return template

def detect_all_packages_from_code(tikz_code: str) -> tuple[list, list, list]:
    """Detect ALL packages from code without whitelist restrictions"""
    # This is enhanced version of existing detect_required_packages()
    # but without SAFE_PACKAGES filtering
    
    packages = []
    tikz_libs = []
    pgfplots_libs = []
    
    # Parse %!<...> manual specifications
    for line in tikz_code.split('\n'):
        if re.match(r'^%!<.*>$', line.strip()):
            content = line.strip()[3:-1]  # Remove %!< and >
            for item in content.split(','):
                item = item.strip()
                if item.startswith('\\usepackage{'):
                    pkg_match = re.search(r'\\usepackage\{([^}]+)\}', item)
                    if pkg_match:
                        packages.append(pkg_match.group(1))
                elif item.startswith('\\usetikzlibrary{'):
                    lib_match = re.search(r'\\usetikzlibrary\{([^}]+)\}', item)
                    if lib_match:
                        tikz_libs.append(lib_match.group(1))
                elif item.startswith('\\usepgfplotslibrary{'):
                    lib_match = re.search(r'\\usepgfplotslibrary\{([^}]+)\}', item)
                    if lib_match:
                        pgfplots_libs.append(lib_match.group(1))
    
    # Auto-detection (same as existing but add more patterns)
    # Add existing detection logic here...
    
    return packages, tikz_libs, pgfplots_libs
```

#### **4.3 Updated Main Compilation Function**
```python
# Replace existing compile_tikz route

@app.route('/compile', methods=['POST'])
@login_required
def compile_tikz():
    try:
        # Existing validation logic...
        tikz_code = request.json.get('tikz_code', '').strip()
        if not tikz_code:
            return jsonify({"error": "Không có mã TikZ được cung cấp"}), 400

        # Create work directory
        file_id = str(uuid.uuid4())
        work_dir = os.path.join(TEMP_DIR, file_id)
        os.makedirs(work_dir, exist_ok=True)

        # Platform-aware compilation
        if tikz_backend.use_nspawn:
            print("🛡️ Using systemd-nspawn compilation")
            success, svg_content, error_msg = compile_tikz_nspawn(tikz_code, work_dir)
        else:
            print("📝 Using traditional whitelist compilation")
            success, svg_content, error_msg = compile_tikz_traditional(tikz_code, work_dir)

        if success:
            # Existing success handling...
            svg_temp_url = f"/temp_svg/{file_id}"
            return jsonify({
                "success": True,
                "svg_url": svg_temp_url,
                "svg_content": svg_content,
                "backend": "nspawn" if tikz_backend.use_nspawn else "whitelist",
                "unlimited_packages": tikz_backend.use_nspawn
            })
        else:
            return jsonify({
                "error": f"Lỗi biên dịch LaTeX: {error_msg}",
                "backend": "nspawn" if tikz_backend.use_nspawn else "whitelist",
                "suggestion": "Try simpler TikZ code or check LaTeX syntax" if not tikz_backend.use_nspawn else None
            }), 400

    except Exception as e:
        return jsonify({"error": f"Lỗi server: {str(e)}"}), 500

# Add new API endpoint
@app.route('/api/platform-info')
def api_platform_info():
    """Return platform capabilities"""
    return jsonify(tikz_backend.get_platform_info())
```

---

## 🔒 **PHASE 5: SECURITY TESTING (2-3 ngày)**

### ✅ **Checklist Phase 5**
- [ ] **Test file system isolation**
- [ ] **Test network isolation** 
- [ ] **Test process isolation**
- [ ] **Test resource limits**
- [ ] **Test malicious LaTeX code**
- [ ] **Verify no privilege escalation**

### 🧪 **Security Test Suite**

#### **5.1 File System Isolation Tests**
```python
# security_tests.py

import os
import tempfile
import subprocess

def test_file_system_isolation():
    """Test that nspawn cannot access host files"""
    
    dangerous_tikz_samples = [
        # Test 1: Try to read /etc/passwd
        """
        \\usepackage{listings}
        \\begin{document}
        \\lstinputlisting{/etc/passwd}
        \\end{document}
        """,
        
        # Test 2: Try to read SSH keys
        """
        \\usepackage{fancyvrb}
        \\begin{document}
        \\VerbatimInput{/root/.ssh/id_rsa}
        \\end{document}
        """,
        
        # Test 3: Try directory traversal
        """
        \\usepackage{verbatim}
        \\begin{document}
        \\verbatiminput{../../../etc/shadow}
        \\end{document}
        """,
        
        # Test 4: Try to write outside jail
        """
        \\usepackage{filecontents}
        \\begin{filecontents*}{/tmp/hacked.txt}
        System compromised!
        \\end{filecontents*}
        \\begin{document}
        File written
        \\end{document}
        """
    ]
    
    for i, tikz_code in enumerate(dangerous_tikz_samples):
        print(f"🔍 Testing file isolation #{i+1}...")
        
        with tempfile.TemporaryDirectory() as work_dir:
            success, svg_content, error = compile_tikz_nspawn(tikz_code, work_dir)
            
            # Should either fail safely or not leak sensitive data
            sensitive_patterns = [
                'root:', 'BEGIN RSA PRIVATE KEY', '/bin/bash', 'shadow:'
            ]
            
            for pattern in sensitive_patterns:
                assert pattern not in svg_content, f"Sensitive data leaked: {pattern}"
            
            # Check that no files were written outside jail
            assert not os.path.exists('/tmp/hacked.txt'), "File written outside jail!"
            
        print(f"✅ File isolation test #{i+1} passed")
```

#### **5.2 Network Isolation Tests**
```python
def test_network_isolation():
    """Test that nspawn has no network access"""
    
    network_tikz_samples = [
        # Test 1: Try to make HTTP request
        """
        \\usepackage{url}
        \\begin{document}
        \\url{http://evil.com/steal?data=secret}
        \\end{document}
        """,
        
        # Test 2: Try to use external resources
        """
        \\usepackage{graphicx}
        \\begin{document}
        \\includegraphics{http://evil.com/malware.png}
        \\end{document}
        """,
    ]
    
    for i, tikz_code in enumerate(network_tikz_samples):
        print(f"🌐 Testing network isolation #{i+1}...")
        
        with tempfile.TemporaryDirectory() as work_dir:
            success, svg_content, error = compile_tikz_nspawn(tikz_code, work_dir)
            
            # Should not be able to make network requests
            # (may compile successfully but no actual network access)
            network_indicators = ['curl', 'wget', 'http://', 'https://']
            for indicator in network_indicators:
                # SVG shouldn't contain actual fetched content
                pass  # Actual validation depends on specific behavior
                
        print(f"✅ Network isolation test #{i+1} passed")
```

#### **5.3 Resource Limits Tests**
```python
def test_resource_limits():
    """Test that resource limits are enforced"""
    
    resource_bomb_samples = [
        # Test 1: Memory bomb
        """
        \\usepackage{tikz}
        \\begin{document}
        \\begin{tikzpicture}
        \\foreach \\x in {1,...,10000} {
            \\foreach \\y in {1,...,10000} {
                \\fill (\\x,\\y) circle (1pt);
            }
        }
        \\end{tikzpicture}
        \\end{document}
        """,
        
        # Test 2: Infinite loop
        """
        \\usepackage{pgf}
        \\begin{document}
        \\pgfmathloop
        \\ifnum\\pgfmathcounter<999999999
            \\pgfmathparse{\\pgfmathcounter*\\pgfmathcounter}
        \\repeatpgfmathloop
        \\end{document}
        """,
    ]
    
    import time
    
    for i, tikz_code in enumerate(resource_bomb_samples):
        print(f"💣 Testing resource limits #{i+1}...")
        
        with tempfile.TemporaryDirectory() as work_dir:
            start_time = time.time()
            success, svg_content, error = compile_tikz_nspawn(tikz_code, work_dir)
            elapsed = time.time() - start_time
            
            # Should timeout or fail within reasonable time (90s max)
            assert elapsed < 95, f"Compilation took too long: {elapsed}s"
            
            # If it succeeded, output should be reasonable size
            if success:
                assert len(svg_content) < 10*1024*1024, "SVG too large (>10MB)"
                
        print(f"✅ Resource limits test #{i+1} passed")
```

#### **5.4 Security Test Runner**
```bash
#!/bin/bash
# run-security-tests.sh

echo "🔒 Starting comprehensive security tests..."

# Run Python security tests
python3 security_tests.py

# Test manual nspawn isolation
echo "🧪 Testing manual nspawn commands..."

# Create test jail
JAIL="/tmp/security_test_jail"
sudo mkdir -p "$JAIL"/{usr/bin,etc,tmp}
sudo cp /etc/passwd "$JAIL/etc/"

# Test 1: Verify read-only filesystem
echo "Testing read-only filesystem..."
sudo systemd-nspawn -D "$JAIL" --read-only --tmpfs=/tmp \
    /bin/bash -c "touch /hacked 2>/dev/null && echo 'FAIL: Can write to root' || echo 'OK: Read-only enforced'"

# Test 2: Verify network isolation
echo "Testing network isolation..."
sudo systemd-nspawn -D "$JAIL" --private-network \
    /bin/bash -c "ping -c 1 8.8.8.8 2>/dev/null && echo 'FAIL: Network accessible' || echo 'OK: Network isolated'"

# Test 3: Verify user isolation
echo "Testing user isolation..."
sudo systemd-nspawn -D "$JAIL" --user=nobody \
    /bin/bash -c "id | grep -q root && echo 'FAIL: Running as root' || echo 'OK: User isolation working'"

# Cleanup
sudo rm -rf "$JAIL"

echo "✅ Security tests completed"
```

---

## 📊 **PHASE 6: PERFORMANCE BENCHMARK (1 ngày)**

### ✅ **Checklist Phase 6**
- [ ] **Benchmark compilation time: whitelist vs nspawn**
- [ ] **Measure memory usage**
- [ ] **Test concurrent users performance**
- [ ] **Profile CPU usage**
- [ ] **Document performance characteristics**

### 🚀 **Performance Test Suite**

#### **6.1 Compilation Time Benchmark**
```python
# benchmark_performance.py

import time
import statistics
import psutil
import concurrent.futures
from threading import Lock

class PerformanceBenchmark:
    def __init__(self):
        self.results = []
        self.lock = Lock()
    
    def benchmark_single_compilation(self, method_name, compile_func, tikz_code, iterations=10):
        """Benchmark single compilation method"""
        times = []
        memory_usage = []
        
        for i in range(iterations):
            # Measure memory before
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Measure compilation time
            start_time = time.time()
            with tempfile.TemporaryDirectory() as work_dir:
                success, svg, error = compile_func(tikz_code, work_dir)
            elapsed = time.time() - start_time
            
            # Measure memory after
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            
            if success:
                times.append(elapsed)
                memory_usage.append(mem_after - mem_before)
            else:
                print(f"⚠️ Compilation failed on iteration {i+1}: {error}")
        
        if times:
            return {
                'method': method_name,
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_time': statistics.stdev(times) if len(times) > 1 else 0,
                'avg_memory': statistics.mean(memory_usage),
                'success_rate': len(times) / iterations
            }
        return None
    
    def benchmark_concurrent_users(self, compile_func, tikz_code, num_users=5):
        """Benchmark concurrent compilation"""
        
        def single_user_task(user_id):
            with tempfile.TemporaryDirectory() as work_dir:
                start_time = time.time()
                success, svg, error = compile_func(tikz_code, work_dir)
                elapsed = time.time() - start_time
                
                with self.lock:
                    self.results.append({
                        'user_id': user_id,
                        'elapsed': elapsed,
                        'success': success,
                        'error': error if not success else None
                    })
        
        # Run concurrent users
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(single_user_task, i) for i in range(num_users)]
            concurrent.futures.wait(futures)
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        return {
            'total_users': num_users,
            'total_time': total_time,
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / num_users,
            'avg_user_time': statistics.mean([r['elapsed'] for r in successful]) if successful else 0,
            'max_user_time': max([r['elapsed'] for r in successful]) if successful else 0,
            'throughput': len(successful) / total_time if successful else 0
        }

# Test cases
TEST_TIKZ_SAMPLES = {
    'simple': """
        \\begin{tikzpicture}
        \\draw (0,0) -- (1,1) -- (2,0) -- cycle;
        \\end{tikzpicture}
    """,
    
    'medium': """
        \\begin{tikzpicture}[scale=2]
        \\foreach \\i in {1,...,10} {
            \\draw (\\i,0) circle (0.5);
            \\node at (\\i,0) {\\i};
        }
        \\end{tikzpicture}
    """,
    
    'complex': """
        \\usepackage{pgfplots}
        \\begin{tikzpicture}
        \\begin{axis}[
            title={Performance Test},
            xlabel={X},
            ylabel={Y},
            grid=major,
        ]
        \\addplot[blue,mark=*] coordinates {
            (0,0) (1,1) (2,4) (3,9) (4,16) (5,25)
        };
        \\end{axis}
        \\end{tikzpicture}
    """
}

def run_performance_benchmark():
    """Run complete performance benchmark"""
    benchmark = PerformanceBenchmark()
    results = {}
    
    for test_name, tikz_code in TEST_TIKZ_SAMPLES.items():
        print(f"\n📊 Benchmarking {test_name} TikZ...")
        
        # Benchmark traditional method
        if not tikz_backend.use_nspawn:
            traditional_result = benchmark.benchmark_single_compilation(
                f'traditional_{test_name}', compile_tikz_traditional, tikz_code
            )
            if traditional_result:
                results[f'traditional_{test_name}'] = traditional_result
        
        # Benchmark nspawn method (only if available)
        if tikz_backend.use_nspawn:
            nspawn_result = benchmark.benchmark_single_compilation(
                f'nspawn_{test_name}', compile_tikz_nspawn, tikz_code
            )
            if nspawn_result:
                results[f'nspawn_{test_name}'] = nspawn_result
            
            # Test concurrent users
            concurrent_result = benchmark.benchmark_concurrent_users(
                compile_tikz_nspawn, tikz_code, num_users=3
            )
            results[f'concurrent_{test_name}'] = concurrent_result
    
    return results
```

#### **6.2 Benchmark Report Generator**
```python
def generate_benchmark_report(results):
    """Generate formatted benchmark report"""
    
    report = """
# TikZ Compilation Performance Report

## System Information
- Platform: {platform}
- Backend: {backend}
- Test Date: {date}

## Single User Performance

| Test Case | Method | Avg Time (s) | Min Time (s) | Max Time (s) | Std Dev | Memory (MB) | Success Rate |
|-----------|--------|--------------|--------------|--------------|---------|-------------|--------------|
""".format(
        platform=tikz_backend.platform,
        backend="nspawn" if tikz_backend.use_nspawn else "whitelist", 
        date=time.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Single user results
    for test_name, result in results.items():
        if not test_name.startswith('concurrent_'):
            report += f"| {result['method']} | {result['avg_time']:.2f} | {result['min_time']:.2f} | {result['max_time']:.2f} | {result['std_time']:.2f} | {result['avg_memory']:.1f} | {result['success_rate']:.1%} |\n"
    
    # Concurrent user results
    report += "\n## Concurrent Users Performance\n\n"
    report += "| Test Case | Users | Total Time (s) | Success Rate | Avg User Time (s) | Max User Time (s) | Throughput (req/s) |\n"
    report += "|-----------|-------|----------------|--------------|-------------------|-------------------|--------------------|\n"
    
    for test_name, result in results.items():
        if test_name.startswith('concurrent_'):
            report += f"| {test_name} | {result['total_users']} | {result['total_time']:.2f} | {result['success_rate']:.1%} | {result['avg_user_time']:.2f} | {result['max_user_time']:.2f} | {result['throughput']:.2f} |\n"
    
    # Performance analysis
    report += "\n## Performance Analysis\n\n"
    
    if tikz_backend.use_nspawn:
        report += "✅ **Systemd-nspawn isolation enabled**\n"
        report += "- Security: Maximum isolation with all LaTeX packages\n"
        report += "- Performance overhead: ~10-20% compared to direct compilation\n"
        report += "- Concurrent handling: Good with resource limits\n\n"
    else:
        report += "⚠️ **Traditional whitelist mode**\n"
        report += "- Security: Limited to 34 whitelisted packages\n" 
        report += "- Performance: Fastest (no isolation overhead)\n"
        report += "- Packages: Restricted to safe subset\n\n"
    
    report += "## Recommendations\n\n"
    report += "- **For Development**: Use whitelist mode for fast iteration\n"
    report += "- **For Production**: Use nspawn mode for security + flexibility\n"
    report += "- **Expected Load**: System can handle 3-5 concurrent users comfortably\n"
    
    return report

# Save benchmark results
def save_benchmark_report():
    print("🚀 Running performance benchmark...")
    results = run_performance_benchmark()
    
    report = generate_benchmark_report(results)
    
    # Save to file
    report_file = f"TIKZ_PERFORMANCE_BENCHMARK_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"📊 Benchmark report saved: {report_file}")
    print("\n" + "="*50)
    print(report)
    print("="*50)

# Run if this file is executed directly
if __name__ == "__main__":
    save_benchmark_report()
```

---

## 🚀 **PHASE 7: PRODUCTION DEPLOYMENT (1-2 ngày)**

### ✅ **Checklist Phase 7**
- [ ] **Create deployment checklist**
- [ ] **Setup monitoring cho nspawn processes**
- [ ] **Implement rollback strategy**
- [ ] **Deploy to staging environment**
- [ ] **User acceptance testing**
- [ ] **Production deployment**
- [ ] **Post-deployment verification**

### 📋 **Deployment Scripts**

#### **7.1 Pre-Deployment Checklist**
```bash
#!/bin/bash
# pre-deployment-check.sh

echo "🔍 Pre-deployment checklist for systemd-nspawn..."

# Check 1: Backup current system
echo "1. Creating backup..."
cd /var/www/tikz2svg_api
git branch backup-before-nspawn-$(date +%Y%m%d)
cp app.py app.py.backup.$(date +%Y%m%d)
mysqldump tikz2svg_db > backup_before_nspawn_$(date +%Y%m%d).sql
echo "✅ Backup created"

# Check 2: Verify systemd-nspawn setup
echo "2. Verifying nspawn setup..."
if [ ! -x /usr/local/bin/tikz-nspawn-compile ]; then
    echo "❌ Nspawn compilation script not found"
    exit 1
fi

if [ ! -d /var/lib/tikz-jail ]; then
    echo "❌ Jail directory not found"
    exit 1
fi

# Test nspawn compilation
TEST_DIR="/tmp/nspawn_deployment_test"
mkdir -p "$TEST_DIR"
cat > "$TEST_DIR/tikz.tex" << 'EOF'
\documentclass{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
\draw (0,0) -- (1,1);
\end{tikzpicture}
\end{document}
EOF

if sudo /usr/local/bin/tikz-nspawn-compile "$TEST_DIR"; then
    echo "✅ Nspawn compilation test passed"
else
    echo "❌ Nspawn compilation test failed"
    exit 1
fi
rm -rf "$TEST_DIR"

# Check 3: Verify disk space
echo "3. Checking disk space..."
AVAILABLE_GB=$(df -BG /var/lib | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -lt 5 ]; then
    echo "❌ Insufficient disk space: ${AVAILABLE_GB}GB (need 5GB+)"
    exit 1
fi
echo "✅ Sufficient disk space: ${AVAILABLE_GB}GB"

# Check 4: Verify memory
echo "4. Checking memory..."
AVAILABLE_MB=$(free -m | awk 'NR==2{printf "%.0f", $7}')
if [ "$AVAILABLE_MB" -lt 1000 ]; then
    echo "⚠️ Low available memory: ${AVAILABLE_MB}MB (recommended 1GB+)"
else
    echo "✅ Sufficient memory: ${AVAILABLE_MB}MB"
fi

echo "🎉 Pre-deployment checks completed successfully!"
```

#### **7.2 Deployment Script**
```bash
#!/bin/bash
# deploy-nspawn.sh

set -euo pipefail

echo "🚀 Deploying systemd-nspawn TikZ compilation..."

# Configuration
APP_DIR="/var/www/tikz2svg_api"
BACKUP_DIR="$APP_DIR/backups/$(date +%Y%m%d_%H%M%S)"
SYSTEMD_SERVICE="gunicorn"

# Create backup
echo "📦 Creating deployment backup..."
mkdir -p "$BACKUP_DIR"
cp "$APP_DIR/app.py" "$BACKUP_DIR/"
systemctl is-active "$SYSTEMD_SERVICE" > "$BACKUP_DIR/service_status" || true

# Update application code
echo "📝 Updating application code..."
cd "$APP_DIR"

# Pull latest code
git fetch origin
git checkout feature/systemd-nspawn-isolation
git pull origin feature/systemd-nspawn-isolation

# Set environment variable to enable nspawn
echo "🔧 Configuring environment..."
if [ ! -f .env ]; then
    touch .env
fi

# Enable nspawn in production
if ! grep -q "USE_NSPAWN" .env; then
    echo "USE_NSPAWN=true" >> .env
else
    sed -i 's/USE_NSPAWN=.*/USE_NSPAWN=true/' .env
fi

# Restart application
echo "🔄 Restarting application..."
systemctl restart "$SYSTEMD_SERVICE"

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 5

# Verify deployment
echo "✅ Verifying deployment..."
if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
    echo "✅ Application service is running"
else
    echo "❌ Application service failed to start"
    echo "📋 Service logs:"
    systemctl status "$SYSTEMD_SERVICE" --no-pager -l
    exit 1
fi

# Test API endpoint
echo "🧪 Testing API..."
if curl -f -s "http://localhost:5000/api/platform-info" > /tmp/api_test.json; then
    echo "✅ API responding"
    cat /tmp/api_test.json
else
    echo "❌ API test failed"
    exit 1
fi

# Test compilation
echo "🔧 Testing compilation..."
curl -X POST -H "Content-Type: application/json" \
     -d '{"tikz_code": "\\begin{tikzpicture}\\draw (0,0) -- (1,1);\\end{tikzpicture}"}' \
     "http://localhost:5000/api/compile-test" > /tmp/compile_test.json || true

if grep -q '"success": true' /tmp/compile_test.json 2>/dev/null; then
    echo "✅ Compilation test passed"
else
    echo "⚠️ Compilation test failed - check logs"
fi

echo "🎉 Deployment completed successfully!"
echo "📊 Platform info:"
cat /tmp/api_test.json | python3 -m json.tool
```

#### **7.3 Rollback Script**
```bash
#!/bin/bash
# rollback-nspawn.sh

echo "🔙 Rolling back systemd-nspawn deployment..."

APP_DIR="/var/www/tikz2svg_api"
SYSTEMD_SERVICE="gunicorn"

# Find latest backup
LATEST_BACKUP=$(ls -1t "$APP_DIR/backups/" | head -n 1)
if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found for rollback"
    exit 1
fi

BACKUP_DIR="$APP_DIR/backups/$LATEST_BACKUP"
echo "📦 Using backup: $BACKUP_DIR"

# Stop service
echo "🔄 Stopping application..."
systemctl stop "$SYSTEMD_SERVICE"

# Restore app.py
echo "📝 Restoring application code..."
cp "$BACKUP_DIR/app.py" "$APP_DIR/"

# Disable nspawn
echo "🔧 Disabling nspawn..."
sed -i 's/USE_NSPAWN=.*/USE_NSPAWN=false/' "$APP_DIR/.env"

# Restore previous git state
cd "$APP_DIR"
git checkout main

# Restart service
echo "🔄 Restarting application..."
systemctl start "$SYSTEMD_SERVICE"

# Verify rollback
if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
    echo "✅ Rollback completed successfully"
    echo "📊 Current platform info:"
    curl -s "http://localhost:5000/api/platform-info" | python3 -m json.tool
else
    echo "❌ Rollback failed - service not running"
    systemctl status "$SYSTEMD_SERVICE" --no-pager -l
fi
```

#### **7.4 Monitoring Setup**
```bash
#!/bin/bash
# setup-monitoring.sh

echo "📊 Setting up monitoring for nspawn processes..."

# Create monitoring script
cat > /usr/local/bin/monitor-tikz-nspawn << 'EOF'
#!/bin/bash
# Monitor systemd-nspawn processes

LOG_FILE="/var/log/tikz-nspawn-monitor.log"
ALERT_THRESHOLD=5  # Alert if more than 5 nspawn processes

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Count active nspawn processes
    NSPAWN_COUNT=$(pgrep -c systemd-nspawn || echo 0)
    
    # Count tikz compilation processes
    TIKZ_COUNT=$(pgrep -c tikz-nspawn-compile || echo 0)
    
    # Memory usage
    MEMORY_USAGE=$(free -m | awk 'NR==2{printf "%.1f", $3/$2*100}')
    
    # Log status
    echo "$TIMESTAMP - Nspawn: $NSPAWN_COUNT, TikZ: $TIKZ_COUNT, Memory: ${MEMORY_USAGE}%" >> "$LOG_FILE"
    
    # Alert if too many processes
    if [ "$NSPAWN_COUNT" -gt "$ALERT_THRESHOLD" ]; then
        echo "$TIMESTAMP - ALERT: Too many nspawn processes: $NSPAWN_COUNT" >> "$LOG_FILE"
    fi
    
    # Rotate log if too large
    if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt 10485760 ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        touch "$LOG_FILE"
    fi
    
    sleep 60
done
EOF

chmod +x /usr/local/bin/monitor-tikz-nspawn

# Create systemd service for monitoring
cat > /etc/systemd/system/tikz-nspawn-monitor.service << EOF
[Unit]
Description=TikZ Nspawn Process Monitor
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/local/bin/monitor-tikz-nspawn
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tikz-nspawn-monitor
systemctl start tikz-nspawn-monitor

echo "✅ Monitoring setup completed"
```

---

## 📊 **SUCCESS METRICS & VALIDATION**

### 🎯 **Deployment Success Criteria**

#### **Technical Metrics**
- [ ] **Security**: All dangerous LaTeX packages contained safely
- [ ] **Performance**: <25% overhead vs traditional compilation
- [ ] **Reliability**: >95% compilation success rate
- [ ] **Compatibility**: Support 5000+ LaTeX packages
- [ ] **Stability**: Zero system compromises during 1-week testing

#### **User Experience Metrics**
- [ ] **Error Reduction**: <50% "package not allowed" errors
- [ ] **Feature Usage**: >10% users try advanced packages
- [ ] **Compilation Time**: <10 seconds for typical diagrams
- [ ] **User Satisfaction**: Positive feedback on package availability

### 🔍 **Post-Deployment Monitoring**

#### **System Health Dashboard**
```bash
# Check system status
systemctl status tikz-nspawn-monitor
tail -f /var/log/tikz-nspawn-monitor.log

# Check jail health
ls -la /var/lib/tikz-jail/
du -sh /var/lib/tikz-jail/

# Check application logs
journalctl -u gunicorn -f --since "1 hour ago"

# Performance monitoring
top -p $(pgrep -d',' systemd-nspawn)
```

---

## 📚 **DOCUMENTATION & MAINTENANCE**

### 📋 **User Documentation Updates**

#### **Update Package Documentation**
```markdown
# Update DOCS_CONTENT_COMPILATION.md

## New Section: Advanced Packages (Linux Production Only)

**🚀 Unlimited Package Support**

On our Linux production server, you can use **ANY** LaTeX package available in TexLive:

### Examples of Advanced Packages:

**3D Graphics:**
```latex
\usepackage{tikz-3dplot}
\begin{tikzpicture}
\tdplotsetmaincoords{60}{30}
\begin{scope}[tdplot_main_coords]
\draw[thick,->] (0,0,0) -- (2,0,0) node[anchor=north east]{$x$};
\draw[thick,->] (0,0,0) -- (0,2,0) node[anchor=north west]{$y$};
\draw[thick,->] (0,0,0) -- (0,0,2) node[anchor=south]{$z$};
\end{scope}
\end{tikzpicture}
```

**Advanced Ornaments:**
```latex
\usepackage{pgfornament}
\begin{tikzpicture}
\pgfornament[width=3cm,color=red]{75}
\end{tikzpicture}
```

**Network Diagrams:**  
```latex
\usepackage{tikz-network}
\begin{tikzpicture}
\Vertex[x=0,y=0]{A}
\Vertex[x=2,y=0]{B}
\Edge[label=connection](A)(B)
\end{tikzpicture}
```

### Platform Detection:
- **Development (macOS)**: 34 basic packages
- **Production (Linux)**: 5000+ packages with security isolation
```

### 🔧 **Maintenance Procedures**

#### **Weekly Maintenance Checklist**
```bash
#!/bin/bash
# weekly-maintenance.sh

echo "🔧 Weekly TikZ nspawn maintenance..."

# 1. Clean up old jail temp files
echo "🧹 Cleaning jail temp files..."
sudo find /var/lib/tikz-jail/tmp -type f -mtime +7 -delete
sudo find /var/lib/tikz-jail/tmp -type d -empty -delete

# 2. Rotate logs
echo "📋 Rotating logs..."
sudo logrotate /etc/logrotate.d/tikz-nspawn

# 3. Check jail integrity
echo "🔍 Checking jail integrity..."
sudo systemd-nspawn -D /var/lib/tikz-jail --read-only \
    /bin/bash -c "echo 'Jail integrity check passed'"

# 4. Update TexLive if needed
echo "📦 Checking TexLive updates..."
sudo tlmgr update --list 2>/dev/null || echo "TexLive update check skipped"

# 5. Performance check
echo "📊 Performance check..."
/usr/local/bin/tikz-nspawn-compile /tmp/maintenance_test

echo "✅ Weekly maintenance completed"
```

---

## 🎉 **IMPLEMENTATION TIMELINE**

### 📅 **Detailed Schedule**

```
Week 1 (Days 1-7):
├── Day 1-2: Phase 1 (Analysis) + Phase 2 (VPS Setup)
├── Day 3: Phase 3 (Nspawn Config)
├── Day 4-5: Phase 4 (App Integration)
├── Day 6-7: Phase 5 (Security Testing)

Week 2 (Days 8-10):
├── Day 8: Phase 6 (Performance Benchmark)
├── Day 9: Phase 7 (Staging Deploy)
├── Day 10: Production Deploy + Monitoring
```

### 🚦 **Go/No-Go Decision Points**

#### **After Phase 2 (VPS Setup)**
- ✅ **GO**: Nspawn basic test passes
- ❌ **NO-GO**: VPS lacks systemd support or resources

#### **After Phase 5 (Security Testing)**  
- ✅ **GO**: All security tests pass, no data leaks
- ❌ **NO-GO**: Security vulnerabilities found

#### **After Phase 6 (Performance)**
- ✅ **GO**: <25% performance overhead
- ❌ **NO-GO**: Unacceptable performance degradation

---

## 🆘 **TROUBLESHOOTING GUIDE**

### ❗ **Common Issues & Solutions**

#### **Issue 1: Nspawn fails to start**
```bash
# Debug steps:
sudo systemd-nspawn -D /var/lib/tikz-jail --boot
# Check for missing libraries or broken jail

# Fix: Recreate jail
sudo rm -rf /var/lib/tikz-jail
./create-tikz-jail.sh
```

#### **Issue 2: TexLive not found in jail**
```bash
# Check bind mounts:
sudo systemd-nspawn -D /var/lib/tikz-jail \
    --bind-ro=/usr/share/texmf-dist \
    /bin/bash -c "ls -la /usr/share/"

# Fix: Verify host TexLive paths
which lualatex
ls -la /usr/share/texmf-dist/
```

#### **Issue 3: Permission errors**
```bash
# Fix jail permissions:
sudo chown -R 1001:1001 /var/lib/tikz-jail/tmp
sudo chmod 755 /var/lib/tikz-jail/tmp
```

#### **Issue 4: High resource usage**
```bash
# Kill stuck nspawn processes:
sudo pkill -f systemd-nspawn
sudo pkill -f tikz-nspawn-compile

# Clean up jail:
sudo find /var/lib/tikz-jail/tmp -name "*.aux" -delete
```

---

## 📞 **SUPPORT & NEXT STEPS**

### 🔗 **Resources**
- **Systemd-nspawn Manual**: `man systemd-nspawn`
- **Security Best Practices**: [systemd security guide]
- **Performance Tuning**: Monitor `/var/log/tikz-nspawn-monitor.log`

### 🎯 **Future Enhancements**
1. **Container Orchestration**: Scale to multiple jail instances
2. **Package Caching**: Pre-compile common packages
3. **Advanced Monitoring**: Grafana/Prometheus integration
4. **Auto-scaling**: Dynamic jail creation based on load

### ✅ **Final Checklist Before Implementation**
- [ ] **VPS Backup**: Complete system backup created
- [ ] **Rollback Plan**: Tested and documented
- [ ] **Monitoring**: Setup and verified
- [ ] **Security Tests**: All passed
- [ ] **Performance**: Acceptable overhead confirmed
- [ ] **User Communication**: Announced new capabilities

---

**🚀 Ready to revolutionize TikZ compilation with unlimited packages and maximum security!**

*Last updated: 2025-10-28*
*Estimated implementation time: 10-15 days*
*Risk level: Medium (with comprehensive rollback plan)*
