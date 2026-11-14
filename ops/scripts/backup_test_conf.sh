#!/usr/bin/env bash
set -Eeuo pipefail

# --- Config ---
SITE_DOMAIN="test-conf.de"
UPLOADS_DIR="/var/www/vhosts/${SITE_DOMAIN}/test_conf/data/uploads"
ENV_FILE="/var/www/vhosts/${SITE_DOMAIN}/test_conf/container/prod/.compose_env"
DB_CONTAINER="test_conf_db"

BACKUP_ROOT="/var/backups/test-conf"
KEEP_DAYS=14

SEND_ONEDRIVE="true"             # set to "false" if not using OneDrive
RCLONE_REMOTE="onedrive:Strato-Server/test_conf_backups"

# --- Prep ---
umask 077
mkdir -p "$BACKUP_ROOT"
DATE="$(date -u +'%Y%m%dT%H%M%SZ')"
WORK_DIR="$(mktemp -d)"
ARCHIVE="${BACKUP_ROOT}/test-conf-backup-${DATE}.tar.zst"

# Remove the temp dir (DB dump, uploads tar) on every exit, including failures.
# Installed right after mktemp so no later `exit` or `set -e` abort can leak it.
trap 'rm -rf "$WORK_DIR"' EXIT

# Prevent overlapping runs
exec 9>"/var/lock/backup_test_conf.lock"
flock -n 9 || { echo "Another backup is running"; exit 1; }

# --- Load DB env safely (no sourcing, no comment parsing inside values) ---
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    # skip blank lines and lines whose first non-space is '#'
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # KEY=VALUE (allow anything after the first '=')
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"
      # trim surrounding whitespace from value only (not inner spaces)
      val="${val#"${val%%[![:space:]]*}"}"
      val="${val%"${val##*[![:space:]]}"}"
      # remove optional single/double surrounding quotes
      if [[ "$val" =~ ^\"(.*)\"$ ]]; then val="${BASH_REMATCH[1]}"; fi
      if [[ "$val" =~ ^\'(.*)\'$ ]]; then val="${BASH_REMATCH[1]}"; fi
      export "$key=$val"
    fi
  done < "$ENV_FILE"
else
  echo "ERROR: Env file not found at $ENV_FILE" >&2
  exit 2
fi

# sanity check
: "${MYSQL_DATABASE:?missing}"; : "${MYSQL_USER:?missing}"; : "${MYSQL_PASSWORD:?missing}"

# --- Dump DB ---
echo "[*] Dumping database ${MYSQL_DATABASE} from container ${DB_CONTAINER}..."
DB_SQL="${WORK_DIR}/db_${MYSQL_DATABASE}.sql"
# The password goes in the environment of this one process, not on the command line,
# so other users cannot read it from the process list.
MYSQL_PWD="$MYSQL_PASSWORD" mysqldump \
  -h 127.0.0.1 -P 6033 \
  -u"$MYSQL_USER" \
  --single-transaction --quick --routines --events --triggers \
  "$MYSQL_DATABASE" > "$DB_SQL"

# --- Archive uploads ---
echo "[*] Archiving uploads from ${UPLOADS_DIR}..."
UPLOADS_TAR="${WORK_DIR}/uploads.tar"
tar -C "$UPLOADS_DIR" -cpf "$UPLOADS_TAR" .

# --- Create manifest (no secrets) ---
MANIFEST="${WORK_DIR}/manifest.txt"
{
  echo "site: ${SITE_DOMAIN}"
  echo "timestamp_utc: ${DATE}"
  echo "uploads_dir: ${UPLOADS_DIR}"
  echo "db_container: ${DB_CONTAINER}"
  echo "database: ${MYSQL_DATABASE}"
  echo "host: $(hostname)"
} > "$MANIFEST"

# --- Bundle & compress (zstd) ---
echo "[*] Creating final archive ${ARCHIVE}..."
tar -C "$WORK_DIR" -cf - "$(basename "$DB_SQL")" "$(basename "$UPLOADS_TAR")" "$(basename "$MANIFEST")" \
  | zstd -T0 -19 -o "$ARCHIVE"

# --- Verify archive (list) ---
echo "[*] Verifying archive contents..."
unzstd -c "$ARCHIVE" | tar -tf - >/dev/null

# --- Retention ---
echo "[*] Deleting backups older than ${KEEP_DAYS} days in ${BACKUP_ROOT}..."
find "$BACKUP_ROOT" -type f -name 'test-conf-backup-*.tar.zst' -mtime +"$KEEP_DAYS" -print -delete

# --- Delivery: OneDrive via rclone ---
if [[ "$SEND_ONEDRIVE" == "true" ]]; then
  echo "[*] Uploading to OneDrive (${RCLONE_REMOTE})..."
  rclone copy -v "$ARCHIVE" "$RCLONE_REMOTE"
fi

echo "[*] Done."
