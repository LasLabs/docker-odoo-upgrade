#!/usr/bin/env bash

set -e

log INFO "Setting up the Postgres credentials"

PGUSER_OLD=${PGUSER_OLD:=${PGUSER}}
PGPASSWORD_OLD=${PGPASSWORD_OLD:=${PGPASSWORD}}

cat <<EOF > ~/.pgpass
db:5432:${DB_TARGET}:${PGUSER}:${PGPASSWORD}
db_old:5432:${DB_SOURCE}:${PGUSER_OLD}:${PGPASSWORD_OLD}
EOF

chmod 0600 ~/.pgpass

log INFO "Rsyncing the old file store to the new file store"
# mkdir -p /var/lib/odoo/filestore/${DB_TARGET}/
# rsync -avz /var/lib/odoo_old/filestore/${DB_SOURCE}/ /var/lib/odoo/filestore/${DB_TARGET}/

log INFO "Creating a clone of the database for upgrade"
# echo "CREATE DATABASE ${DB_TARGET};" | psql -h db
# pg_dump -h db_old -Fc "${DB_SOURCE}" | pg_restore -h db -d "${DB_TARGET}"

# log INFO "Upgrading database clone"
# odoo -d "${DB_TARGET}" --workers 0 --stop-after-init --update "${ODOO_UPDATE:=all}"
