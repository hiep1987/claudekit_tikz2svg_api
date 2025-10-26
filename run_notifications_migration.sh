#!/bin/bash

# ================================================================
# Notifications System - Migration Runner
# ================================================================
# Usage:
#   Local:  ./run_notifications_migration.sh local
#   VPS:    ./run_notifications_migration.sh vps
# ================================================================

set -e  # Exit on error

MIGRATION_FILE="migrations/create_notifications_table.sql"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Notifications System - Database Migration${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}ERROR: Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

# Determine environment
ENV=${1:-local}

if [ "$ENV" = "local" ]; then
    DB_NAME="tikz2svg_local"
    echo -e "${YELLOW}Environment: LOCAL${NC}"
elif [ "$ENV" = "vps" ] || [ "$ENV" = "production" ]; then
    DB_NAME="tikz2svg_production"
    echo -e "${YELLOW}Environment: PRODUCTION (VPS)${NC}"
    echo -e "${RED}⚠️  WARNING: You are about to modify PRODUCTION database!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Migration cancelled.${NC}"
        exit 0
    fi
else
    echo -e "${RED}ERROR: Invalid environment. Use 'local' or 'vps'${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Database: ${DB_NAME}${NC}"
echo ""

# Create backup before migration
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/pre_notifications_${ENV}_${TIMESTAMP}.sql"

echo -e "${YELLOW}Step 1: Creating backup...${NC}"
echo "Backup file: $BACKUP_FILE"

mysqldump -u root -p "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup created successfully${NC}"
else
    echo -e "${RED}❌ Backup failed. Migration aborted.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Running migration...${NC}"

# Run migration
mysql -u root -p "$DB_NAME" < "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration completed successfully${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    echo -e "${YELLOW}You can restore from backup: $BACKUP_FILE${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Verifying migration...${NC}"

# Verify table exists
mysql -u root -p -e "USE $DB_NAME; DESCRIBE notifications;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Table 'notifications' verified${NC}"
    
    # Show table info
    echo ""
    echo -e "${BLUE}Table structure:${NC}"
    mysql -u root -p -e "USE $DB_NAME; DESCRIBE notifications;"
    
    echo ""
    echo -e "${BLUE}Indexes:${NC}"
    mysql -u root -p -e "USE $DB_NAME; SHOW INDEXES FROM notifications;"
else
    echo -e "${RED}❌ Table verification failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Migration completed successfully! 🎉${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Backup location: ${BLUE}$BACKUP_FILE${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Implement NotificationService (notification_service.py)"
echo "2. Add API endpoints to app.py"
echo "3. Update trigger points (like, comment, follow)"
echo "4. Add bell icon to navigation"
echo ""

