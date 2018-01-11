#!/usr/bin/env python

import logging
import os
import requests
import subprocess

from io import BytesIO
from zipfile import ZipFile

DB_SOURCE = os.environ.get('DB_SOURCE', 'odoo')
DB_TARGET = os.environ.get('DB_TARGET', 'odoo')

PGUSER = os.environ.get('PGUSER', 'odoo')
PGPASSWORD = os.environ.get('PGPASSWORD')
PGUSER_OLD = os.environ.get('PGUSER_OLD', PGUSER)
PGPASSWORD_OLD = os.environ.get('PGPASSWORD_OLD', PGPASSWORD)

ODOO_FILESTORE_NEW = os.environ.get('ODOO_FILESTORE_NEW', '/var/lib/odoo')
ODOO_FILESTORE_OLD = os.environ.get('ODOO_FILESTORE_OLD', '/var/lib/odoo_old')
ODOO_UPDATE = os.environ.get('ODOO_UPDATE', 'all')

logging.info('Create empty directories for the file stores if non-existent.')
logging.debug(
    subprocess.check_output([
        'mkdir', '-p',
        '%s/filestore/%s' % (ODOO_FILESTORE_NEW, DB_TARGET),
        ODOO_FILESTORE_OLD,
    ])
)

logging.info('Setup the PostgreSQL credentials file.')
path = '%s/.pgpass' % os.path.expanduser('~')
with os.fdopen(os.open(path, os.O_CREAT | os.O_WRONLY, 0o600), 'w') as fh:
    fh.writelines([
        'db:5432:%s:%s:%s' % (DB_TARGET, PGUSER, PGPASSWORD),
        'db_old:5432:%s:%s:%s' % (DB_SOURCE, PGUSER_OLD, PGPASSWORD_OLD),
    ])

# Create the target database
logging.debug(
    subprocess.check_output(['createdb', '-h', 'db', DB_TARGET])
)

if os.environ.get('ODOO_URI_OLD') or os.environ.get('ODOO_BACKUP_PATH'):
    """Download and extract a backup from external Odoo."""

    admin_pass = os.environ.get(
        'ADMIN_PASSWORD_OLD', os.environ.get('ADMIN_PASSWORD'),
    )
    rsync_location = os.path.join(ODOO_FILESTORE_OLD, 'filestore')

    if os.environ.get('ODOO_URI_OLD'):
        logging.info('Getting the backup from the external Odoo.')
        odoo_uri = os.environ['ODOO_URI_OLD'].strip('/')
        response = requests.post(
            '%s/web/database/backup' % odoo_uri,
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

    rsync_location = os.path.join(ODOO_FILESTORE_OLD, 'filestore', DB_TARGET)

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
        rsync_location,
        os.path.join(ODOO_FILESTORE_NEW, 'filestore', DB_TARGET),
    ])
)
