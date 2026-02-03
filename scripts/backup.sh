#!/bin/bash

# Hungwetips Backup Script
# Backs up media files, PostgreSQL database, and .env file to Google Drive

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_DIR/backup.log"
RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive}"
RCLONE_PATH="${RCLONE_PATH:-HungwetipsBackups}"
KEEP_LOCAL_BACKUPS="${KEEP_LOCAL_BACKUPS:-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    
    # Check if rclone is installed
    if ! command -v rclone &> /dev/null; then
        log_error "rclone is not installed. Install it with: curl https://rclone.org/install.sh | sudo bash"
        exit 1
    fi
    
    # Check if rclone remote is configured
    if ! rclone listremotes | grep -q "^${RCLONE_REMOTE}:$"; then
        log_error "rclone remote '${RCLONE_REMOTE}' is not configured. Run: rclone config"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_error ".env file not found at $PROJECT_DIR/.env"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Load environment variables from .env (only vars needed for backup)
# Uses safe extraction to avoid syntax errors from special chars in other vars (e.g. DJANGO_SECRET_KEY)
load_env() {
    log "Loading environment variables from .env..."
    
    while IFS= read -r line; do
        [[ "$line" =~ ^# ]] && continue
        [[ -z "$line" ]] && continue
        key="${line%%=*}"
        value="${line#*=}"
        case "$key" in
            POSTGRES_USER)  export POSTGRES_USER="$value" ;;
            POSTGRES_DB)    export POSTGRES_DB="$value" ;;
            POSTGRES_PASSWORD) export POSTGRES_PASSWORD="$value" ;;
        esac
    done < "$PROJECT_DIR/.env"
    
    # Check required variables
    if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
        log_error "Required environment variables (POSTGRES_USER, POSTGRES_DB) not found in .env"
        exit 1
    fi
    
    log_success "Environment variables loaded"
}

# Create backup directory structure (sets BACKUP_DIR and BACKUP_NAME globally)
create_backup_dir() {
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    BACKUP_NAME="hungwetips_backup_${TIMESTAMP}"
    TEMP_DIR=$(mktemp -d)
    BACKUP_DIR="$TEMP_DIR/backup"
    
    mkdir -p "$BACKUP_DIR"
    log "Created temporary backup directory: $BACKUP_DIR"
}

# Backup media files
backup_media() {
    local backup_dir=$1
    mkdir -p "$backup_dir/media"
    log "Backing up media files..."
    
    # Try to copy from container first
    if docker ps --format '{{.Names}}' | grep -q "^hungwetips_web$"; then
        log "Copying media from hungwetips_web container..."
        if docker cp hungwetips_web:/app/media/. "$backup_dir/media/" 2>/dev/null; then
            log_success "Media files backed up from container"
            return 0
        else
            log_warning "Failed to copy from container, trying volume method..."
        fi
    else
        log_warning "Container hungwetips_web is not running, trying volume method..."
    fi
    
    # Fallback: extract from volume directly
    # Try to find the media volume (Docker Compose prefixes with project name)
    log "Searching for media volume..."
    VOLUME_NAME=$(docker volume ls --format "{{.Name}}" | grep -E "(hungwetips|hungwetips-api).*media" | head -n 1)
    
    if [ -z "$VOLUME_NAME" ]; then
        # Try common volume name patterns
        for pattern in "hungwetips-api_hungwetips_media" "hungwetips_hungwetips_media" "hungwetips_media"; do
            if docker volume inspect "$pattern" > /dev/null 2>&1; then
                VOLUME_NAME="$pattern"
                break
            fi
        done
    fi
    
    if [ -n "$VOLUME_NAME" ]; then
        log "Found media volume: $VOLUME_NAME"
        log "Extracting media from Docker volume..."
        if docker run --rm \
            -v "$VOLUME_NAME":/media:ro \
            alpine \
            sh -c "cd /media && tar -cf - ." 2>> "$LOG_FILE" | tar -xf - -C "$backup_dir/media/" 2>> "$LOG_FILE"; then
            log_success "Media files backed up from volume"
            return 0
        else
            log_error "Failed to extract media from volume (check $LOG_FILE for details)"
        fi
    else
        log_error "Could not find media volume. Available volumes:"
        docker volume ls --format "{{.Name}}" | grep -i hungwetips || log "  (none found)"
    fi
    
    log_error "Failed to backup media files"
    return 1
}

# Backup PostgreSQL database
backup_database() {
    local backup_dir=$1
    log "Backing up PostgreSQL database..."
    
    # Check if database container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^hungwetips_db$"; then
        log_error "Database container hungwetips_db is not running"
        return 1
    fi
    
    # Create database dump
    if docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
        pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F c > "$backup_dir/data_backup.dump" 2>/dev/null; then
        # Check if dump file was created and has content
        if [ -f "$backup_dir/data_backup.dump" ] && [ -s "$backup_dir/data_backup.dump" ]; then
            DUMP_SIZE=$(du -h "$backup_dir/data_backup.dump" | cut -f1)
            log_success "Database backed up successfully (size: $DUMP_SIZE)"
            return 0
        else
            log_error "Database dump file is empty or not created"
            return 1
        fi
    else
        log_error "Failed to create database dump"
        return 1
    fi
}

# Backup .env file
backup_env() {
    local backup_dir=$1
    log "Backing up .env file..."
    
    if cp "$PROJECT_DIR/.env" "$backup_dir/.env"; then
        log_success ".env file backed up"
        return 0
    else
        log_error "Failed to backup .env file"
        return 1
    fi
}

