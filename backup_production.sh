#!/bin/bash
#
# Production Backup Script for Enhanced Whitelist + Resource Limits v2.0
# =======================================================================
#
# Automated backup system for database, application files, logs,
# and configuration with rotation and monitoring.
#
# Usage:
#   chmod +x backup_production.sh
#   ./backup_production.sh [full|database|files|config]
#
# Cron example (daily backups):
#   0 2 * * * /opt/tikz2svg_api/backup_production.sh full

set -euo pipefail

# ================================
# 🎨 CONFIGURATION
# ================================

APP_NAME="tikz2svg_api"
APP_DIR="/opt/${APP_NAME}"
BACKUP_DIR="/opt/backups/${APP_NAME}"
DB_NAME="${DB_NAME:-tikz2svg_production}"
DB_USER="${DB_USER:-tikz2svg_user}"

# Backup retention (days)
DAILY_RETENTION=7
WEEKLY_RETENTION=4
MONTHLY_RETENTION=6

# Backup types
BACKUP_TYPE="${1:-full}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_ONLY=$(date +"%Y%m%d") 

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ================================
# 📝 LOGGING
# ================================

BACKUP_LOG="${BACKUP_DIR}/logs/backup_${DATE_ONLY}.log"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$BACKUP_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$BACKUP_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$BACKUP_LOG"
}

log_step() {
    echo -e "\n${BLUE}[STEP]${NC} $1" | tee -a "$BACKUP_LOG"
    echo "================================" | tee -a "$BACKUP_LOG"
}

# ================================
# 🚀 INITIALIZATION
# ================================

init_backup() {
    log_step "Initializing backup system"
    
    # Create backup directories
    mkdir -p "${BACKUP_DIR}"/{database,files,config,logs}
    mkdir -p "${BACKUP_DIR}/database"/{daily,weekly,monthly}
    mkdir -p "${BACKUP_DIR}/files"/{daily,weekly,monthly}
    
    # Set permissions
    chmod 750 "${BACKUP_DIR}"
    chmod 640 "${BACKUP_LOG}"
    
    log_info "Backup system initialized"
    log_info "Backup directory: ${BACKUP_DIR}"
    log_info "Log file: ${BACKUP_LOG}"
}

# ================================
# 🗄️ DATABASE BACKUP
# ================================

backup_database() {
    log_step "Backing up database"
    
    local backup_file="${BACKUP_DIR}/database/daily/tikz2svg_db_${TIMESTAMP}.sql"
    local backup_file_compressed="${backup_file}.gz"
    
    # Read database password from .env
    if [[ -f "${APP_DIR}/.env" ]]; then
        DB_PASSWORD=$(grep "^DB_PASSWORD=" "${APP_DIR}/.env" | cut -d'=' -f2)
    else
        log_error "Cannot find .env file with database credentials"
        return 1
    fi
    
    log_info "Creating database dump..."
    
    # Create database backup with comprehensive options
    mysqldump \
        --user="${DB_USER}" \
        --password="${DB_PASSWORD}" \
        --host=localhost \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --compress \
        --lock-tables=false \
        --add-drop-table \
        --add-locks \
        --create-options \
        --disable-keys \
        --extended-insert \
        --quick \
        --set-charset \
        "${DB_NAME}" > "${backup_file}"
    
    # Compress backup
    log_info "Compressing database backup..."
    gzip "${backup_file}"
    
    # Verify backup
    if [[ -f "${backup_file_compressed}" ]]; then
        local size=$(du -h "${backup_file_compressed}" | cut -f1)
        log_info "✅ Database backup completed: ${backup_file_compressed} (${size})"
    else
        log_error "❌ Database backup failed"
        return 1
    fi
    
    # Create weekly/monthly copies if needed
    create_weekly_monthly_copies "database" "${backup_file_compressed}"
}

# ================================
# 📁 FILES BACKUP
# ================================

backup_files() {
    log_step "Backing up application files"
    
    local backup_file="${BACKUP_DIR}/files/daily/tikz2svg_files_${TIMESTAMP}.tar.gz"
    
    log_info "Creating files archive..."
    
    # Create comprehensive file backup
    tar -czf "${backup_file}" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='*.log' \
        --exclude='venv' \
        --exclude='node_modules' \
        --exclude='temp_svg/*.svg' \
        -C "${APP_DIR}" \
        source \
        static/svg_files \
        .env
    
    # Verify backup
    if [[ -f "${backup_file}" ]]; then
        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "✅ Files backup completed: ${backup_file} (${size})"
    else
        log_error "❌ Files backup failed"
        return 1
    fi
    
    # Create weekly/monthly copies if needed
    create_weekly_monthly_copies "files" "${backup_file}"
}

# ================================
# ⚙️ CONFIGURATION BACKUP
# ================================

