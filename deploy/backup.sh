#!/usr/bin/env bash
# Backup diario de la DB de MisGastos. Instalar via cron en el VPS:
#   ln -sf /opt/gastos/deploy/backup.sh /etc/cron.daily/gastos-backup
# ponytail: copia consistente con .backup + retencion de 14 dias. Suficiente
# para uso personal; si algun dia importa off-site, anadir rclone a Drive.
set -euo pipefail
DB=/var/lib/gastos/gastos.db
DEST=/var/backups/gastos
mkdir -p "$DEST"
sqlite3 "$DB" ".backup '$DEST/gastos-$(date +%F).db'"
ls -1t "$DEST"/gastos-*.db | tail -n +15 | xargs -r rm -f
