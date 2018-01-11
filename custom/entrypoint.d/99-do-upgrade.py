#!/usr/bin/env python

import logging
import os
import requests
import subprocess

from io import BytesIO
from zipfile import ZipFile

DB_SOURCE = os.environ['DB_SOURCE']
DB_TARGET = os.environ['DB_TARGET']

PGUSER = os.environ.get('PGUSER')
PGPASSWORD = os.environ.get('PGPASSWORD')
PGUSER_OLD = os.environ.get('PGUSER_OLD', PGUSER)
PGPASSWORD_OLD = os.environ.get('PGPASSWORD_OLD', PGPASSWORD)

ODOO_FILESTORE_NEW = os.environ.get('ODOO_FILESTORE_NEW', '/var/lib/odoo')
ODOO_FILESTORE_OLD = os.envion.get('ODOO_FILESTORE_OLD', '/var/lib/odoo_old')
ODOO_UPDATE = os.environ.get('ODOO_UPDATE', 'all')

logging.info('Create empty directories for the filestores if non-existent.')
logging.debug(
    subprocess.check_output([
        'mkdir', '-p',
        '%s/filestore/%s' % (ODOO_FILESTORE_NEW, DB_TARGET),
        ODOO_FILESTORE_OLD,
    ])
)

logging.info('Setup the PostgreSQL credentials file.')
with open(os.open('~/.pgpass', os.O_CREAT | os.O_WRONLY, 0o600), 'w') as fh:
    fh.writelines([
        'db:5432:%s:%s:%s' % (DB_TARGET, PGUSER, PGPASSWORD),
        'db_old:5432:%s:%s:%s' % (DB_SOURCE, PGUSER_OLD, PGPASSWORD_OLD),
    ])

# Create the target database
logging.debug(
    subprocess.check_output([
        'psql', '-h', 'db', '-c', 'CREATE DATABASE "%s";' % DB_TARGET,
    ])
)

if os.environ.get('ODOO_URI_OLD'):
    """Download and extract a backup from external Odoo."""

    admin_pass = os.environ.get(
        'ADMIN_PASSWORD_OLD', os.environ['ADMIN_PASSWORD'],
    )

    logging.info('Getting the backup from the external Odoo.')
    response = requests.post(
        '%s/web/database/backup' % os.environ['ODOO_URI_OLD'],
        {
            'master_pwd': admin_pass,
            'name': os.environ['DB_SOURCE'],
            'backup_format': 'zip',
        },
        stream=True,
    )

    logging.info('Extracting the backup file to disk.')
    backup_zip = ZipFile(BytesIO(response.content))
    backup_zip.extractall(ODOO_FILESTORE_OLD)

    logging.info('Copying the database backup into the target database.')
    logging.debug(
        subprocess.check_output(
            'psql -h db -d "%s" < %s/dump.sql' % (
                DB_TARGET, ODOO_FILESTORE_OLD,
            ),
            shell=True,
        )
    )

else:
    """Copy the backup from another database."""

    logging.info('Dumping the source database into the target.')
    logging.debug(
        subprocess.check_output(
            'pg_dump -h db_old -Fc "%s" | pg_restore -h db -d "%s"' % (
                DB_SOURCE, DB_TARGET,
            ),
            shell=True,
        )
    )


logging.info('Cloning the old file store to the new one.')
logging.debug(
    subprocess.check_output([
        'rsync', '-avz',
        '%s/filestore/%s/' % (ODOO_FILESTORE_OLD, DB_SOURCE),
        '%s/filestore/%s' % (ODOO_FILESTORE_NEW, DB_TARGET),
    ])
)

logging.info('Beginning OpenUpgrade process.')
logging.debug(
    subprocess.check_output([
        'odoo',
        '-d', DB_TARGET,
        '--workers', '0',
        '--stop-after-init',
        '--data-dir', ODOO_FILESTORE_NEW,
        '--update', ODOO_UPDATE,
    ])
)