backup_config() {
    log_step "Backing up system configuration"
    
    local backup_file="${BACKUP_DIR}/config/system_config_${TIMESTAMP}.tar.gz"
    
    log_info "Creating configuration archive..."
    
    # Backup system configurations
    tar -czf "${backup_file}" \
        -C / \
        --exclude='/etc/ssl/private' \
        etc/nginx/sites-available/tikz2svg \
        etc/systemd/system/tikz2svg.service \
        etc/fail2ban/jail.local \
        etc/mysql/mariadb.conf.d/99-tikz2svg.cnf \
        etc/logrotate.d/tikz2svg \
        usr/local/bin/tikz2svg-monitor \
        etc/cron.daily/tikz2svg-log-cleanup \
        2>/dev/null || true
    
    # Verify backup
    if [[ -f "${backup_file}" ]]; then
        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "✅ Configuration backup completed: ${backup_file} (${size})"
    else
        log_error "❌ Configuration backup failed"
        return 1
    fi
}

# ================================
# 📊 LOGS BACKUP
# ================================

backup_logs() {
    log_step "Backing up application logs"
    
    local backup_file="${BACKUP_DIR}/logs/tikz2svg_logs_${TIMESTAMP}.tar.gz"
    
    log_info "Creating logs archive..."
    
    # Backup logs (last 30 days)
    find "${APP_DIR}/logs" -name "*.log" -mtime -30 -type f | \
        tar -czf "${backup_file}" -T -
    
    # Include system logs
    tar -rf "${backup_file}" \
        /var/log/nginx/access.log \
        /var/log/nginx/error.log \
        /var/log/fail2ban.log \
        2>/dev/null || true
    
    # Compress final archive
    gzip "${backup_file}" 2>/dev/null || true
    
    if [[ -f "${backup_file}" ]]; then
        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "✅ Logs backup completed: ${backup_file} (${size})"
    else
        log_warn "⚠️ Logs backup may be incomplete"
    fi
}

# ================================
# 📅 WEEKLY/MONTHLY COPIES
# ================================

create_weekly_monthly_copies() {
    local backup_type=$1
    local source_file=$2
    local day_of_week=$(date +%u)  # 1=Monday, 7=Sunday
    local day_of_month=$(date +%d)
    
    # Weekly backup (every Sunday)
    if [[ $day_of_week -eq 7 ]]; then
        local weekly_file="${BACKUP_DIR}/${backup_type}/weekly/$(basename "${source_file}" | sed "s/${TIMESTAMP}/weekly_${DATE_ONLY}/")"
        cp "${source_file}" "${weekly_file}"
        log_info "📅 Weekly copy created: ${weekly_file}"
    fi
    
    # Monthly backup (first day of month)
    if [[ $day_of_month -eq 01 ]]; then
        local monthly_file="${BACKUP_DIR}/${backup_type}/monthly/$(basename "${source_file}" | sed "s/${TIMESTAMP}/monthly_${DATE_ONLY}/")"
        cp "${source_file}" "${monthly_file}"
        log_info "📅 Monthly copy created: ${monthly_file}"
    fi
}

# ================================
# 🧹 CLEANUP OLD BACKUPS
# ================================

cleanup_old_backups() {
    log_step "Cleaning up old backups"
    
    # Daily backups cleanup
    log_info "Cleaning daily backups older than ${DAILY_RETENTION} days..."
    find "${BACKUP_DIR}"/*/daily -name "*.gz" -mtime +${DAILY_RETENTION} -delete 2>/dev/null || true
    find "${BACKUP_DIR}"/*/daily -name "*.tar.gz" -mtime +${DAILY_RETENTION} -delete 2>/dev/null || true
    
    # Weekly backups cleanup
    log_info "Cleaning weekly backups older than ${WEEKLY_RETENTION} weeks..."
    find "${BACKUP_DIR}"/*/weekly -name "*weekly*" -mtime +$((WEEKLY_RETENTION * 7)) -delete 2>/dev/null || true
    
    # Monthly backups cleanup
    log_info "Cleaning monthly backups older than ${MONTHLY_RETENTION} months..."
    find "${BACKUP_DIR}"/*/monthly -name "*monthly*" -mtime +$((MONTHLY_RETENTION * 30)) -delete 2>/dev/null || true
    
    # Log files cleanup
    log_info "Cleaning old log files..."
    find "${BACKUP_DIR}/logs" -name "backup_*.log" -mtime +30 -delete 2>/dev/null || true
    
    log_info "✅ Cleanup completed"
}

# ================================
# 📊 BACKUP VERIFICATION
# ================================

