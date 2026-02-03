#!/bin/bash

# Hungwetips Restore Script
# Restores media files, PostgreSQL database, and .env file from Google Drive backup

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive}"
RCLONE_PATH="${RCLONE_PATH:-HungwetipsBackups}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Show usage
usage() {
    log_error "Missing argument. Specify which backup to restore."
    echo ""
    echo "Usage: $0 [backup_filename|latest]"
    echo ""
    echo "Examples:"
    echo "  $0 latest                                    # Restore most recent backup"
    echo "  $0 hungwetips_backup_20240202_020000.zip    # Restore specific backup"
    exit 1
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
    
    log_success "All prerequisites met"
}

# Get backup filename
get_backup_filename() {
    local arg=$1
    
    if [ -z "$arg" ]; then
        usage
        return 1
    fi
    
    if [ "$arg" = "latest" ]; then
        log "Finding latest backup in Google Drive..." >&2
        
        # Try listing from configured path first, then root (for root_folder_id config)
        local file_list=""
        local list_path="${RCLONE_REMOTE}:"
        [ -n "$RCLONE_PATH" ] && list_path="${RCLONE_REMOTE}:${RCLONE_PATH}/"
        
        file_list=$(rclone lsf "$list_path" 2>/dev/null) || true
        if [ -z "$file_list" ] && [ -n "$RCLONE_PATH" ]; then
            log "Trying root path (in case root_folder_id points to backup folder)..." >&2
            file_list=$(rclone lsf "${RCLONE_REMOTE}:" 2>/dev/null) || true
        fi
        
        BACKUP_FILE=$(echo "$file_list" | grep "^hungwetips_backup_.*\.zip$" | sort -r | head -n 1)
        
        if [ -z "$BACKUP_FILE" ]; then
            log_error "No backup files found in Google Drive" >&2
            log "Tried paths: $list_path and ${RCLONE_REMOTE}:" >&2
            log "Run: rclone lsf ${RCLONE_REMOTE}: or rclone ls ${RCLONE_REMOTE}: to list files" >&2
            return 1
        fi
        
        log_success "Found latest backup: $BACKUP_FILE" >&2
        echo "$BACKUP_FILE"
    else
        # Validate filename format
        if [[ ! "$arg" =~ ^hungwetips_backup_.*\.zip$ ]]; then
            log_warning "Filename doesn't match expected pattern: hungwetips_backup_*.zip" >&2
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
        echo "$arg"
    fi
}

# Download backup from Google Drive (only echoes file path to stdout for capture)
download_backup() {
    local backup_file=$1
    local local_file="$PROJECT_DIR/$backup_file"
    
    log "Downloading backup from Google Drive..." >&2
    
    # Ensure destination directory exists
    mkdir -p "$PROJECT_DIR"
    
    # Build remote path - try configured path first, then root
    local remote_path=""
    if [ -n "$RCLONE_PATH" ]; then
        remote_path="${RCLONE_REMOTE}:${RCLONE_PATH}/$backup_file"
    else
        remote_path="${RCLONE_REMOTE}:$backup_file"
    fi
    
    # Redirect rclone output to stderr so it isn't captured by $(...)
    if rclone copyto "$remote_path" "$local_file" --progress 1>&2; then
        if [ -f "$local_file" ]; then
            FILE_SIZE=$(du -h "$local_file" | cut -f1)
            log_success "Backup downloaded: $backup_file (size: $FILE_SIZE)" >&2
            echo "$local_file"
            return 0
        fi
    fi
    
    # Fallback: try root path (when root_folder_id points to HungwetipsBackups)
    if [ -n "$RCLONE_PATH" ]; then
        log "Trying root path..." >&2
        remote_path="${RCLONE_REMOTE}:$backup_file"
        if rclone copyto "$remote_path" "$local_file" --progress 1>&2; then
            if [ -f "$local_file" ]; then
                FILE_SIZE=$(du -h "$local_file" | cut -f1)
                log_success "Backup downloaded: $backup_file (size: $FILE_SIZE)" >&2
                echo "$local_file"
                return 0
            fi
        fi
    fi
    
    log_error "Failed to download backup from Google Drive" >&2
    log_error "Run: rclone ls ${RCLONE_REMOTE}: to verify files exist" >&2
    return 1
}

# Extract backup archive (uses Docker alpine to avoid requiring unzip on host)
# Only echoes backup dir path to stdout for capture
extract_backup() {
    local zip_file=$1
    local extract_dir=$(mktemp -d)
    
    log "Extracting backup archive..." >&2
    
    if docker run --rm \
        -v "$zip_file":/backup.zip:ro \
        -v "$extract_dir":/out \
        alpine sh -c "apk add --no-cache unzip > /dev/null 2>&1 && unzip -q /backup.zip -d /out"; then
        BACKUP_DIR="$extract_dir/backup"
        if [ -d "$BACKUP_DIR" ]; then
            log_success "Backup extracted to: $BACKUP_DIR" >&2
            echo "$BACKUP_DIR"
            return 0
        else
            log_error "Backup directory not found in archive (expected 'backup/' folder)" >&2
            rm -rf "$extract_dir"
            return 1
        fi
    else
        log_error "Failed to extract backup archive" >&2
        rm -rf "$extract_dir"
        return 1
    fi
}

