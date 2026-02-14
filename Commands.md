# HungweTips Commands


```bash
docker network create hungwetips_net

docker stop $(docker ps -q)

rm -rf hungwetips-api

ssh-keygen -t rsa -b 4096 -C "$(whoami)@$(hostname)" -f ~/.ssh/github

cat /c/Users/User/.ssh/github

timedatectl set-timezone Africa/Johannesburg


```

```bash
docker compose run web wagtail start hungwetips .

docker compose run web python manage.py migrate

docker compose run web python manage.py createsuperuser

docker compose exec -T web pip freeze > requirements.txt
```

## VPS Start Commands

```bash
sudo apt update

sudo apt upgrade -y

sudo apt install ufw -y

sudo ufw enable

sudo ufw allow 80/tcp && sudo ufw allow 8000/tcp && sudo ufw allow 443/tcp && sudo ufw allow 22/tcp && sudo ufw allow 6379/tcp

sudo ufw reload

sudo ufw status
```

## Install Docker on VPS

```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg lsb-release

sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin 

docker --version

sudo usermod -aG docker $USER

docker run hello-world
```

## Clone and Setup Wagtail Project

```bash
mkdir -p ~/srv

cd ~/srv

sudo git clone https://github.com/kelvinmaringire/hungwetips-api.git

cd hungwetips-api

nano .env   # (paste your environment variables here)

docker pull 7612/hungwetips-backend:0.1.0

docker compose up -d
```

## Unified Backup & Restore (Media + Database + .env → Google Drive)

### Setup rclone (one-time)

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure Google Drive remote
rclone config

# Follow the prompts:
# 1. Select "n" for new remote
# 2. Name it "gdrive" (or your preferred name)
# 3. Select "drive" (Google Drive)
# 4. Leave client_id and client_secret blank (uses defaults)
# 5. Choose scope (full access recommended for backups)
# 6. Complete OAuth authentication in browser
# 7. Verify configuration: rclone listremotes
```

### Backup (Media + Database + .env)

```bash
# Run backup script
bash scripts/backup.sh

# The script will:
# - Backup media files from container/volume
# - Backup PostgreSQL database (using credentials from .env)
# - Backup .env file
# - Create a timestamped .zip file
# - Upload to Google Drive: gdrive:HungweTipsBackups/
# - Keep last 2 backups locally (configurable via KEEP_LOCAL_BACKUPS env var)
# - Log all operations to backup.log
```

**Configuration Options:**
```bash
# Customize rclone remote name (default: gdrive)
export RCLONE_REMOTE="gdrive"

# Customize Google Drive folder (default: HungweTipsBackups)
export RCLONE_PATH="HungweTipsBackups"

# Customize number of local backups to keep (default: 2)
export KEEP_LOCAL_BACKUPS=3

# Then run backup
bash scripts/backup.sh
```

### Restore from Backup

```bash
# Restore latest backup
bash scripts/restore.sh latest

# Restore specific backup
bash scripts/restore.sh hungwetips_backup_20240202_020000.zip

# The script will:
# - Download backup from Google Drive
# - Extract backup archive
# - Restore media files to container
# - Drop and recreate database, then restore from dump
# - Restore .env file (with confirmation prompt)
# - Clean up temporary files
```

**Restore Process:**
- Media files: Automatically copied to `hungwetips_web` container
- Database: Requires confirmation before dropping/recreating (destructive operation)
- .env file: Requires confirmation before overwriting (previous .env backed up to `.env.backup`)

### Scheduled Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /home/user/srv/hungwetips-api && bash scripts/backup.sh >> backup.log 2>&1

# Or with custom environment variables
0 2 * * * cd /home/user/srv/hungwetips-api && RCLONE_REMOTE=gdrive RCLONE_PATH=HungweTipsBackups bash scripts/backup.sh >> backup.log 2>&1

# Verify cron job
crontab -l
```

### Manual Backup & Restore (Legacy Methods)

<details>
<summary>Click to expand manual backup/restore commands</summary>

#### Media Files Backup & Restore

```bash
# Backup Media Files
mkdir -p ./media
docker cp hungwetips_web:/app/media/. ./media

# Restore Media Files
docker cp ./media/. hungwetips_web:/app/media/
```

#### PostgreSQL Backup & Restore

```bash
# Backup Database
docker compose exec -T db pg_dump -U postgres -d hungwetips_db -F c > ./data_backup.dump

# Restore Database
docker compose exec -T db psql -U postgres -c "DROP DATABASE hungwetips_db;"
docker compose exec -T db psql -U postgres -c "CREATE DATABASE hungwetips_db;"
docker compose exec -T db pg_restore -U postgres -d hungwetips_db < data_backup.dump
```

</details>