verify_backups() {
    log_step "Verifying backup integrity"
    
    local errors=0
    
    # Check recent database backup
    local latest_db_backup=$(find "${BACKUP_DIR}/database/daily" -name "*.sql.gz" -mtime -1 | head -1)
    if [[ -n "$latest_db_backup" ]]; then
        if gzip -t "$latest_db_backup" 2>/dev/null; then
            log_info "✅ Database backup integrity verified"
        else
            log_error "❌ Database backup corrupted: $latest_db_backup"
            ((errors++))
        fi
    else
        log_warn "⚠️ No recent database backup found"
        ((errors++))
    fi
    
    # Check recent files backup
    local latest_files_backup=$(find "${BACKUP_DIR}/files/daily" -name "*.tar.gz" -mtime -1 | head -1)
    if [[ -n "$latest_files_backup" ]]; then
        if tar -tf "$latest_files_backup" >/dev/null 2>&1; then
            log_info "✅ Files backup integrity verified"
        else
            log_error "❌ Files backup corrupted: $latest_files_backup"
            ((errors++))
        fi
    else
        log_warn "⚠️ No recent files backup found"
        ((errors++))
    fi
    
    return $errors
}

# ================================
# 📈 BACKUP STATISTICS
# ================================

show_backup_stats() {
    log_step "Backup statistics"
    
    # Count backups by type
    local db_daily=$(find "${BACKUP_DIR}/database/daily" -name "*.gz" 2>/dev/null | wc -l)
    local db_weekly=$(find "${BACKUP_DIR}/database/weekly" -name "*.gz" 2>/dev/null | wc -l)
    local db_monthly=$(find "${BACKUP_DIR}/database/monthly" -name "*.gz" 2>/dev/null | wc -l)
    
    local files_daily=$(find "${BACKUP_DIR}/files/daily" -name "*.tar.gz" 2>/dev/null | wc -l)
    local files_weekly=$(find "${BACKUP_DIR}/files/weekly" -name "*.tar.gz" 2>/dev/null | wc -l)
    local files_monthly=$(find "${BACKUP_DIR}/files/monthly" -name "*.tar.gz" 2>/dev/null | wc -l)
    
    # Calculate total size
    local total_size=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
    
    log_info "Database backups: ${db_daily} daily, ${db_weekly} weekly, ${db_monthly} monthly"
    log_info "Files backups: ${files_daily} daily, ${files_weekly} weekly, ${files_monthly} monthly"
    log_info "Total backup size: ${total_size}"
    
    # Show disk space
    local backup_disk=$(df -h "${BACKUP_DIR}" | awk 'NR==2 {print $4}')
    log_info "Available disk space: ${backup_disk}"
}

# ================================
# 📧 NOTIFICATION SYSTEM
# ================================

send_notification() {
    local status=$1
    local message=$2
    
    # Log notification
    if [[ "$status" == "success" ]]; then
        log_info "📧 Backup completed successfully"
    else
        log_error "📧 Backup failed: $message"
    fi
    
    # Could implement email notifications here
    # echo "$message" | mail -s "TikZ2SVG Backup $status" admin@domain.com
}

# ================================
# 🚀 MAIN BACKUP FUNCTIONS
# ================================

backup_full() {
    log_info "Starting full backup (database + files + config + logs)"
    
    local errors=0
    
    backup_database || ((errors++))
    backup_files || ((errors++))
    backup_config || ((errors++))
    backup_logs || ((errors++))
    
    cleanup_old_backups
    verify_backups || ((errors++))
    show_backup_stats
    
    if [[ $errors -eq 0 ]]; then
        send_notification "success" "Full backup completed successfully"
        return 0
    else
        send_notification "error" "Full backup completed with $errors errors"
        return 1
    fi
}

# ================================
# 🎯 MAIN EXECUTION
# ================================

main() {
    log_info "TikZ2SVG Enhanced Whitelist + Resource Limits v2.0 - Backup System"
    log_info "Backup type: ${BACKUP_TYPE}"
    log_info "Timestamp: ${TIMESTAMP}"
    
    # Initialize backup system
    init_backup
    
    # Execute backup based on type
    case "${BACKUP_TYPE}" in
        "full")
            backup_full
            ;;
        "database")
            backup_database
            cleanup_old_backups
            show_backup_stats
            ;;
        "files")
            backup_files
            cleanup_old_backups
            show_backup_stats
            ;;
        "config")
            backup_config
            show_backup_stats
            ;;
        "logs")
            backup_logs
            show_backup_stats
            ;;
        *)
            log_error "Invalid backup type: ${BACKUP_TYPE}"
            log_info "Valid types: full, database, files, config, logs"
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "✅ Backup operation completed successfully"
    else
        log_error "❌ Backup operation completed with errors"
    fi
    
    log_info "Backup log: ${BACKUP_LOG}"
    
    exit $exit_code
}

# Check if running as root or tikz2svg user
if [[ $EUID -ne 0 ]] && [[ "$(whoami)" != "tikz2svg" ]]; then
    echo "This script should be run as root or tikz2svg user"
    exit 1
fi

# Run main function
main "$@"
