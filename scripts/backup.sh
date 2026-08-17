#!/usr/bin/env bash
# Stratum AI — backup script (DB + client data)
set -euo pipefail
BACKUP_DIR="${BACKUP_DIR:-./backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}/${STAMP}"

echo "→ Backing up database..."
pg_dump "${DATABASE_URL:-postgresql://agent:agent@localhost:5432/stratum}" \
  -Fc -f "${BACKUP_DIR}/${STAMP}/stratum.dump" 2>/dev/null || \
  echo "  WARN: pg_dump failed (is DATABASE_URL set / postgres running?)"

echo "→ Backing up client instances..."
tar -czf "${BACKUP_DIR}/${STAMP}/client_management.tar.gz" \
  -C . CLIENT_MANAGEMENT/client_instances CLIENT_PORTAL/data 2>/dev/null || true

echo "→ Backing up monitoring rules..."
cp -r DEPLOYMENT_INFRASTRUCTURE/monitoring "${BACKUP_DIR}/${STAMP}/" 2>/dev/null || true

echo "✅ Backup written to ${BACKUP_DIR}/${STAMP}"