# Create zip archive (returns zip file path)
# Uses Docker alpine to avoid requiring zip on host
create_zip() {
    local backup_dir=$1
    local backup_name=$2
    local zip_file="$PROJECT_DIR/${backup_name}.zip"
    local backup_parent="$(dirname "$backup_dir")"
    local backup_folder="$(basename "$backup_dir")"
    
    log "Creating zip archive..."
    
    if docker run --rm \
        -v "$backup_parent":/src:ro \
        -v "$PROJECT_DIR":/out \
        alpine sh -c "apk add --no-cache zip > /dev/null 2>&1 && cd /src && find $backup_folder -print | zip -q /out/${backup_name}.zip -@"; then
        ZIP_SIZE=$(du -h "$zip_file" | cut -f1)
        log_success "Zip archive created: ${backup_name}.zip (size: $ZIP_SIZE)"
        echo "$zip_file"
        return 0
    else
        log_error "Failed to create zip archive"
        return 1
    fi
}

# Upload to Google Drive
upload_to_gdrive() {
    local zip_file=$1
    
    log "Uploading backup to Google Drive..."
    
    if rclone copy "$zip_file" "${RCLONE_REMOTE}:${RCLONE_PATH}/" --progress 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Backup uploaded to Google Drive: ${RCLONE_REMOTE}:${RCLONE_PATH}/$(basename "$zip_file")"
        return 0
    else
        log_error "Failed to upload backup to Google Drive"
        return 1
    fi
}

# Cleanup old local backups
cleanup_local_backups() {
    log "Cleaning up old local backups (keeping last $KEEP_LOCAL_BACKUPS)..."
    
    # Find and sort backup files, keep only the most recent ones
    cd "$PROJECT_DIR"
    local backup_files=$(ls -t hungwetips_backup_*.zip 2>/dev/null | tail -n +$((KEEP_LOCAL_BACKUPS + 1)))
    
    if [ -n "$backup_files" ]; then
        echo "$backup_files" | while read -r file; do
            if [ -f "$file" ]; then
                rm -f "$file"
                log "Removed old backup: $file"
            fi
        done
    fi
    
    log_success "Local cleanup completed"
}

# Cleanup old Google Drive backups (keep only latest 2)
cleanup_gdrive_backups() {
    log "Cleaning up old Google Drive backups (keeping last 2)..."
    
    # List all backup files (rclone lsf lists files, filenames include timestamp so sort works)
    local backup_files=$(rclone lsf "${RCLONE_REMOTE}:${RCLONE_PATH}/" 2>/dev/null | grep "^hungwetips_backup_.*\.zip$" | sort -r)
    
    if [ -z "$backup_files" ]; then
        log_warning "No backup files found in Google Drive"
        return 0
    fi
    
    # Count total backups
    local total_count=$(echo "$backup_files" | grep -c . || echo "0")
    
    if [ "$total_count" -le 2 ]; then
        log "Only $total_count backup(s) in Google Drive, no cleanup needed"
        return 0
    fi
    
    # Get files to delete (skip first 2, delete the rest)
    local files_to_delete=$(echo "$backup_files" | tail -n +3)
    
    if [ -n "$files_to_delete" ]; then
        echo "$files_to_delete" | while IFS= read -r file; do
            if [ -n "$file" ]; then
                log "Deleting old backup from Google Drive: $file"
                if rclone deletefile "${RCLONE_REMOTE}:${RCLONE_PATH}/$file" 2>&1 | tee -a "$LOG_FILE"; then
                    log "Deleted: $file"
                else
                    log_warning "Failed to delete $file"
                fi
            fi
        done
        log_success "Google Drive cleanup completed"
    else
        log_success "No old backups to delete"
    fi
}

# Main backup function
main() {
    log "=========================================="
    log "Starting Hungwetips backup process"
    log "=========================================="
    
    check_prerequisites
    load_env
    
    # Create backup directory
    create_backup_dir
    
    # Perform backups
    MEDIA_SUCCESS=false
    DB_SUCCESS=false
    ENV_SUCCESS=false
    
    if backup_media "$BACKUP_DIR"; then
        MEDIA_SUCCESS=true
    fi
    
    if backup_database "$BACKUP_DIR"; then
        DB_SUCCESS=true
    fi
    
    if backup_env "$BACKUP_DIR"; then
        ENV_SUCCESS=true
    fi
    
    # Check if at least one backup succeeded
    if [ "$MEDIA_SUCCESS" = false ] && [ "$DB_SUCCESS" = false ] && [ "$ENV_SUCCESS" = false ]; then
        log_error "All backup operations failed"
        rm -rf "$(dirname "$BACKUP_DIR")"
        exit 1
    fi
    
    # Create zip archive (capture only last line - the path)
    ZIP_FILE=$(create_zip "$BACKUP_DIR" "$BACKUP_NAME" | tail -n 1)
    if [ -z "$ZIP_FILE" ] || [ ! -f "$ZIP_FILE" ]; then
        log_error "Failed to create zip archive"
        rm -rf "$(dirname "$BACKUP_DIR")"
        exit 1
    fi
    
    # Upload to Google Drive
    if upload_to_gdrive "$ZIP_FILE"; then
        # Cleanup old Google Drive backups after successful upload
        cleanup_gdrive_backups
    else
        log_warning "Backup created locally but upload to Google Drive failed"
        log_warning "Local backup available at: $ZIP_FILE"
    fi
    
    # Cleanup temp directory
    rm -rf "$(dirname "$BACKUP_DIR")"
    log "Temporary files cleaned up"
    
    # Cleanup old local backups
    cleanup_local_backups
    
    log "=========================================="
    log_success "Backup process completed successfully"
    log "Backup file: ${BACKUP_NAME}.zip"
    log "=========================================="
}

# Run main function
main "$@"
