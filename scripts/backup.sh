#!/bin/bash

# LifeMetrics Backup Script
# Creates encrypted backups of all data

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lifemetrics_backup_${TIMESTAMP}"

echo "======================================"
echo "LifeMetrics Backup Script"
echo "======================================"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_NAME"
echo ""

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec lifemetrics-postgres pg_dump -U lifemetrics_user lifemetrics > "$BACKUP_DIR/${BACKUP_NAME}_postgres.sql"
echo "✓ PostgreSQL backup complete"

# Backup MinIO data
echo "Backing up MinIO data..."
tar -czf "$BACKUP_DIR/${BACKUP_NAME}_minio.tar.gz" -C ./data minio 2>/dev/null || echo "⚠ MinIO data directory not found"
echo "✓ MinIO backup complete"

# Backup .env file
echo "Backing up configuration..."
cp .env "$BACKUP_DIR/${BACKUP_NAME}_env" 2>/dev/null || echo "⚠ .env file not found"
echo "✓ Configuration backup complete"

# Create a combined archive
echo "Creating combined archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"_*
rm -f "${BACKUP_NAME}"_*
cd ..

# Encrypt backup (optional, requires gpg)
if command -v gpg &> /dev/null; then
    echo ""
    read -p "Encrypt backup with GPG? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gpg -c "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        rm "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        echo "✓ Backup encrypted: ${BACKUP_NAME}.tar.gz.gpg"
    fi
fi

echo ""
echo "======================================"
echo "Backup Complete!"
echo "======================================"
echo ""
echo "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""
echo "To restore from backup:"
echo "  ./scripts/restore.sh $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo ""