# Restore media files
restore_media() {
    local backup_dir=$1
    
    log "Restoring media files..."
    
    if [ ! -d "$backup_dir/media" ]; then
        log_warning "Media directory not found in backup, skipping..."
        return 0
    fi
    
    # Check if web container is running
    if docker ps --format '{{.Names}}' | grep -q "^hungwetips_web$"; then
        log "Copying media files to hungwetips_web container..."
        if docker cp "$backup_dir/media/." hungwetips_web:/app/media/; then
            log_success "Media files restored to container"
            return 0
        else
            log_error "Failed to restore media files to container"
            return 1
        fi
    else
        log_warning "Container hungwetips_web is not running"
        log_warning "Media files will be restored when container starts (if volume is mounted)"
        return 0
    fi
}

# Load environment variables from .env (only vars needed for restore)
# Uses safe extraction to avoid syntax errors from special chars in other vars (e.g. DJANGO_SECRET_KEY)
load_env() {
    log "Loading environment variables from .env..."
    
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_error ".env file not found at $PROJECT_DIR/.env"
        return 1
    fi
    
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
        return 1
    fi
    
    log_success "Environment variables loaded"
}

# Restore database
restore_database() {
    local backup_dir=$1
    
    log "Restoring PostgreSQL database..."
    
    if [ ! -f "$backup_dir/data_backup.dump" ]; then
        log_warning "Database dump file not found in backup, skipping..."
        return 0
    fi
    
    # Check if database container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^hungwetips_db$"; then
        log_error "Database container hungwetips_db is not running"
        return 1
    fi
    
    # Drop and recreate database
    log "Dropping existing database..."
    docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
        psql -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" postgres || true
    
    log "Creating new database..."
    docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
        psql -U "$POSTGRES_USER" -c "CREATE DATABASE ${POSTGRES_DB};" postgres
    
    # Restore database
    log "Restoring database from dump..."
    if docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T db \
        pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl < "$backup_dir/data_backup.dump"; then
        log_success "Database restored successfully"
        return 0
    else
        log_error "Failed to restore database"
        return 1
    fi
}

# Restore .env file
restore_env() {
    local backup_dir=$1
    
    log "Restoring .env file..."
    
    if [ ! -f "$backup_dir/.env" ]; then
        log_warning ".env file not found in backup, skipping..."
        return 0
    fi
    
    # Confirm .env restore (destructive operation)
    log_warning "This will OVERWRITE the existing .env file"
    if [ -f "$PROJECT_DIR/.env" ]; then
        log_warning "Current .env will be backed up to .env.backup"
        cp "$PROJECT_DIR/.env" "$PROJECT_DIR/.env.backup"
    fi
    
    read -p "Are you sure you want to continue? (yes/NO): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log ".env restore cancelled"
        return 1
    fi
    
    if cp "$backup_dir/.env" "$PROJECT_DIR/.env"; then
        log_success ".env file restored"
        log "Previous .env backed up to .env.backup"
        return 0
    else
        log_error "Failed to restore .env file"
        return 1
    fi
}

# Main restore function
main() {
    log "=========================================="
    log "Starting Hungwetips restore process"
    log "=========================================="
    
    check_prerequisites
    
    # Get backup filename
    set +e  # Temporarily disable exit on error to handle function return
    BACKUP_FILE=$(get_backup_filename "$1")
    local get_file_result=$?
    set -e  # Re-enable exit on error
    
    if [ $get_file_result -ne 0 ] || [ -z "$BACKUP_FILE" ]; then
        log_error "Failed to get backup filename"
        exit 1
    fi
    
    # Download backup (trim to handle any stray output in capture)
    LOCAL_ZIP=$(download_backup "$BACKUP_FILE" | tail -n 1 | xargs)
    if [ -z "$LOCAL_ZIP" ] || [ ! -f "$LOCAL_ZIP" ]; then
        log_error "Failed to download backup"
        exit 1
    fi
    
    # Extract backup (trim to handle any stray output in capture)
    BACKUP_DIR=$(extract_backup "$LOCAL_ZIP" | tail -n 1 | xargs)
    if [ -z "$BACKUP_DIR" ]; then
        rm -f "$LOCAL_ZIP"
        exit 1
    fi
    
    # Load environment variables (needed for database restore)
    if ! load_env; then
        log_error "Failed to load environment variables"
        rm -rf "$BACKUP_DIR"
        rm -f "$LOCAL_ZIP"
        exit 1
    fi
    
    # Perform restores (media and database only - .env is not restored)
    MEDIA_SUCCESS=false
    DB_SUCCESS=false
    
    if restore_media "$BACKUP_DIR"; then
        MEDIA_SUCCESS=true
    fi
    
    if restore_database "$BACKUP_DIR"; then
        DB_SUCCESS=true
    fi
    
    # Cleanup extracted files
    rm -rf "$BACKUP_DIR"
    log "Temporary files cleaned up"
    
    # Remove downloaded backup file
    rm -f "$LOCAL_ZIP"
    log "Downloaded backup file removed"
    
    log "=========================================="
    if [ "$MEDIA_SUCCESS" = true ] || [ "$DB_SUCCESS" = true ]; then
        log_success "Restore process completed"
        log "Media: $MEDIA_SUCCESS | Database: $DB_SUCCESS"
    else
        log_error "Restore process completed with errors"
    fi
    log "=========================================="
}

# Run main function
main "$@"
