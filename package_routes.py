"""
Package Management System Routes
===============================
Backend API routes for package management functionality
Integrates with Phase 1 database structure
"""

from functools import lru_cache
import time
import json
from datetime import datetime
from flask import request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import current_user
import mysql.connector
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

# =====================================================
# PERFORMANCE OPTIMIZED PACKAGE ROUTES
# =====================================================

def get_db_connection():
    """Get database connection with error handling"""
    try:
        import os
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return conn
    except Exception as e:
        current_app.logger.error(f"Database connection error: {e}")
        return None

@lru_cache(maxsize=1)
def get_cached_packages(cache_timestamp=None):
    """5-minute cached package data for performance - SIMPLIFIED SCHEMA"""
    conn = get_db_connection()
    if not conn:
        return {'active': [], 'manual': []}, {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get packages by status (active = có sẵn, manual = cần %!<..>)
        cursor.execute("""
            SELECT package_name, status, created_at, updated_at
            FROM supported_packages 
            ORDER BY status DESC, package_name
        """)
        
        all_packages = cursor.fetchall()
        
        # Group by status
        active_packages = [pkg for pkg in all_packages if pkg['status'] == 'active']
        manual_packages = [pkg for pkg in all_packages if pkg['status'] == 'manual']
        
        packages_by_status = {
            'active': active_packages,
            'manual': manual_packages
        }
        
        # Get request statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_requests
            FROM package_requests
        """)
        
        request_stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Format statistics
        stats = {
            'total_packages': len(all_packages),
            'active_packages': len(active_packages),
            'manual_packages': len(manual_packages),
            'total_requests': request_stats['total_requests'] or 0,
            'pending_requests': request_stats['pending_requests'] or 0
        }
        
        return packages_by_status, stats
        
    except Exception as e:
        current_app.logger.error(f"Error fetching packages: {e}")
        if conn:
            conn.close()
        return {'active': [], 'manual': []}, {}

def clear_package_cache():
    """Clear the package cache to force refresh"""
    get_cached_packages.cache_clear()

def setup_package_routes(app, limiter=None):
    """Setup all package management routes"""
    
    # Create limiter if not provided
    if limiter is None:
        import warnings
        # Suppress Flask-Limiter memory storage warning for development
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "Using the in-memory storage")
            limiter = Limiter(
                key_func=get_remote_address,
                app=app,
                default_limits=["1000 per hour", "100 per minute"]
            )
    
    @app.route('/packages')
    def packages():
        """Main packages listing page - SIMPLIFIED LAYOUT"""
        try:
            # Generate cache key based on current minute (5-minute cache)
            cache_key = int(time.time() // 300)  # 5-minute intervals
            packages_by_status, stats = get_cached_packages(cache_key)
            
            return render_template('packages.html',
                active_packages=packages_by_status['active'],
                manual_packages=packages_by_status['manual'],
                package_stats=stats,
                current_timestamp=int(time.time()),
                current_user_email=current_user.email if current_user.is_authenticated else None,
                current_username=current_user.username if current_user.is_authenticated else None,
                current_avatar=current_user.avatar if current_user.is_authenticated else None
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f"Error in packages route: {e}")
            current_app.logger.error(f"Full traceback: {error_details}")
            print(f"[DEBUG] Packages route exception: {e}", flush=True)
            print(f"[DEBUG] Full traceback: {error_details}", flush=True)
            flash('Có lỗi khi tải danh sách packages. Vui lòng thử lại sau.', 'error')
            return redirect(url_for('index'))
    
    @app.route('/packages/request')
    def package_request_form():
        """Package request form page"""
        return render_template('package_request.html',
            current_timestamp=int(time.time()),
            current_user_email=current_user.email if current_user.is_authenticated else None,
            current_username=current_user.username if current_user.is_authenticated else None,
            current_avatar=current_user.avatar if current_user.is_authenticated else None
        )
    
    @app.route('/packages/request', methods=['POST'])
    @limiter.limit("3 per hour")  # Rate limiting for requests
    def submit_package_request():
        """Handle package request form submission - Updated for simplified schema"""
        print("[DEBUG] Package request form submitted!", flush=True)
        print(f"[DEBUG] Form data: {dict(request.form)}", flush=True)
        try:
            # Validate required fields - Simplified for new schema
            required_fields = ['package_name', 'justification', 'requester_name', 'requester_email']
            
            print(f"[DEBUG] Validating {len(required_fields)} required fields...", flush=True)
            for field in required_fields:
                value = request.form.get(field, '').strip()
                print(f"[DEBUG] Field '{field}': '{value}' ({'✅ OK' if value else '❌ EMPTY'})", flush=True)
                if not value:
                    print(f"[DEBUG] Validation failed for field: {field}", flush=True)
                    flash(f'⚠️ <strong>Thiếu thông tin:</strong><br>Trường "{field}" là bắt buộc.', 'error')
                    return redirect(url_for('package_request_form'))
            
            # Get form data - Simplified for new schema
            form_data = {
                'package_name': request.form.get('package_name', '').strip(),
                'justification': request.form.get('justification', '').strip(),
                'use_case_example': request.form.get('use_case_example', '').strip() or None,
                'requester_name': request.form.get('requester_name', '').strip(),
                'requester_email': request.form.get('requester_email', '').strip(),
                'priority': request.form.get('priority', 'medium').strip()
            }
            
            # Check for duplicate package
            print("[DEBUG] Attempting database connection...", flush=True)
            conn = get_db_connection()
            if not conn:
                print("[DEBUG] ❌ Database connection failed!", flush=True)
                flash('Lỗi kết nối database. Vui lòng thử lại sau.', 'error')
                return redirect(url_for('package_request_form'))
            
            print("[DEBUG] ✅ Database connection successful!", flush=True)
            cursor = conn.cursor()
            
            # Check if package already exists - Updated for simplified schema
            cursor.execute("""
                SELECT id FROM supported_packages 
                WHERE package_name = %s
            """, (form_data['package_name'],))
            
            existing_package = cursor.fetchone()
            if existing_package:
                flash(f'📦 <strong>Package đã tồn tại!</strong><br>"{form_data["package_name"]}" đã có trong hệ thống.<br><a href="{url_for("packages")}">Xem danh sách packages →</a>', 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('packages'))
            
            # Check for duplicate request - Updated for simplified schema
            cursor.execute("""
                SELECT id FROM package_requests 
                WHERE package_name = %s 
                AND status IN ('pending', 'under_review')
            """, (form_data['package_name'],))
            
            existing_request = cursor.fetchone()
            if existing_request:
                flash(f'⏳ <strong>Yêu cầu đang được xử lý!</strong><br>Package "{form_data["package_name"]}" đã được yêu cầu trước đó.<br>Vui lòng đợi kết quả xử lý.', 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('packages'))
            
            # Insert new request - Updated for simplified schema
            print("[DEBUG] Inserting new package request...", flush=True)
            print(f"[DEBUG] SQL data: {form_data}", flush=True)
            
            cursor.execute("""
                INSERT INTO package_requests (
                    package_name, justification, use_case_example, 
                    requester_name, requester_email, priority, status
                ) VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            """, (
                form_data['package_name'], form_data['justification'], form_data['use_case_example'],
                form_data['requester_name'], form_data['requester_email'], form_data['priority']
            ))
            
            request_id = cursor.lastrowid
            print(f"[DEBUG] ✅ Package request inserted with ID: {request_id}", flush=True)
            
            # Log to changelog  
            print("[DEBUG] Logging to changelog...", flush=True)
            cursor.execute("""
                INSERT INTO package_changelog (
                    package_name, action_type, new_values, changed_by_email, change_reason, request_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                form_data['package_name'], 
                'added',  # Valid enum value
                json.dumps(form_data),
                form_data['requester_email'],
                f'New package request submitted (ID: {request_id})',
                request_id
            ))
            print("[DEBUG] ✅ Changelog entry created!", flush=True)
            
            print("[DEBUG] Committing database changes...", flush=True)
            conn.commit()
            print("[DEBUG] ✅ Database changes committed successfully!", flush=True)
            
            cursor.close()
            conn.close()
            
            # Send notification email to admin (implement later)
            # send_admin_notification_email(form_data, request_id)
            
            # Send success notification to user
            package_name = form_data['package_name']
            print(f"[DEBUG] 🎉 SUCCESS: Package request completed for '{package_name}'", flush=True)
            
            # Detailed success message
            success_message = f'''
            🎉 <strong>Yêu cầu thành công!</strong><br>
            📦 Package "<strong>{package_name}</strong>" đã được gửi để xem xét.<br>
            📧 Bạn sẽ nhận email thông báo khi có kết quả.<br>
            ⏱️ Thời gian xử lý: 3-7 ngày làm việc.
            '''
            flash(success_message, 'success')
            
            # Optional: Send notification email to admin
            try:
                # Check if email service is available
                if hasattr(current_app, 'email_service'):
                    print("[DEBUG] Attempting to send admin notification email...", flush=True)
                    admin_email = 'quochiep0504@gmail.com'
                    email_subject = f'🔔 New Package Request: {package_name}'
                    email_body = f'''
                    <h3>New Package Request Received</h3>
                    <p><strong>Package:</strong> {package_name}</p>
                    <p><strong>Requester:</strong> {form_data['requester_name']} ({form_data['requester_email']})</p>
                    <p><strong>Priority:</strong> {form_data['priority'].upper()}</p>
                    <p><strong>Justification:</strong></p>
                    <blockquote>{form_data['justification']}</blockquote>
                    {f"<p><strong>Use Case:</strong></p><blockquote>{form_data['use_case_example']}</blockquote>" if form_data['use_case_example'] else ""}
                    <p><strong>Request ID:</strong> #{request_id}</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr>
                    <p><a href="http://localhost:5173/admin/packages">🔗 Review in Admin Panel</a></p>
                    '''
                    
                    # Attempt to send email (non-blocking)
                    current_app.email_service.send_email(
                        to_email=admin_email,
                        subject=email_subject,
                        body=email_body,
                        is_html=True
                    )
                    print("[DEBUG] ✅ Admin notification email sent successfully!", flush=True)
                else:
                    print("[DEBUG] ⚠️ Email service not available, skipping admin notification", flush=True)
            except Exception as email_error:
                print(f"[DEBUG] ⚠️ Failed to send admin notification email: {email_error}", flush=True)
                # Don't fail the request if email fails
            
            return redirect(url_for('packages'))
            
        except Exception as e:
            print(f"[DEBUG] ❌ EXCEPTION in submit_package_request: {e}", flush=True)
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}", flush=True)
            current_app.logger.error(f"Error submitting package request: {e}")
            error_message = '''
            ❌ <strong>Có lỗi xảy ra!</strong><br>
            🔄 Vui lòng thử lại sau hoặc liên hệ admin nếu lỗi tiếp tục.<br>
            📧 Email hỗ trợ: quochiep0504@gmail.com
            '''
            flash(error_message, 'error')
            return redirect(url_for('package_request_form'))
    
    @app.route('/admin/packages')
    def admin_packages_dashboard():
        """Admin interface for managing package requests"""
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                flash('🔒 <strong>Bạn cần đăng nhập để truy cập Admin Panel</strong>', 'error')
                return redirect(url_for('index'))
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                flash('🚫 <strong>Không có quyền truy cập!</strong><br>Chỉ admin mới có thể truy cập trang này.', 'error')
                return redirect(url_for('index'))
            
            print("[DEBUG] Loading admin packages interface...", flush=True)
            
            conn = get_db_connection()
            if not conn:
                print("[DEBUG] ❌ Database connection failed!", flush=True)
                flash('Database connection error', 'error')
                return redirect(url_for('packages'))
            
            cursor = conn.cursor(dictionary=True)
            
            # Get all package requests with statistics
            cursor.execute("""
                SELECT pr.*, 
                       sp.status as package_status
                FROM package_requests pr
                LEFT JOIN supported_packages sp ON pr.package_name = sp.package_name
                ORDER BY pr.created_at DESC
            """)
            
            requests = cursor.fetchall()
            
            # Get summary statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'under_review' THEN 1 ELSE 0 END) as under_review,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN status = 'implemented' THEN 1 ELSE 0 END) as implemented
                FROM package_requests
            """)
            
            stats = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            print(f"[DEBUG] ✅ Loaded {len(requests)} requests and stats", flush=True)
            
            # Filter requests by status for template compatibility
            pending_requests = [req for req in requests if req['status'] == 'pending']
            approved_requests = [req for req in requests if req['status'] == 'approved']
            rejected_requests = [req for req in requests if req['status'] == 'rejected']
            
            return render_template('admin/packages.html',
                requests=requests,
                pending_requests=pending_requests,
                approved_requests=approved_requests,
                rejected_requests=rejected_requests,
                stats=stats,
                current_timestamp=int(time.time()),
                current_user_email=current_user.email if current_user.is_authenticated else None,
                current_username=current_user.username if current_user.is_authenticated else None,
                current_avatar=current_user.avatar if current_user.is_authenticated else None
            )
            
        except Exception as e:
            print(f"[DEBUG] ❌ Error in admin_packages: {e}", flush=True)
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}", flush=True)
            flash('Error loading admin interface', 'error')
            return redirect(url_for('packages'))
    
    @app.route('/admin/analytics')
    def admin_analytics():
        """Admin analytics dashboard (placeholder)"""
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                flash('🔒 <strong>Bạn cần đăng nhập để truy cập Admin Panel</strong>', 'error')
                return redirect(url_for('index'))
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                flash('🚫 <strong>Không có quyền truy cập!</strong><br>Chỉ admin mới có thể truy cập trang này.', 'error')
                return redirect(url_for('index'))
            
            # TODO: Implement analytics dashboard
            flash('📊 <strong>Analytics Dashboard</strong><br>Tính năng này sẽ được phát triển trong tương lai.', 'info')
            return redirect(url_for('admin_packages_dashboard'))
        except Exception as e:
            print(f"[DEBUG] ❌ Error in admin_analytics: {e}", flush=True)
            flash('Error loading analytics dashboard', 'error')
            return redirect(url_for('packages'))
    
    @app.route('/api/packages/search')
    def api_packages_search():
        """API endpoint for package search"""
        try:
            search_term = request.args.get('q', '').strip().lower()
            package_type = request.args.get('type', '').strip()
            
            packages, _ = get_cached_packages(int(time.time() // 300))
            
            # Filter packages
            filtered_packages = []
            for package in packages:
                # Text search
                if search_term:
                    searchable_text = f"{package['package_name']} {package.get('description', '')}".lower()
                    if search_term not in searchable_text:
                        continue
                
                # Type filter
                if package_type and package['package_type'] != package_type:
                    continue
                
                filtered_packages.append(package)
            
            return jsonify({
                'packages': filtered_packages,
                'total': len(filtered_packages)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error in package search API: {e}")
            return jsonify({'error': 'Search failed'}), 500
    
    @app.route('/api/packages/stats')
    def api_packages_stats():
        """API endpoint for package statistics"""
        try:
            _, stats = get_cached_packages(int(time.time() // 300))
            return jsonify(stats)
            
        except Exception as e:
            current_app.logger.error(f"Error in package stats API: {e}")
            return jsonify({'error': 'Failed to get statistics'}), 500
    
    # Admin routes (require authentication)
    @app.route('/admin/packages')
    def admin_packages():
        """Admin interface for package management"""
        print("[DEBUG] Admin packages page accessed", flush=True)
        # TODO: Add admin authentication check
        # if not is_admin(current_user):
        #     return redirect(url_for('login'))
        
        try:
            conn = get_db_connection()
            if not conn:
                flash('Database connection error', 'error')
                return redirect(url_for('index'))
            
            cursor = conn.cursor(dictionary=True)
            
            # Get pending requests
            print("[DEBUG] Fetching pending package requests...", flush=True)
            cursor.execute("""
                SELECT * FROM package_requests 
                WHERE status IN ('pending', 'under_review')
                ORDER BY 
                    FIELD(priority, 'urgent', 'high', 'medium', 'low'),
                    created_at ASC
            """)
            
            pending_requests = cursor.fetchall()
            print(f"[DEBUG] Found {len(pending_requests)} pending requests", flush=True)
            for req in pending_requests:
                print(f"[DEBUG] Request ID {req['id']}: {req['package_name']} ({req['status']})", flush=True)
            
            # Get recent changelog
            cursor.execute("""
                SELECT * FROM package_changelog
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            recent_changes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('admin/packages.html',
                pending_requests=pending_requests,
                recent_changes=recent_changes
            )
            
        except Exception as e:
            current_app.logger.error(f"Error in admin packages: {e}")
            flash('Error loading admin interface', 'error')
            return redirect(url_for('index'))
    
    @app.route('/api/admin/requests/count')
    def admin_requests_count():
        """Get count of pending package requests for admin dashboard"""
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                return jsonify({'error': 'Unauthorized - Login required'}), 403
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                return jsonify({'error': 'Unauthorized - Admin access only'}), 403
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(dictionary=True)
            
            # Get counts by status
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN status = 'under_review' THEN 1 END) as under_review_count,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
                    COUNT(*) as total_count
                FROM package_requests
            """)
            
            counts = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'counts': {
                    'pending': counts['pending_count'] or 0,
                    'under_review': counts['under_review_count'] or 0,
                    'approved': counts['approved_count'] or 0,
                    'rejected': counts['rejected_count'] or 0,
                    'total': counts['total_count'] or 0
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"Error getting request counts: {e}")
            return jsonify({'error': 'Failed to get counts'}), 500
    
    # =====================================================
    # PHASE 2: ADVANCED FEATURES - API ENDPOINTS
    # =====================================================
    
    @app.route('/api/packages/popular')
    def api_popular_packages():
        """Get most popular packages with usage analytics"""
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(dictionary=True)
            
            # Get popular packages with enhanced statistics
            cursor.execute("""
                SELECT 
                    sp.package_name,
                    sp.package_type,
                    sp.description,
                    sp.usage_count,
                    sp.documentation_url,
                    COUNT(pr.id) as request_count,
                    AVG(CASE WHEN pr.status = 'approved' THEN 1 ELSE 0 END) * 100 as approval_rate
                FROM supported_packages sp
                LEFT JOIN package_requests pr ON sp.package_name = pr.package_name
                WHERE sp.status = 'active' AND sp.usage_count > 0
                GROUP BY sp.id, sp.package_name, sp.package_type, sp.description, sp.usage_count, sp.documentation_url
                ORDER BY sp.usage_count DESC, request_count DESC
                LIMIT 20
            """)
            
            popular_packages = cursor.fetchall()
            
            # Get trending packages (packages with recent usage increases)
            cursor.execute("""
                SELECT 
                    package_name,
                    package_type,
                    usage_count,
                    description
                FROM supported_packages 
                WHERE status = 'active' AND usage_count > 0
                ORDER BY updated_at DESC, usage_count DESC
                LIMIT 10
            """)
            
            trending_packages = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'popular': popular_packages,
                'trending': trending_packages,
                'timestamp': int(time.time())
            })
            
        except Exception as e:
            current_app.logger.error(f"Error in popular packages API: {e}")
            return jsonify({'error': 'Failed to get popular packages'}), 500
    
    @app.route('/api/packages/recommendations/<package_name>')
    def api_package_recommendations(package_name):
        """Get AI-powered package recommendations"""
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(dictionary=True)
            
            # Get package info
            cursor.execute("""
                SELECT package_type, description FROM supported_packages 
                WHERE package_name = %s AND status = 'active'
            """, (package_name,))
            
            base_package = cursor.fetchone()
            if not base_package:
                return jsonify({'error': 'Package not found'}), 404
            
            # Get related packages by type
            cursor.execute("""
                SELECT package_name, description, usage_count
                FROM supported_packages 
                WHERE package_type = %s AND package_name != %s AND status = 'active'
                ORDER BY usage_count DESC
                LIMIT 5
            """, (base_package['package_type'], package_name))
            
            related_by_type = cursor.fetchall()
            
            # Get frequently used together (simple correlation analysis)
            frequently_used_with = []
            if base_package['package_type'] == 'latex_package':
                if package_name in ['amsmath', 'amssymb', 'amsfonts']:
                    frequently_used_with = ['mathtools', 'physics', 'siunitx']
                elif package_name == 'tikz':
                    frequently_used_with = ['pgf', 'xcolor', 'positioning', 'arrows.meta']
                elif package_name == 'pgfplots':
                    frequently_used_with = ['tikz', 'pgf', 'colorbrewer', 'statistics']
            
            # Get alternative packages
            alternatives = []
            if package_name == 'babel':
                alternatives = [{'name': 'polyglossia', 'reason': 'Modern alternative for XeLaTeX/LuaLaTeX'}]
            elif package_name == 'inputenc':
                alternatives = [{'name': 'fontspec', 'reason': 'Better Unicode support with XeLaTeX/LuaLaTeX'}]
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'package': package_name,
                'type': base_package['package_type'],
                'related_by_type': related_by_type,
                'frequently_used_with': frequently_used_with,
                'alternatives': alternatives,
                'dependencies': get_package_dependencies(package_name),
                'conflicts': get_package_conflicts(package_name)
            })
            
        except Exception as e:
            current_app.logger.error(f"Error in package recommendations API: {e}")
            return jsonify({'error': 'Failed to get recommendations'}), 500
    
    @app.route('/api/packages/analytics')
    def api_packages_analytics():
        """Get comprehensive package analytics"""
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(dictionary=True)
            
            # Usage statistics by package type
            cursor.execute("""
                SELECT 
                    package_type,
                    COUNT(*) as total_packages,
                    SUM(usage_count) as total_usage,
                    AVG(usage_count) as avg_usage,
                    MAX(usage_count) as max_usage
                FROM supported_packages 
                WHERE status = 'active'
                GROUP BY package_type
            """)
            
            type_stats = cursor.fetchall()
            
            # Request statistics
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    AVG(DATEDIFF(CURRENT_DATE, created_at)) as avg_age_days
                FROM package_requests
                GROUP BY status
            """)
            
            request_stats = cursor.fetchall()
            
            # Growth statistics (last 30 days)
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as requests_count
                FROM package_requests
                WHERE created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            growth_data = cursor.fetchall()
            
            # Top requested packages
            cursor.execute("""
                SELECT 
                    package_name,
                    COUNT(*) as request_count,
                    AVG(CASE WHEN status IN ('approved', 'implemented') THEN 1 ELSE 0 END) * 100 as approval_rate
                FROM package_requests
                GROUP BY package_name
                HAVING request_count > 1
                ORDER BY request_count DESC
                LIMIT 10
            """)
            
            top_requested = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'type_statistics': type_stats,
                'request_statistics': request_stats,
                'growth_data': growth_data,
                'top_requested': top_requested,
                'generated_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            current_app.logger.error(f"Error in package analytics API: {e}")
            return jsonify({'error': 'Failed to get analytics'}), 500
    
    @app.route('/api/admin/requests/<int:request_id>/status', methods=['POST'])
    def admin_update_request_status(request_id):
        """Update package request status (admin only)"""
        print(f"[DEBUG] Admin update status requested for request_id: {request_id}", flush=True)
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                print("[DEBUG] ❌ User not authenticated", flush=True)
                return jsonify({'error': 'Unauthorized - Login required'}), 403
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                print(f"[DEBUG] ❌ Unauthorized access attempt by: {current_user.email}", flush=True)
                return jsonify({'error': 'Unauthorized - Admin access only'}), 403
            
            data = request.get_json()
            new_status = data.get('status')
            admin_notes = data.get('admin_notes', '')
            
            print(f"[DEBUG] Request data: {data}", flush=True)
            print(f"[DEBUG] New status: {new_status}, Admin notes: {admin_notes}", flush=True)
            
            valid_statuses = ['pending', 'under_review', 'approved', 'rejected', 'implemented']
            if new_status not in valid_statuses:
                print(f"[DEBUG] ❌ Invalid status: {new_status}", flush=True)
                return jsonify({'error': 'Invalid status'}), 400
            
            print("[DEBUG] Attempting database connection...", flush=True)
            conn = get_db_connection()
            if not conn:
                print("[DEBUG] ❌ Database connection failed!", flush=True)
                return jsonify({'error': 'Database connection failed'}), 500
            
            print("[DEBUG] ✅ Database connected, getting request details...", flush=True)
            cursor = conn.cursor(dictionary=True)
            
            # Get request details
            cursor.execute("SELECT * FROM package_requests WHERE id = %s", (request_id,))
            package_request = cursor.fetchone()
            
            if not package_request:
                print(f"[DEBUG] ❌ Request not found for ID: {request_id}", flush=True)
                return jsonify({'error': 'Request not found'}), 404
            
            print(f"[DEBUG] ✅ Found request: {package_request['package_name']}", flush=True)
            
            # Update request status
            cursor.execute("""
                UPDATE package_requests 
                SET status = %s, admin_notes = %s, reviewed_at = CURRENT_TIMESTAMP,
                    reviewed_by_email = %s
                WHERE id = %s
            """, (new_status, admin_notes, 'admin@tikz2svg.com', request_id))
            
            # If approved, add package to supported packages - Updated for simplified schema
            if new_status == 'approved':
                # Default new packages to 'manual' status (need %!<..> in code)
                # Admin can later change to 'active' if they add it to TEX_TEMPLATE
                cursor.execute("""
                    INSERT IGNORE INTO supported_packages 
                    (package_name, status)
                    VALUES (%s, 'manual')
                """, (package_request['package_name'],))
                
                # Clear cache to reflect new package
                clear_package_cache()
            
            # Log to changelog
            print("[DEBUG] Logging status change to changelog...", flush=True)
            changelog_action = 'updated'  # Use valid enum value
            cursor.execute("""
                INSERT INTO package_changelog 
                (package_name, action_type, new_values, changed_by_email, change_reason, request_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                package_request['package_name'],
                changelog_action,
                json.dumps({'status': new_status, 'admin_notes': admin_notes}),
                'admin@tikz2svg.com',
                f'Request {new_status}: {admin_notes}',
                request_id
            ))
            
            print("[DEBUG] Committing database changes...", flush=True)
            conn.commit()
            print("[DEBUG] ✅ Database changes committed successfully!", flush=True)
            
            cursor.close()
            conn.close()
            
            print(f"[DEBUG] 🎉 SUCCESS: Status updated to '{new_status}' for request {request_id}", flush=True)
            return jsonify({
                'success': True,
                'request_id': request_id,
                'new_status': new_status,
                'message': f'Request {new_status} successfully'
            })
            
        except Exception as e:
            print(f"[DEBUG] ❌ EXCEPTION in admin_update_request_status: {e}", flush=True)
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}", flush=True)
            current_app.logger.error(f"Error updating request status: {e}")
            return jsonify({'error': 'Failed to update request status'}), 500
    
    @app.route('/api/admin/requests/<int:request_id>/package-name', methods=['PUT'])
    def admin_update_package_name(request_id):
        """Update package name in a request (admin only) - for correcting user typos"""
        print(f"[DEBUG] Admin update package name requested for request_id: {request_id}", flush=True)
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                print("[DEBUG] ❌ User not authenticated", flush=True)
                return jsonify({'error': 'Unauthorized - Login required'}), 403
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                print(f"[DEBUG] ❌ Unauthorized access attempt by: {current_user.email}", flush=True)
                return jsonify({'error': 'Unauthorized - Admin access only'}), 403
            
            data = request.get_json()
            new_package_name = data.get('package_name', '').strip()
            admin_notes = data.get('admin_notes', '')
            
            print(f"[DEBUG] New package name: '{new_package_name}'", flush=True)
            
            # Validate package name
            if not new_package_name:
                return jsonify({'error': 'Package name cannot be empty'}), 400
            
            # Basic validation: only alphanumeric, dash, underscore, dot
            import re
            if not re.match(r'^[a-zA-Z0-9\-_.]+$', new_package_name):
                return jsonify({'error': 'Invalid package name format'}), 400
            
            conn = get_db_connection()
            if not conn:
                print("[DEBUG] ❌ Database connection failed!", flush=True)
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(dictionary=True)
            
            # Get current request details
            cursor.execute("SELECT * FROM package_requests WHERE id = %s", (request_id,))
            package_request = cursor.fetchone()
            
            if not package_request:
                print(f"[DEBUG] ❌ Request not found for ID: {request_id}", flush=True)
                return jsonify({'error': 'Request not found'}), 404
            
            old_package_name = package_request['package_name']
            
            # Check if package name already exists in supported_packages or other requests
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM supported_packages 
                WHERE package_name = %s
            """, (new_package_name,))
            
            existing_supported = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM package_requests 
                WHERE package_name = %s AND id != %s AND status IN ('pending', 'under_review', 'approved')
            """, (new_package_name, request_id))
            
            existing_requests = cursor.fetchone()['count']
            
            if existing_supported > 0:
                cursor.close()
                conn.close()
                return jsonify({
                    'error': f'Package "{new_package_name}" already exists in supported packages',
                    'suggestion': 'This package is already available. You may reject this request.'
                }), 400
            
            if existing_requests > 0:
                cursor.close()
                conn.close()
                return jsonify({
                    'error': f'Package "{new_package_name}" already has an active request',
                    'suggestion': 'Another request with this name exists. Check for duplicates.'
                }), 400
            
            # Update package name
            cursor.execute("""
                UPDATE package_requests 
                SET package_name = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_package_name, request_id))
            
            # Log to changelog
            cursor.execute("""
                INSERT INTO package_changelog 
                (package_name, action_type, old_values, new_values, changed_by_email, change_reason, request_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                new_package_name,
                'updated',
                json.dumps({'package_name': old_package_name}),
                json.dumps({'package_name': new_package_name}),
                current_user.email,
                admin_notes or f'Admin corrected package name from "{old_package_name}" to "{new_package_name}"',
                request_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[DEBUG] ✅ Package name updated: {old_package_name} → {new_package_name}", flush=True)
            
            return jsonify({
                'success': True,
                'request_id': request_id,
                'old_name': old_package_name,
                'new_name': new_package_name,
                'message': f'Package name updated from "{old_package_name}" to "{new_package_name}"'
            })
            
        except Exception as e:
            print(f"[DEBUG] ❌ EXCEPTION in admin_update_package_name: {e}", flush=True)
            import traceback
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}", flush=True)
            current_app.logger.error(f"Error updating package name: {e}")
            return jsonify({'error': 'Failed to update package name'}), 500
    
    @app.route('/api/admin/packages/bulk-approve', methods=['POST'])
    def admin_bulk_approve():
        """Process multiple package requests simultaneously"""
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                return jsonify({'error': 'Unauthorized - Login required'}), 403
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                return jsonify({'error': 'Unauthorized - Admin access only'}), 403
            
            data = request.get_json()
            request_ids = data.get('request_ids', [])
            
            if not request_ids:
                return jsonify({'error': 'No request IDs provided'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(dictionary=True)
            results = []
            
            for req_id in request_ids:
                try:
                    # Get request details
                    cursor.execute("SELECT * FROM package_requests WHERE id = %s", (req_id,))
                    pkg_request = cursor.fetchone()
                    
                    if not pkg_request:
                        results.append({'request_id': req_id, 'success': False, 'error': 'Request not found'})
                        continue
                    
                    # Update status to approved
                    cursor.execute("""
                        UPDATE package_requests 
                        SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP,
                            reviewed_by_email = %s, admin_notes = %s
                        WHERE id = %s
                    """, ('admin@tikz2svg.com', 'Bulk approved', req_id))
                    
                    # Add to supported packages
                    cursor.execute("""
                        INSERT IGNORE INTO supported_packages 
                        (package_name, package_type, description, documentation_url, status)
                        VALUES (%s, %s, %s, %s, 'active')
                    """, (
                        pkg_request['package_name'],
                        pkg_request['package_type'],
                        pkg_request['description'],
                        pkg_request['documentation_url']
                    ))
                    
                    results.append({'request_id': req_id, 'success': True, 'package_name': pkg_request['package_name']})
                    
                except Exception as e:
                    results.append({'request_id': req_id, 'success': False, 'error': str(e)})
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Clear cache
            clear_package_cache()
            
            successful_count = sum(1 for r in results if r['success'])
            
            return jsonify({
                'success': True,
                'results': results,
                'processed': len(request_ids),
                'successful': successful_count,
                'failed': len(request_ids) - successful_count
            })
            
        except Exception as e:
            current_app.logger.error(f"Error in bulk approve: {e}")
            return jsonify({'error': 'Bulk approval failed'}), 500
    
    @app.route('/api/admin/cache/refresh', methods=['POST'])
    def admin_refresh_cache():
        """Refresh package cache"""
        try:
            # Admin authentication check - Only specific email allowed
            if not current_user.is_authenticated:
                return jsonify({'error': 'Unauthorized - Login required'}), 403
            
            # Hardcoded admin email for security
            ADMIN_EMAIL = 'quochiep0504@gmail.com'
            if current_user.email != ADMIN_EMAIL:
                return jsonify({'error': 'Unauthorized - Admin access only'}), 403
            
            clear_package_cache()
            return jsonify({'success': True, 'message': 'Cache refreshed successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app

# =====================================================
# PHASE 2: ADVANCED UTILITY FUNCTIONS
# =====================================================

def get_package_dependencies(package_name):
    """Get package dependencies for recommendations"""
    dependencies = {
        'tikz': ['pgf'],
        'pgfplots': ['tikz', 'pgf'],
        'circuitikz': ['tikz', 'pgf'],
        'mathtools': ['amsmath'],
        'physics': ['amsmath', 'amssymb'],
        'siunitx': ['xparse'],
        'subcaption': ['caption'],
        'booktabs': ['array'],
        'longtable': ['array']
    }
    return dependencies.get(package_name, [])

def get_package_conflicts(package_name):
    """Get package conflicts for recommendations"""
    conflicts = {
        'inputenc': ['fontspec'],
        'fontenc': ['fontspec'],
        'babel': ['polyglossia'],
        'polyglossia': ['babel'],
        'fontspec': ['inputenc', 'fontenc']
    }
    return conflicts.get(package_name, [])

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def update_package_usage(package_names, package_types=None):
    """Update usage count for packages (call after successful compilation)"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        for package_name in package_names:
            cursor.execute("""
                UPDATE supported_packages 
                SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE package_name = %s AND status = 'active'
            """, (package_name,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Clear cache to reflect usage updates
        clear_package_cache()
        
    except Exception as e:
        current_app.logger.error(f"Error updating package usage: {e}")

def is_admin_user(email):
    """Check if user has admin permissions"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT permission_level FROM admin_permissions 
            WHERE email = %s AND is_active = TRUE
        """, (email,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result and result[0] in ['admin', 'moderator']
        
    except Exception as e:
        current_app.logger.error(f"Error checking admin permissions: {e}")
        return False

# Duplicate function removed - using the one with actual route definitions above
