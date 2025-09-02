/**
 * Index Page JavaScript
 * Xử lý tất cả logic cho trang chủ TikZ to SVG
 * Dựa trên older/index.html
 */

(function() {
    'use strict';

    // Private variables (không pollute global scope)
    let isLoggedIn = false;
    let activeFeedbackCount = 0;
    let cm = null; // CodeMirror instance
    let pollingInterval = null;

    // Initialize app state from HTML
    function initializeAppState() {
        try {
            const appStateElement = document.getElementById('app-state');
            if (appStateElement) {
                window.appState = JSON.parse(appStateElement.textContent);
                isLoggedIn = window.appState ? window.appState.loggedIn : false;
            } else {
                // Fallback: create default appState
                window.appState = { loggedIn: false };
                isLoggedIn = false;
            }
        } catch (error) {
            console.error('Error parsing appState:', error);
            window.appState = { loggedIn: false };
            isLoggedIn = false;
        }
    }

    // Suppress deprecated DOMNodeInserted warnings silently
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
        if (type === 'DOMNodeInserted' || type === 'DOMRemoved' || type === 'DOMSubtreeModified') {
            // Silently suppress deprecated MutationEvents without logging
            return;
        }
        return originalAddEventListener.call(this, type, listener, options);
    };

    // Utility functions
    function cleanControlChars(str) {
        return str.replace(/[^\x09\x0A\x20-\x7E\xA0-\uFFFF]/g, '');
    }

    function showLoginModal() {
        document.getElementById('login-modal').style.display = 'flex';
    }

    function hideLoginModal() {
        document.getElementById('login-modal').style.display = 'none';
    }

    function updateHeaderLoginState() {
        // Logic mới: Header đã được render từ server với avatar/username
        // Chỉ cần xử lý các logic bổ sung
        
        if (window.appState.loggedIn) {
            // Button states đã được xử lý trong file_card.js
            
            // Kiểm tra xem có ảnh SVG đang chờ hiển thị sau khi đăng nhập không
        }
    }

    // CodeMirror initialization
    function ensureCodeMirror() {
        const textarea = document.getElementById('code');
        if (!textarea) return;
        
        // Nếu đã có CodeMirror instance, không khởi tạo lại
        if (textarea.nextSibling && textarea.nextSibling.classList && textarea.nextSibling.classList.contains('CodeMirror')) {
            return;
        }
        
        cm = CodeMirror.fromTextArea(textarea, {
            mode: 'stex',
            theme: 'material',
            lineNumbers: true,
            placeholder: 'Nhập code TikZ tại đây...'
        });
    }

    function copySvgCode() {
        const codeBlock = document.getElementById('svgCode');
        const copyBtn = document.getElementById('copy-svg-code-btn');
        if (codeBlock && copyBtn) {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(function() {
                copyBtn.textContent = '✅ Đã copy!';
                setTimeout(() => { 
                    copyBtn.textContent = '📋 Copy Code'; 
                }, 2000);
            }).catch(function(err) {
                console.error('Clipboard API failed:', err);
                // Fallback method
                const textArea = document.createElement('textarea');
                textArea.value = code;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                copyBtn.textContent = '✅ Đã copy!';
                setTimeout(() => { 
                    copyBtn.textContent = '📋 Copy Code'; 
                }, 2000);
            });
        }
    }

    // Khởi tạo CodeMirror sẽ được gọi trong init chính
    function initCodeMirrorAndBindings() {
        var tikzCode = document.getElementById('code');
        cm = CodeMirror.fromTextArea(tikzCode, {
            mode: 'stex',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            placeholder: 'Nhập code TikZ tại đây...'
        });
        // Giá trị ban đầu từ server
        try {
            cm.setValue(JSON.parse(document.getElementById('initial-tikz')?.textContent || '""'));
        } catch(e) {
            cm.setValue('');
        }
        
        // Thêm sự kiện click vào CodeMirror để hiện modal đăng nhập nếu chưa đăng nhập
        if (!window.appState.loggedIn) {
            cm.on('mousedown', function() {
                showLoginModal();
            });
        }
        
        // Thêm sự kiện real-time preview cho form nhập code
        cm.on('change', function() {
            if (window.inputPreviewTimer) {
                clearTimeout(window.inputPreviewTimer);
            }
            window.inputPreviewTimer = setTimeout(() => {
                updateInputPreview(cm.getValue());
            }, 1000); // Delay 1 giây sau khi ngừng gõ
        });
        
        // Khởi tạo preview nếu có code TikZ ban đầu
        const initialCode = cm.getValue();
        if (initialCode && initialCode.trim()) {
            updateInputPreview(initialCode);
        }
    }

    // Hiển thị lỗi biên dịch TikZ, kèm log chi tiết nếu có
    function displayCompileError(message, fullLog) {
        console.log('displayCompileError called with:', { message, hasFullLog: !!fullLog });
        // Xóa TẤT CẢ error sections cũ
        document.querySelectorAll('.result-section, #result-section, #ajax-result-section').forEach(el => {
            if (el.querySelector('.error') || el.querySelector('#ajax-show-log-btn')) {
                el.remove();
            }
        });
        // Nếu không có log chi tiết thì chỉ hiện text lỗi chung
        const section = document.createElement('div');
        section.id = 'ajax-result-section';
        section.className = 'result-section';
        let html = `<div class=\"error\">Lỗi khi biên dịch!</div>`;
        if (fullLog && fullLog.trim()) {
            html += `<button id=\"ajax-show-log-btn\" style=\"margin-top:10px; background:#b71c1c; color:white; border:none; border-radius:4px; padding:6px 16px; cursor:pointer;\">Hiển thị chi tiết log</button>`;
            html += `<button id=\"ajax-copy-log-btn\" style=\"display:none; margin-left:10px; background:#ffc107; color:#212529; border:none; border-radius:4px; padding:6px 16px; cursor:pointer; font-weight:bold;\">Copy log</button>`;
            html += `<pre id=\"ajax-full-log\" style=\"display:none; background:#fff0f0; color:#b71c1c; border:1px solid #f5c6cb; border-radius:4px; padding:12px; margin-top:10px; max-height:400px; overflow:auto;\">${fullLog}</pre>`;
        }
        section.innerHTML = html;
        // Insert OUTSIDE the scroll area: sau .table-scroll-x và sau mobile hint
        const tableScroll = document.querySelector('.table-scroll-x');
        const mobileHint = document.getElementById('mobile-scroll-hint');
        if (tableScroll && tableScroll.parentNode) {
            if (mobileHint && mobileHint.parentNode) {
                // Insert error section sau mobile hint
                mobileHint.parentNode.insertBefore(section, mobileHint.nextSibling);
            } else {
                // Insert error section sau table-scroll-x
                tableScroll.parentNode.insertBefore(section, tableScroll.nextSibling);
            }
        } else {
            // Fallback: sau form
            const form = document.getElementById('tikz-form');
            if (form && form.parentNode) {
                form.parentNode.insertBefore(section, form.nextSibling);
            } else {
                document.body.appendChild(section);
            }
        }
        // Gán event handler
        const logBtn = document.getElementById('ajax-show-log-btn');
        const copyBtn = document.getElementById('ajax-copy-log-btn');
        if (logBtn) {
            logBtn.onclick = function() {
                const log = document.getElementById('ajax-full-log');
                if (log) {
                    if (log.style.display === 'none') {
                        log.style.display = 'block';
                        this.textContent = 'Ẩn chi tiết log';
                        if (copyBtn) copyBtn.style.display = 'inline-block';
                    } else {
                        log.style.display = 'none';
                        this.textContent = 'Hiển thị chi tiết log';
                        if (copyBtn) copyBtn.style.display = 'none';
                    }
                }
            };
            console.log('Log button event handler attached');
        }
        if (copyBtn) {
            copyBtn.onclick = function() {
                const log = document.getElementById('ajax-full-log');
                if (log) {
                    navigator.clipboard.writeText(log.textContent)
                        .then(() => {
                            copyBtn.textContent = '✅ Đã copy!';
                            setTimeout(() => { copyBtn.textContent = 'Copy log'; }, 2000);
                        })
                        .catch(() => {
                            copyBtn.textContent = '❌ Lỗi copy!';
                            setTimeout(() => { copyBtn.textContent = 'Copy log'; }, 2000);
                        });
                }
            };
        }
    }

    // Hàm AJAX mới để submit không reload trang
    async function submitTikzCodeAjax(event) {
        console.log('AJAX submit started'); // Debug
        event.preventDefault(); // Ngăn form submit bình thường
        
        // Kiểm tra đăng nhập
        if (!window.appState.loggedIn) {
            showLoginModal();
            return false;
        }

        // Lấy code từ CodeMirror
        const tikzCode = cleanControlChars(cm.getValue());
        if (!tikzCode.trim()) {
            alert('Vui lòng nhập code TikZ');
            return false;
        }

        // Hiển thị loading
        const compileBtn = document.getElementById('compile-btn');
        const originalText = compileBtn.textContent;
        compileBtn.textContent = 'Đang biên dịch...';
        compileBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('code', tikzCode);

            const response = await fetch('/', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                // KIỂM TRA LỖI CHÍNH XÁC HƠN
                // 1. Kiểm tra trong preview-col trước
                const previewColError = doc.querySelector('.preview-col .error');
                // 2. Kiểm tra trong result-section 
                const resultSectionError = doc.querySelector('.result-section .error');
                // 3. Kiểm tra error độc lập
                const standaloneError = doc.querySelector('.error');

                // Debug để kiểm tra error detection
                console.log('Checking for errors in response...');
                console.log('Preview col error:', previewColError);
                console.log('Result section error:', resultSectionError);
                console.log('Standalone error:', standaloneError);

                const errorElement = previewColError || resultSectionError || standaloneError;
                if (errorElement) {
                    const msg = errorElement.innerHTML;
                    // Tìm full log trong cùng document
                    const fullLogEl = doc.getElementById('full-log');
                    const fullLog = fullLogEl ? fullLogEl.textContent : '';
                    console.log('Error detected:', msg);
                    console.log('Full log:', fullLog ? 'Yes' : 'No');
                    displayCompileError(msg, fullLog);
                    return;
                }

                // Cập nhật preview
                const previewCol = document.querySelector('.preview-col');
                const newPreviewCol = doc.querySelector('.preview-col');
                if (previewCol && newPreviewCol) {
                    previewCol.innerHTML = newPreviewCol.innerHTML;
                }

                // Cập nhật result-tools-section và đảm bảo đặt bên ngoài .table-scroll-x
                const tableScroll = document.querySelector('.table-scroll-x');
                const mobileHint = document.getElementById('mobile-scroll-hint');
                const resultToolsSection = document.getElementById('result-tools-section');
                const newResultToolsSection = doc.getElementById('result-tools-section');
                
                if (newResultToolsSection) {
                    if (resultToolsSection) {
                        resultToolsSection.innerHTML = newResultToolsSection.innerHTML;
                        resultToolsSection.style.display = 'block';
                        // Di chuyển ra ngay sau mobile hint (nếu có), ngược lại ngay sau .table-scroll-x
                        if (mobileHint && mobileHint.parentNode) {
                            mobileHint.parentNode.insertBefore(resultToolsSection, mobileHint.nextSibling);
                        } else if (tableScroll && tableScroll.parentNode) {
                            tableScroll.parentNode.insertBefore(resultToolsSection, tableScroll.nextSibling);
                        }
                    } else {
                        // Tạo mới result-tools-section nếu chưa có và đặt sau mobile hint (nếu có) hoặc sau .table-scroll-x
                        const newSection = document.createElement('div');
                        newSection.id = 'result-tools-section';
                        newSection.innerHTML = newResultToolsSection.innerHTML;
                        if (mobileHint && mobileHint.parentNode) {
                            mobileHint.parentNode.insertBefore(newSection, mobileHint.nextSibling);
                        } else if (tableScroll && tableScroll.parentNode) {
                            tableScroll.parentNode.insertBefore(newSection, tableScroll.nextSibling);
                        } else {
                            // Fallback: thêm cuối body nếu không tìm thấy .table-scroll-x
                            document.body.appendChild(newSection);
                        }
                    }
                    // Ẩn hoặc xóa ajax-result-section nếu có
                    const ajaxResultSection = document.getElementById('ajax-result-section');
                    if (ajaxResultSection) {
                        ajaxResultSection.style.display = 'none';
                    }
                } else if (resultToolsSection) {
                    resultToolsSection.style.display = 'none';
                }

                // Khởi tạo lại CodeMirror cho textarea id="code"
                ensureCodeMirror();
                
                // Debug: Kiểm tra nút save server có được gán event chưa
                const saveServerBtn = document.getElementById('save-server-btn');
                if (saveServerBtn) {
                    console.log('Save server button found after AJAX update');
                    console.log('Button onclick:', saveServerBtn.onclick);
                } else {
                    console.log('Save server button not found after AJAX update');
                }

                // Hiện nút Lưu server sau khi biên dịch thành công
                if (saveServerBtn && newResultToolsSection) {
                    // Lấy svg_temp_id mới từ nút export-btn hoặc từ DOM mới
                    const exportBtn = (document.getElementById('result-tools-section') || newResultToolsSection)?.querySelector('#export-btn');
                    if (exportBtn) {
                        const newFileId = exportBtn.getAttribute('data-file-id');
                        if (newFileId) saveServerBtn.setAttribute('data-file-id', newFileId);
                        
                        // Thêm event listener cho export-btn sau khi được tạo động
                        if (!exportBtn.hasAttribute('data-event-bound')) {
                            exportBtn.setAttribute('data-event-bound', 'true');
                            exportBtn.addEventListener('click', async function() {
                                const svgTempId = exportBtn.getAttribute('data-file-id') || '';
                                const format = document.getElementById('export-format').value;
                                const widthVal = document.getElementById('export-width').value;
                                const heightVal = document.getElementById('export-height').value;
                                const dpiVal = document.getElementById('export-dpi').value;
                                const msg = document.getElementById('export-msg');

                                // Reset message area
                                msg.textContent = '';
                                msg.className = '';

                                if ((widthVal && widthVal <= 0) || (heightVal && heightVal <= 0) || (dpiVal && dpiVal <= 0)) {
                                    msg.textContent = 'Width, Height, DPI phải là số dương!';
                                    return;
                                }

                                exportBtn.disabled = true;
                                exportBtn.textContent = 'Đang xử lý...';

                                try {
                                    const res = await fetch('/temp_convert', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                            file_id: svgTempId,
                                            fmt: format,
                                            width: widthVal || undefined,
                                            height: heightVal || undefined,
                                            dpi: dpiVal || undefined
                                        })
                                    });
                                    const data = await res.json();
                                    if (data.url) {
                                        // Container to make layout clean like view_svg
                                        const container = document.createElement('div');
                                        container.style.display = 'flex';
                                        container.style.flexDirection = 'column';
                                        container.style.alignItems = 'center';
                                        container.style.gap = '6px';

                                        // Build link safely
                                        const link = document.createElement('a');
                                        link.href = data.url;
                                        link.download = '';
                                        link.className = 'export-download-link';
                                        link.textContent = `Tải về ${format.toUpperCase()}`;
                                        container.appendChild(link);

                                        // Optional: show file info if backend returns it (align with view_svg.html)
                                        if (data.file_size || data.actual_size) {
                                            const info = document.createElement('div');
                                            info.style.marginTop = '8px';
                                            info.style.fontSize = '12px';
                                            info.style.color = '#666';
                                            info.style.textAlign = 'center';
                                            info.style.fontWeight = 'bold';

                                            const parts = [];
                                            if (data.file_size) {
                                                const sizeKB = (data.file_size / 1024).toFixed(1);
                                                parts.push(`Dung lượng: ${sizeKB} KB`);
                                            }
                                            if (data.actual_size) {
                                                parts.push(`Kích thước: ${data.actual_size}`);
                                            }
                                            info.textContent = parts.join(' | ');
                                            container.appendChild(info);
                                        }

                                        msg.appendChild(container);
                                    } else {
                                        msg.textContent = data.error || 'Lỗi không xác định!';
                                    }
                                } catch (err) {
                                    msg.textContent = 'Lỗi kết nối hoặc máy chủ!';
                                }

                                exportBtn.disabled = false;
                                exportBtn.textContent = 'Tải xuống';
                            });
                        }
                    }
                    
                    // Thêm event listener cho toggle-svg-code-btn sau khi được tạo động
                    const toggleSvgCodeBtn = (document.getElementById('result-tools-section') || newResultToolsSection)?.querySelector('#toggle-svg-code-btn');
                    if (toggleSvgCodeBtn && !toggleSvgCodeBtn.hasAttribute('data-event-bound')) {
                        toggleSvgCodeBtn.setAttribute('data-event-bound', 'true');
                        toggleSvgCodeBtn.onclick = function() {
                            const container = document.getElementById('svg-code-container');
                            if (container) {
                                const currentlyHidden = container.style.display === 'none' || container.style.display === '';
                                container.style.display = currentlyHidden ? 'block' : 'none';
                                this.textContent = currentlyHidden ? '📜 Ẩn code SVG' : '📜 Xem code SVG';
                            }
                        };
                    }
                    
                    // Thêm event listener cho copy-svg-code-btn sau khi được tạo động
                    const copySvgCodeBtn = (document.getElementById('result-tools-section') || newResultToolsSection)?.querySelector('#copy-svg-code-btn');
                    if (copySvgCodeBtn && !copySvgCodeBtn.hasAttribute('data-event-bound')) {
                        copySvgCodeBtn.setAttribute('data-event-bound', 'true');
                        copySvgCodeBtn.onclick = function() {
                            copySvgCode();
                        };
                    }
                    
                    // Lấy code TikZ mới từ CodeMirror
                    if (cm && typeof cm.getValue === 'function') {
                        saveServerBtn.setAttribute('data-tikz-code', cm.getValue());
                    }
                    saveServerBtn.style.display = 'inline-block';
                }
            } else {
                // Handle HTTP errors
                try {
                    const errorData = await response.json();
                    displayCompileError(errorData.error || 'Lỗi khi biên dịch', errorData.error_log_full || '');
                } catch (e) {
                    displayCompileError('Lỗi kết nối với server', '');
                }
            }
        } catch (error) {
            console.error('AJAX Error:', error);
            displayCompileError('Có lỗi xảy ra khi biên dịch: ' + error.message, '');
        } finally {
            // Khôi phục nút
            compileBtn.textContent = originalText;
            compileBtn.disabled = false;
            console.log('AJAX submit completed'); // Debug
        }
        return false;
    }

    // Hàm cập nhật preview real-time cho form nhập code
    async function updateInputPreview(tikzCode) {
        if (!tikzCode.trim()) {
            const previewContainer = document.querySelector('.col:last-child');
            if (previewContainer) {
                previewContainer.innerHTML = '<div class="preview-placeholder"><p>Nhập code TikZ để xem preview real-time</p></div>';
            }
            return;
        }
        
        const previewContainer = document.querySelector('.col:last-child');
        if (previewContainer) {
            // Nếu đang có ảnh SVG preview, làm mờ ảnh thay vì ẩn
            const previewImg = previewContainer.querySelector('img');
            if (previewImg) {
                previewImg.style.opacity = '0.5';
                previewImg.alt = 'Đang cập nhật preview...';
            } else {
                previewContainer.innerHTML = '<div class="preview-placeholder"><p>Đang cập nhật preview...</p></div>';
            }
        }
        
        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `code=${encodeURIComponent(tikzCode)}`
            });
            
            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // Kiểm tra lỗi trước khi tìm SVG
                const previewColError = doc.querySelector('.preview-col .error');
                const resultSectionError = doc.querySelector('.result-section .error');
                const standaloneError = doc.querySelector('.error');
                
                const errorElement = previewColError || resultSectionError || standaloneError;
                if (errorElement) {
                    if (previewContainer) {
                        previewContainer.innerHTML = '<div class="preview-placeholder"><p>Code có lỗi - vui lòng sửa</p></div>';
                    }
                    return;
                }
                
                // Tìm SVG trong preview-col
                const newSvgUrl = doc.querySelector('.col:last-child img')?.src;
                
                if (newSvgUrl && previewContainer) {
                    // Nếu đã có img, chỉ cập nhật src và opacity
                    let previewImg = previewContainer.querySelector('img');
                    if (previewImg) {
                        previewImg.src = newSvgUrl;
                        previewImg.style.opacity = '1';
                        previewImg.alt = 'SVG Preview (Real-time)';
                    } else {
                        previewContainer.innerHTML = `<img src="${newSvgUrl}" alt="SVG Preview (Real-time)" style="width:100%;height:100%;object-fit:contain;display:block;">`;
                    }
                } else if (previewContainer) {
                    previewContainer.innerHTML = '<div class="preview-placeholder"><p>Chưa có preview</p></div>';
                }
            } else {
                if (previewContainer) {
                    previewContainer.innerHTML = '<div class="preview-placeholder"><p>Lỗi khi tạo preview</p></div>';
                }
            }
        } catch (error) {
            console.log('Input preview update failed:', error);
            if (previewContainer) {
                previewContainer.innerHTML = '<div class="preview-placeholder"><p>Lỗi kết nối</p></div>';
            }
        }
    }

    // Keyword modal functionality
    function initKeywordModal() {
        const confirmBtn = document.getElementById('confirmKeywordBtn');
        const keywordsInput = document.getElementById('keywordsInput');
        const suggestionsBox = document.getElementById('keywordSuggestions');

        let typingTimeout = null;

        // Khởi tạo biến global cho pending data
        window.pendingFileId = null;
        window.pendingTikzCode = "";

        // Event listener cho nút save-server-btn
        document.querySelectorAll('#save-server-btn').forEach(btn => {
            btn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();

                const fileId = this.getAttribute('data-file-id');
                const tikzCode = this.getAttribute('data-tikz-code') || "";
                
                if (!fileId) {
                    alert("Lỗi: không có file_id!");
                    return;
                }

                // Reset modal
                const keywordsInput = document.getElementById('keywordsInput');
                const suggestionsBox = document.getElementById('keywordSuggestions');
                if (keywordsInput) keywordsInput.value = "";
                if (suggestionsBox) {
                    suggestionsBox.innerHTML = '';
                    suggestionsBox.style.display = 'none';
                }

                // Lấy URL ảnh SVG từ preview hiện tại
                const currentPreview = document.querySelector('.col:last-child img');
                const modalSvgImg = document.getElementById('modal-svg-img');
                if (currentPreview && modalSvgImg) {
                    modalSvgImg.src = currentPreview.src;
                    modalSvgImg.style.display = 'block';
                } else if (modalSvgImg) {
                    modalSvgImg.style.display = 'none';
                }

                // Kiểm tra xem có file_id hợp lệ không (tức là đã biên dịch thành công)
                if (!fileId || fileId === 'None' || fileId === '') {
                    alert('⚠️ Cảnh báo: Chưa có ảnh SVG được biên dịch thành công.\n\nVui lòng nhấn nút "Biên dịch" trước khi lưu server.');
                    return;
                }

                // Kiểm tra xem code TikZ hiện tại có khớp với code TikZ đã được biên dịch không
                const currentTikzCode = cm ? cm.getValue() : document.getElementById('code').value;
                const compiledTikzCode = this.getAttribute('data-tikz-code') || "";
                
                if (currentTikzCode.trim() !== compiledTikzCode.trim()) {
                    alert('⚠️ Cảnh báo: Code TikZ hiện tại khác với code TikZ đã được biên dịch.\n\nẢnh hiển thị: từ code TikZ hiện tại\nẢnh sẽ được lưu: từ code TikZ đã biên dịch\n\nVui lòng nhấn nút "Biên dịch" để cập nhật trước khi lưu server.');
                    return;
                }

                // Lưu thông tin tạm thời
                window.pendingFileId = fileId;
                window.pendingTikzCode = tikzCode;

                // Hiện modal Bootstrap
                const modal = new bootstrap.Modal(document.getElementById('keywordModal'));
                modal.show();
            };
        });

        // Khi gõ trong ô textarea → fetch gợi ý
        keywordsInput.addEventListener('input', function() {
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                const text = keywordsInput.value.trim();
                const parts = text.split(',');
                const lastPart = parts[parts.length - 1].trim();

                if (lastPart.length < 1) {
                    suggestionsBox.style.display = 'none';
                    return;
                }

                fetch(`/api/keywords/search?q=${encodeURIComponent(lastPart)}`)
                    .then(res => res.json())
                    .then(data => {
                        suggestionsBox.innerHTML = '';
                        if (data.length === 0) {
                            suggestionsBox.style.display = 'none';
                            return;
                        }

                        data.forEach(word => {
                            const item = document.createElement('button');
                            item.type = 'button';
                            item.className = 'list-group-item list-group-item-action';
                            item.textContent = word;
                            item.addEventListener('click', () => {
                                // Thay thế phần cuối bằng từ chọn
                                parts[parts.length - 1] = word;
                                keywordsInput.value = parts.map(s => s.trim()).filter(s => s).join(', ') + ', ';
                                suggestionsBox.style.display = 'none';
                                keywordsInput.focus();
                            });
                            suggestionsBox.appendChild(item);
                        });
                        suggestionsBox.style.display = 'block';
                    })
                    .catch(err => {
                        console.error(err);
                        suggestionsBox.style.display = 'none';
                    });
            }, 300);
        });

        // Click ngoài suggestion → ẩn
        document.addEventListener('click', function(event) {
            if (!keywordsInput.contains(event.target) && !suggestionsBox.contains(event.target)) {
                suggestionsBox.style.display = 'none';
            }
        });

        // Khi modal mở → load tất cả keywords để hiển thị suggestions
        const keywordModal = document.getElementById('keywordModal');
        if (keywordModal) {
            keywordModal.addEventListener('shown.bs.modal', function() {
                // Load tất cả keywords khi modal mở
                fetch('/api/keywords/search?q=')
                    .then(res => res.json())
                    .then(data => {
                        suggestionsBox.innerHTML = '';
                        if (data.length > 0) {
                            data.forEach(word => {
                                const item = document.createElement('button');
                                item.type = 'button';
                                item.className = 'list-group-item list-group-item-action';
                                item.textContent = word;
                                item.addEventListener('click', () => {
                                    const currentValue = keywordsInput.value.trim();
                                    const newValue = currentValue ? currentValue + ', ' + word : word;
                                    keywordsInput.value = newValue + ', ';
                                    suggestionsBox.style.display = 'none';
                                    keywordsInput.focus();
                                });
                                suggestionsBox.appendChild(item);
                            });
                            suggestionsBox.style.display = 'block';
                        }
                    })
                    .catch(err => {
                        console.error('Error loading keywords:', err);
                    });
            });
        }

        // Khi bấm nút "Xác nhận" trong modal
        if (confirmBtn) {
            confirmBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const keywords = keywordsInput.value.trim();
                if (!keywords) {
                    alert('Vui lòng nhập ít nhất một từ khóa!');
                    keywordsInput.focus();
                    return;
                }

                if (!window.pendingFileId) {
                    alert("Lỗi: không có file_id!");
                    return;
                }

                fetch('/save_svg', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        file_id: window.pendingFileId,
                        tikz_code: window.pendingTikzCode,
                        keywords: keywords
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert("Đã lưu thành công!");
                        window.location.href = "/";
                    } else {
                        alert(data.error || "Có lỗi xảy ra!");
                    }
                })
                .catch(err => {
                    alert("Lỗi mạng hoặc server!");
                });

                const modal = bootstrap.Modal.getInstance(document.getElementById('keywordModal'));
                modal.hide();
            });
        }
    }

    // Search functionality
    function initializeSearch() {
        console.log('🔍 initializeSearch() called');
        const searchInput = document.getElementById('main-search-input');
        const suggestionsBox = document.getElementById('search-suggestions');
        
        console.log('🔍 searchInput:', searchInput);
        console.log('🔍 suggestionsBox:', suggestionsBox);
        
        if (!searchInput || !suggestionsBox) {
            console.log('❌ Missing searchInput or suggestionsBox');
            return;
        }
        
        // Handle input changes
        searchInput.addEventListener('input', function() {
            console.log('🔍 Search input event triggered');
            if (window.typingTimeout) {
                clearTimeout(window.typingTimeout);
            }
            const query = this.value.trim();
            console.log('🔍 Query:', query);
            
            if (query.length < 1) {
                console.log('🔍 Query too short, hiding suggestions');
                suggestionsBox.style.display = 'none';
                return;
            }
            
            console.log('🔍 Fetching suggestions for query:', query);
            window.typingTimeout = setTimeout(() => {
                fetch(`/api/keywords/search?q=${encodeURIComponent(query)}`)
                    .then(res => {
                        console.log('🔍 API response status:', res.status);
                        return res.json();
                    })
                    .then(data => {
                        console.log('🔍 API response data:', data);
                        suggestionsBox.innerHTML = '';
                        
                        if (data.length === 0) {
                            console.log('🔍 No suggestions found');
                            suggestionsBox.style.display = 'none';
                            return;
                        }
                        
                        console.log('🔍 Adding suggestions:', data);
                        data.forEach(keyword => {
                            const item = document.createElement('div');
                            item.className = 'search-suggestion-item';
                            item.textContent = keyword;
                            item.addEventListener('click', () => {
                                searchInput.value = keyword;
                                suggestionsBox.style.display = 'none';
                                // Navigate to search results page
                                window.location.href = `/search?q=${encodeURIComponent(keyword)}`;
                            });
                            suggestionsBox.appendChild(item);
                        });
                        
                        suggestionsBox.style.display = 'block';
                        console.log('🔍 Suggestions displayed');
                    })
                    .catch(err => {
                        console.error('❌ Search error:', err);
                        suggestionsBox.style.display = 'none';
                    });
            }, 300);
        });
        
        // Handle Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    suggestionsBox.style.display = 'none';
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
                suggestionsBox.style.display = 'none';
            }
        });
    }

    // Real-time synchronization for likes via polling
    // Only update like counts, not entire file list
    function startFilesPolling() {
        console.log('🔄 Starting likes polling...');
        
        const pollInterval = 15000; // 15 seconds
        
        pollingInterval = setInterval(function() {
            console.log('🔄 Polling likes...', new Date().toLocaleTimeString());
            
            // Kiểm tra flag toàn cục
            if (activeFeedbackCount > 0) {
                return;
            }
            
            // Fetch updated files data to check for like count changes
            const apiEndpoint = isLoggedIn ? '/api/files' : '/api/public/files';
            fetch(apiEndpoint)
                .then(response => response.json())
                .then(data => {
                    // Xử lý response format khác nhau giữa /api/files và /api/public/files
                    const files = isLoggedIn ? data : (data.files || []);
                    
                    // Only update like counts if there are changes
                    updateLikeCounts(files);
                })
                .catch(error => {
                    console.error('Error polling likes:', error);
                });
        }, pollInterval);
        
        console.log('🔄 Started likes polling (15s interval)');
    }

    // Function to update only like counts without reloading entire file list
    function updateLikeCounts(files) {
        files.forEach(file => {
            const fileCard = document.querySelector(`[data-file-id="${file.id}"]`);
            if (fileCard) {
                // Update like count
                const likeCountOne = fileCard.querySelector('.like-count.one');
                const likeCountTwo = fileCard.querySelector('.like-count.two');
                if (likeCountOne && likeCountTwo) {
                    likeCountOne.textContent = file.like_count;
                    likeCountTwo.textContent = file.like_count;
                }
                
                // Update like button state if user is logged in
                if (isLoggedIn) {
                    const likeCheckbox = fileCard.querySelector(`input[id="heart-${file.id}"]`);
                    if (likeCheckbox && likeCheckbox.checked !== file.is_liked_by_current_user) {
                        likeCheckbox.checked = file.is_liked_by_current_user;
                    }
                }
            }
        });
    }

    // Function to stop polling
    function stopFilesPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            console.log('🔄 Stopped files polling');
        }
    }

    // Cleanup function for page unload
    function cleanupOnPageUnload() {
        console.log('🧹 Cleaning up resources on page unload...');
        
        // Stop polling
        stopFilesPolling();
        
        // Clear any pending timeouts
        if (window.inputPreviewTimer) {
            clearTimeout(window.inputPreviewTimer);
            window.inputPreviewTimer = null;
        }
        
        if (window.typingTimeout) {
            clearTimeout(window.typingTimeout);
            window.typingTimeout = null;
        }
        
        // Clear any other intervals or timeouts if needed
        // Add more cleanup logic here as needed
        
        console.log('🧹 Cleanup completed');
    }

    // Setup cleanup event listeners
    function setupCleanupEventListeners() {
        // Cleanup when user navigates away from the page
        window.addEventListener('pagehide', cleanupOnPageUnload);
        
        // Cleanup when user closes the tab/window
        window.addEventListener('beforeunload', cleanupOnPageUnload);
        
        // Cleanup when user navigates to a different page (SPA navigation)
        window.addEventListener('unload', cleanupOnPageUnload);
        
        // Cleanup when page becomes hidden (user switches tabs)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                console.log('📱 Page hidden, pausing polling...');
                stopFilesPolling();
            } else {
                console.log('📱 Page visible, resuming polling...');
                startFilesPolling();
            }
        });
        
        console.log('🧹 Cleanup event listeners setup complete');
    }

    // Initialize form event listeners
    function initializeFormEvents() {
        const tikzForm = document.getElementById('tikz-form');
        if (tikzForm) {
            tikzForm.addEventListener('submit', function(event) {
                console.log('Form submit event');
                return submitTikzCodeAjax(event);
            });
        }
    }

    // Main initialization
    document.addEventListener('DOMContentLoaded', function() {
        // 0) Initialize app state first
        initializeAppState();
        
        // 0.5) Setup cleanup event listeners
        setupCleanupEventListeners();
        
        // 1) Touch device detection
        if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
            document.documentElement.classList.add('is-touch');
        }

        // 2) Initialize File Card component (single entry point)
        if (window.FileCardComponent && typeof window.FileCardComponent.init === 'function') {
            window.FileCardComponent.init();
        }

        // 3) Mobile menu
        const menuToggle = document.getElementById('menu-toggle');
        const mobileMenu = document.getElementById('mobile-menu');
        const closeMenu = document.getElementById('close-menu');
        if (menuToggle && mobileMenu && closeMenu) {
            menuToggle.addEventListener('click', () => mobileMenu.classList.remove('hidden'));
            closeMenu.addEventListener('click', () => mobileMenu.classList.add('hidden'));
            mobileMenu.addEventListener('click', e => { if (e.target === mobileMenu) mobileMenu.classList.add('hidden'); });
        }

        // 4) Header login state + pending view svg injection
        updateHeaderLoginState();

        // 5) Event listeners đã được xử lý trong file_card.js

        // 6) Smooth scroll hint + touch scroll – run after full load to avoid early layout thrash
        function setupHorizontalScrollUX() {
            const mobileHint = document.getElementById('mobile-scroll-hint');
            const scrollHost = document.querySelector('.table-scroll-x');
            function showMobileScrollHint() {
                if (!mobileHint || !scrollHost) return;
                const isMobile = window.innerWidth <= 768;
                const hasScroll = scrollHost.scrollWidth > scrollHost.clientWidth;
                if (isMobile && hasScroll) {
                    mobileHint.style.display = 'block';
                    setTimeout(() => { mobileHint.style.opacity = '0.7'; }, 3000);
                    setTimeout(() => { mobileHint.style.display = 'none'; }, 8000);
                } else {
                    mobileHint.style.display = 'none';
                }
            }
            showMobileScrollHint();
            window.addEventListener('resize', showMobileScrollHint);
            if (scrollHost) {
                let isScrolling = false, startX = 0, scrollLeft = 0;
                scrollHost.addEventListener('touchstart', function(e) {
                    isScrolling = true;
                    startX = e.touches[0].pageX - scrollHost.offsetLeft;
                    scrollLeft = scrollHost.scrollLeft;
                }, { passive: true });
                scrollHost.addEventListener('touchmove', function(e) {
                    if (!isScrolling) return;
                    const x = e.touches[0].pageX - scrollHost.offsetLeft;
                    const walk = (x - startX) * 2;
                    scrollHost.scrollLeft = scrollLeft - walk;
                }, { passive: true });
                scrollHost.addEventListener('touchend', function() { isScrolling = false; }, { passive: true });
            }
        }

        // Defer heavy layout work until all stylesheets/fonts are loaded
        window.addEventListener('load', function() {
            // 6) Horizontal scroll UX (after full load)
            setupHorizontalScrollUX();

                    // 7) Init CodeMirror + preview real-time (after CSS ready)
        initCodeMirrorAndBindings();

            // 8) Init highlight.js (after CSS ready)
            if (window.hljs) {
                hljs.highlightAll();
                if (hljs.initLineNumbersOnLoad) hljs.initLineNumbersOnLoad();
            }
        });

        // 9) Modal login button
        const modalLoginBtn = document.getElementById('modal-login-btn');
        if (modalLoginBtn) {
            modalLoginBtn.addEventListener('click', function() {
                window.location.href = window.appState.loginUrl;
            });
        }

        // 9.5) Modal cancel button
        const modalCancelBtn = document.querySelector('#login-modal .btn-cancel');
        if (modalCancelBtn) {
            modalCancelBtn.addEventListener('click', function() {
                hideLoginModal();
            });
        }

        // 10) Logout link
        const logoutLink = document.getElementById('logout-link');
        if (logoutLink) {
            logoutLink.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = '/logout?next=/';
            });
        }

        // 11) Keyword modal behaviors
        initKeywordModal();
        
        // 12) Initialize search functionality
        initializeSearch();
        
        // 13) Initialize form events
        initializeFormEvents();
        
        // 14) Action buttons đã được initialize trong file_card.js

        // 15) Touch events đã được xử lý trong initializeTouchBtnEvents cho tất cả users
        console.log('🔄 Touch events initialized for all users');

        console.log('DOMContentLoaded - appState.loggedIn:', window.appState && window.appState.loggedIn);

        // 16) Start polling for like updates
        startFilesPolling();

        // Nếu có code TikZ từ localStorage (từ View Mode), điền vào textarea chính
        // Thực thi sau khi tất cả đã được khởi tạo
        setTimeout(() => {
            const tikzFromStorage = localStorage.getItem('tikz_code_for_compile');
            if (tikzFromStorage) {
                console.log('Found tikz_code_for_compile in localStorage:', tikzFromStorage);
                // Điền code vào textarea chính
                if (cm && typeof cm.setValue === 'function') {
                    cm.setValue(tikzFromStorage);
                    console.log('Code set to CodeMirror successfully');
                } else {
                    const textarea = document.getElementById('code');
                    if (textarea) {
                        textarea.value = tikzFromStorage;
                        console.log('Code set to textarea successfully');
                    }
                }
                // Xóa dữ liệu đã sử dụng
                localStorage.removeItem('tikz_code_for_compile');
                console.log('tikz_code_for_compile removed from localStorage');
            }
        }, 100); // Delay 100ms để đảm bảo CodeMirror đã sẵn sàng
    });

    // Sau khi login → ép reload để đồng bộ session
    if (window.location.search.includes('login=1')) {
        window.location.href = window.location.pathname;
    }

    // Export only necessary functions to global scope
    window.showLoginModal = showLoginModal;
    window.hideLoginModal = hideLoginModal;
    window.ensureCodeMirror = ensureCodeMirror;
    window.initCodeMirrorAndBindings = initCodeMirrorAndBindings;
    window.initKeywordModal = initKeywordModal;
    window.submitTikzCodeAjax = submitTikzCodeAjax;
    window.copySvgCode = copySvgCode;
    window.updateInputPreview = updateInputPreview;
    window.startFilesPolling = startFilesPolling;
    window.stopFilesPolling = stopFilesPolling;
    window.updateLikeCounts = updateLikeCounts;
    window.cleanupOnPageUnload = cleanupOnPageUnload;

})();
