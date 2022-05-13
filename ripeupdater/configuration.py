# -*- coding: utf-8 -*-

from os import getenv

# DEBUG
# enables verbose logging
# values: yes/no
# default: no
DEBUG = getenv('DEBUG', 'no')

# MAIL_REPORT
# enables email-reporting
# values: yes/no
# default: no
MAIL_REPORT = getenv('MAIL_REPORT', 'no')

# SMTP
# url or ip of smtp server
# values: url
# default: 127.0.0.1
SMTP = getenv('SMTP', '127.0.0.1')

# SMTP_STARTTLS
# use STARTTLS when connecting to smtp server
# values: yes/no
# default: no
SMTP_STARTTLS = getenv('SMTP_STARTTLS', 'no')

# SENDER_MAIL
# sender mail of email-reports
# values: email
# default: -
SENDER_MAIL = getenv('SENDER_MAIL')

# RECIPIENT_MAIL
# receiver of email-reports
# values: email
# default: -
RECIPIENT_MAIL = getenv('RECIPIENT_MAIL')

# UPDATE_TOKEN
# if set, each netbox webhook must contain this tokes as Authorisation header
# values: string
# default: -
UPDATE_TOKEN = getenv('UPDATE_TOKEN')

# NETBOX_URL
# url of your netbox instance
# values: url
# default: -
NETBOX_URL = getenv('NETBOX_URL')

# NETBOX_TOKEN
# netbox token, which can read prefixes, aggregates, regions and sites
# values: string
# default: -
NETBOX_TOKEN = getenv('NETBOX_TOKEN')

# DEFAULT_COUNTRY
# default country if none could be determined
# values: ISO3166-II country
# default: -
DEFAULT_COUNTRY = getenv('DEFAULT_COUNTRY')

# TEMPLATES_DIR
# location of templates
# values: path
# default: /opt/ripeupdater/templates
TEMPLATES_DIR = getenv('TEMPLATES_DIR', '/opt/ripeupdater/templates')

# RIPE_MNT_PASSWORD
# ripe maintainer password with write permissions to your INET(6)NUM objects
# values: string
# default: -
RIPE_MNT_PASSWORD = getenv('RIPE_MNT_PASSWORD')

# RIPE_DB
# which ripe-db to use
# values: RIPE/TEST
# default: TEST
RIPE_DB = getenv('RIPE_DB', 'TEST')

# RIPE_TEST_MNT
# which maintainer to use in the TEST database, as your maintainer may not be present
# values: string
# default: TEST-DBM-MNT
RIPE_TEST_MNT = getenv('RIPE_TEST_MNT', 'TEST-DBM-MNT')

# RIPE_TEST_ORG
# which organisation to use in the TEST database, as your organisation may not be present
# values: string
# default: ORG-EIPB1-TEST
RIPE_TEST_ORG = getenv('RIPE_TEST_ORG', 'ORG-EIPB1-TEST')

# RIPE_TEST_PERSON
# which person to use in the TEST database, as your person may not be present
# values: string
# default: AA1-TEST
RIPE_TEST_PERSON = getenv('RIPE_TEST_PERSON', 'AA1-TEST')

# RIPE_TEST_STATUS_V4
# which status to use in the TEST database, as your status may not be able to be set. Your parent INETNUM object, with your MNT-LOWER attribute set to your maintainer may be missing. 
# values: string
# default: ALLOCATED PA
RIPE_TEST_STATUS_V4 = getenv('RIPE_TEST_STATUS_V4', 'ALLOCATED PA')

# RIPE_TEST_STATUS_v6
# which status to use in the TEST database, as your status may not be able to be set. Your parent INET6NUM object, with your MNT-LOWER attribute set to your maintainer may be missing.
# values: string
# default: ALLOCATED PA
RIPE_TEST_STATUS_V6 = getenv('RIPE_TEST_STATUS_V6', 'ALLOCATED PA')

# SMALLEST_PREFIX_V4
# prefix length bigger than this limit will not be handled
# values: 0-32
# default: 31
SMALLEST_PREFIX_V4 = getenv('SMALLEST_PREFIX_V4', '31')

# SMALLEST_PREFIX_V6
# prefix length bigger than this limit will not be handled
# values: 0-128
# default: 127
SMALLEST_PREFIX_V6 = getenv('SMALLEST_PREFIX_V6', '127')

# S3_BACKUP
# enable or disable S3 backups
# values: yes/no
# default: no
S3_BACKUP = getenv('S3_BACKUP', 'no')

# S3_ENDPOINTURL
# specify url of your s3 endpoint
# values: url
# default: -
S3_ENDPOINT_URL = getenv('S3_ENDPOINT_URL')

# S3_ACCESS_KEY
# access key to your s3 storage
# values: string
# default: -
S3_ACCESS_KEY = getenv('S3_ACCESS_KEY')

# S3_SECRET_ACCESS_KEY
# secret access key to your s3 storage
# values: string
# default: -
S3_SECRET_ACCESS_KEY = getenv('S3_SECRET_ACCESS_KEY')

# S3_BUCKET
# bucket to store backups in
# values: string
# default: -
S3_BUCKET = getenv('S3_BUCKET')
