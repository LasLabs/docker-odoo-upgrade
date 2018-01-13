[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0.html)
[![Build Status](https://travis-ci.org/LasLabs/docker-odoo-upgrade.svg?branch=master)](https://travis-ci.org/LasLabs/docker-odoo-upgrade)

[![](https://images.microbadger.com/badges/image/laslabs/odoo-upgrade:9.0.svg)](https://microbadger.com/images/laslabs/odoo-upgrade:9.0 "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/laslabs/odoo-upgrade:9.0.svg)](https://microbadger.com/images/laslabs/odoo-upgrade:9.0 "Get your own version badge on microbadger.com")

[![](https://images.microbadger.com/badges/image/laslabs/odoo-upgrade:10.0.svg)](https://microbadger.com/images/laslabs/odoo-upgrade:10.0 "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/laslabs/odoo-upgrade:10.0.svg)](https://microbadger.com/images/laslabs/odoo-upgrade:10.0 "Get your own version badge on microbadger.com")

[![](https://images.microbadger.com/badges/image/laslabs/odoo-upgrade:11.0.svg)](https://microbadger.com/images/laslabs/odoo-upgrade:11.0 "Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/laslabs/odoo-upgrade:11.0.svg)](https://microbadger.com/images/laslabs/odoo-upgrade:11.0 "Get your own version badge on microbadger.com")

Docker Odoo Upgrade
===================

This image upgrades Odoo major versions using OpenUpgrade. This is an
experimental upgrade methodology, and care should be taken if using for
production environments.

This repository is tagged by the Odoo version that is being targeted, and
you can only upgrade one version at a time. Each tag is represented by a
Dockerfile, prefixed with the tag name. For example, to upgrade version
8 to version 10, you need to use the:

* [9.0 image](./9.0-Dockerfile) first
* [10.0 image](./10.0-Dockerfile) next

Basic Instructions
==================

High level usage of this image is as follows:

* Run the image with the following options:
    * Mount the root of your current Odoo file store into the container as `/var/lib/odoo_old`
        * Note that this should not the be `filestore` directory, but the one that contains the
          `filestore` and `sessions` directories (among others).
    * Mount your new Odoo file store into the container as `/var/lib/odoo`
        * You can easily use the old file store path if you wish
        * Note that this should not the be `filestore` directory, but the one that contains the
          `filestore` and `sessions` directories (among others).
    * Link your current PostgreSQL container as `db_old`
    * Link your new PostgreSQL container as `db`
        * You can easily use your old container if you wish. This is primarily to facilitate PSQL
          major version upgrades.
    * Add environment variables for the PostgreSQL credentials (`PGUSER`, `PGPASSWORD`)
        * Add environment variables for the old PostgreSQL db. These will default to the new
          db credentials if not defined. (`PGUSER_OLD`, `PGPASSWORD_OLD`)
    * Add environment variables for the source and target database names (`DB_SOURCE`, `DB_TARGET`)

Given the above, and assuming the below:

* You have a database container named `postgresql`
    * There is a user named `odoo_user` with the password `odoo_password` that has superuser
      access to the database.
* You have an Odoo v8 database named `odoo_v8`
* You have an Odoo v8 filesystem on your host at `/var/lib/odoo_v8`
* You want to upgrade to Odoo v10

You would run the following commands:

```bash
export PG_USER=odoo_user
export PG_PASSWORD=odoo_password

# Migrate v8 to v9
docker run \
    --link postgresql:db \
    --link postgresql:db_old \
    -v /var/lib/odoo_v8:/var/lib/odoo_old \
    -v /var/lib/odoo_v9:/var/lib/odoo \
    -e "PGDATABASE=odoo_v9" \
    -e "PGUSER=${PG_USER}" \
    -e "PGPASSWORD=${PG_PASSWORD}" \
    -e "DB_SOURCE=odoo_v8" \
    -e "DB_TARGET=odoo_v9" \
    laslabs/odoo-upgrade:9.0
# Migrate v9 to v10
docker run \
    --link postgresql:db \
    --link postgresql:db_old \
    -v /var/lib/odoo_v9:/var/lib/odoo_old \
    -v /var/lib/odoo_v10:/var/lib/odoo \
    -e "PGDATABASE=odoo_v10" \
    -e "PGUSER=${PG_USER}" \
    -e "PGPASSWORD=${PG_PASSWORD}" \
    -e "DB_SOURCE=odoo_v9" \
    -e "DB_TARGET=odoo_v10" \
    laslabs/odoo-upgrade:10.0

# Whatever command to start your v10 environment goes below.
odoo
```

Running the above, you will be left with an Odoo v9 and an Odoo v10 database &
filesystem. They will be named `odoo_v9` and `odoo_v10` respectively.

You typically want to run one migration at a time, and validate that it works before
proceeding to the next one. Living on the edge can be fun though.

Docker-Compose Instructions
===========================

The above section is mostly instructional usage, in that it uses plain Docker and
does not consider custom addons that you may have in your installation. Instead, you
would want to use a `docker-compose.yml` file similar to the below:

```yml
version: "2"

services:

  postgresql:
    image: postgres:9.6-alpine
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata
      POSTGRES_PASSWORD: odoo_password
      POSTGRES_USER: odoo_user
    volumes:
    - ~/postgresql_data/:/var/lib/postgresql/data/

  # This is your original Odoo v8 deploy.
  # Use this as a reference for changes that need to be made in other sections
  # in order to match your actual deploy. An environment file makes this easier,
  # but was excluded in the interest of a one file example.
  #
  # odoo_v8:
  #  image: your_organization/your_odoo_scaffold_image:8.0
  #  environment:
  #    - PGDATABASE: odoo_v8
  #    - PGPASSWORD: odoo_password
  #    - PGUSER: odoo_user
  #  volumes:
  #    - ~/odoo_v8_data:/var/lib/odoo
  #  links:
  #    - postgresql:db

  openupgrade_v9:
    image: laslabs/odoo-upgrade:9.0
    volumes:
      - ~/odoo_v8_data:/var/lib/odoo_old
      - ~/odoo_v9_data:/var/lib/odoo
    environment:
      - DB_SOURCE: odoo_v8
      - DB_TARGET: odoo_v9
      - PGDATABASE: odoo_v9
      - PGUSER: odoo_user
      - PGPASSWORD: odoo_password
    links:
      - postgresql:db
      - postgresql:db_old

  custom_upgrader:
    image: your_organization/your_odoo_scaffold_image:9.0
    command: |
      odoo --workers 0 \
           --limit-time-cpu 0 \
           --limit-time-real 0 \
           --stop-after-init \
           --update all
    volumes:
      - ~/odoo_v9_data:/var/lib/odoo
    environment:
      - PGDATABASE: odoo_v9
      - PGUSER: odoo_user
      - PGPASSWORD: odoo_password
    links:
      - postgresql:db

  custom_upgrader:
    image: your_organization/your_odoo_scaffold_image:9.0
    volumes:
      - ~/odoo_v9_data:/var/lib/odoo
    environment:
      - PGDATABASE: odoo_v9
      - PGUSER: odoo_user
      - PGPASSWORD: odoo_password
    links:
      - postgresql:db
```

After running the above, you will be left with a running Odoo v9 instance
that was upgraded from your Odoo v8 instance.

Using a Live Instance
=====================

This image provides the ability to obtain an Odoo backup on the fly, instead
of having to mount the old volume and database. To enable this functionality,
you should set the following environment variables on the upgrader instance:

* `ODOO_URI_OLD`: The base URI of the old Odoo instance, including `http(s)://`
* `ADMIN_PASSWORD_OLD`: The database administration password for the old Odoo
  instance.

The Odoo instance that you provide must have the capability of delivering a
database backup through its web interface. This is usually not possible in
production due to time limits, but that is easy enough to work around and out
of scope here.

Assuming the following:

* You have a PostgreSQL container named `postgresql` running
* You want your new file store to be located at `~/odoo_v10_test` on your host
* The old Odoo is located at `https://odoo.example.com`
* The old Odoo database is named `odoo_v9`
* You want to name the new Odoo database `odoo_v10`
* Your PostgreSQL user and password are both `odoo`

Then a docker run command to upgrade a v9 to v10 would look something like this:

```bash
docker run \
       -e "DB_SOURCE=odoo_v9" \
       -e "DB_TARGET=odoo_v10" \
       -e "PGDATABASE=odoo_v10" \
       -e "PGUSER=odoo" \
       -e "PGPASSWORD=odoo" \
       -e "ODOO_URI_OLD=https://odoo.example.com" \
       -e "ADMIN_PASSWORD_OLD=test" \
       --link postgresql:db \
       -v ~/odoo_v10_test:/var/lib/odoo \
       laslabs/odoo-upgrade:10.0
```

You would subsequently launch your v10 environment as normal, making sure
to configure the `data_dir` and `db_host` parameters appropriately.

Upon first launch, your custom modules will be upgraded. This is because the
upgrade image is only scoped to Odoo core modules, but makes sure to flag the
remainder of the modules for upgrade as well.

Configuration
=============

*

Usage
=====

* 

Build Arguments
===============

The following build arguments are available for customization:


| Name | Default | Description |
|------|---------|-------------|


Environment Variables
=====================

The following environment variables are available for your configuration
pleasure:

| Name | Default | Description |
|------|---------|-------------|
| `DB_SOURCE` | odoo | The name of the source database |
| `DB_TARGET` | odoo | The name of the target database |
| `ODOO_FILESTORE_NEW` | /var/lib/odoo | The path you mounted the new Odoo file store on. |
| `ODOO_FILESTORE_OLD` | /var/lib/odoo_old | The path you mounted the old Odoo file store on. |
| `ODOO_SYSTEM_USER` | odoo | This is the name (or uid) of the Odoo system user on the target image. This is used to ensure proper permissions on the file store. |
| `ODOO_SYSTEM_GROUP` | odoo | This is the name (or gid) of the Odoo system group on the target image. This is used to ensure proper permissions on the file store. |
| `ODOO_URI_OLD` |  | Define this to obtain a backup from a live instance. Include the URI scheme. |
| `ADMIN_PASSWORD_OLD` |  | If using an external backup, this is the database administration password. |
| `ODOO_UPDATE` | all | The modules to flag for updating |
| `PGUSER` | odoo | The PostgreSQL user to use for the new Odoo |
| `PGUSER_OLD` | $PGUSER | The PostgreSQL user to use for the old Odoo |
| `PGPASSWORD` |  | The PostgreSQL password to use for the new Odoo |
| `PGPASSWORD_OLD` | $PGPASSWORD | The PostgreSQL password to use for the old Odoo |

Known Issues / Roadmap
======================


Bug Tracker
===========

Bugs are tracked on [GitHub Issues](https://github.com/LasLabs/docker-odoo-upgrade/issues).
In case of trouble, please check there to see if your issue has already been reported.
If you spotted it first, help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Dave Lasley <dave@laslabs.com>

Maintainer
----------

[![LasLabs Inc.](https://laslabs.com/logo.png)](https://laslabs.com)

This module is maintained by [LasLabs Inc.](https://laslabs.com)

* https://github.com/LasLabs/docker-odoo-upgrade
