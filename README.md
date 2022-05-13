# ripe-updater

ripe-updater is an API wrapper tool between [NetBox](https://github.com/netbox-community/netbox/) and [RIPE-DB](https://apps.db.ripe.net/), to keep INETNUM and INET6NUM objects updated. Initial work has started at [SysEleven](https://syseleven.de) and development continued at [Inter.link](https://inter.link).

ripe-updater is a [Flask](https://flask.palletsprojects.com/) based Python app. The code is available on [GitHub](https://github.com/interdotlink/ripe-updater/)

## Features
* Using NetBox Webhooks on Prefix updates
* Templates for RIPE-DB attributes
* Backups of overwritten/deleted objects (stored in S3)
* Email reporting
* handling of overlapping INET(6)NUM objects

## Deployment
### Requirements
* NetBox 2.4 or later
* Python 3.8 or later

### Getting started
These steps are mandatory to get ripe-updater up and running.
1. deploy ripe-updater
1. configure ripe-updater
1. configure NetBox
1. setup templates

### Containerized (recommended)
Copy and edit `.env`
```
cp .env.example .env
vi .env
docker run \
  -p 8000:80 \
  -v "/home/user/ripe-updater/templates:/opt/ripeupdater/templates:ro" \
  --env-file .env \
  interdotlink/ripe-updater
```

#### docker-compose
Copy and edit `docker-compose.override.yml`
```
cp docker-compose.override.example.yml docker-compose.override.yml
docker-compose up -d
```

### Installation on Linux
Edit `ripeupdater/configuration.py`.
```
pip install -r requirements.txt
python -m gunicorn -b :80 -w 2 ripeupdater.main:app
```

### Note for production deployments

For production use it is recommended, to setup a reverse proxy e.g. Nginx in front of the ripe-updater and add an SSL certificate, e.g. letsencrypt.

## Configuration
Configuration is set via environment variables, but you can also edit `ripeupdater/configuration.py`.

| parameter | values | default | description |
| --- | --- | --- | --- |
| DEBUG | yes/no | no | enables verbose logging |
| MAIL_REPORT | yes/no | no | enables email-reporting |
| SMTP | url | 127.0.0.1 | url or ip of smtp server |
| SMTP_STARTTLS | yes/no | no | use STARTTLS when connecting to smtp server |
| SENDER_MAIL | email | - | sender mail of email-reports |
| RECIPIENT_MAIL | email | - | receiver of email-reports |
| UPDATE_TOKEN | string | - | if set, each netbox webhook must contain this tokes as Authorisation header |
| NETBOX_URL | url | - | url of your netbox instance |
| NETBOX_TOKEN | string | - | netbox token, which can read prefixes, aggregates, regions and sites |
| DEFAULT_COUNTRY | ISO3166-II country | - | default country if none could be determined, e.g. DE or NL |
| TEMPLATES_DIR | path | /opt/ripeupdater/templates | location of templates |
| RIPE_MNT_PASSWORD | string | - | ripe maintainer password with write permissions to your INET(6)NUM objects |
| RIPE_DB | RIPE/TEST | TEST | which ripe-db to use |
| RIPE_TEST_MNT | string | TEST-DBM-MNT | which maintainer to use in the TEST database, as your maintainer may not be present |
| RIPE_TEST_ORG | string | ORG-EIPB1-TEST | which organisation to use in the TEST database, as your organisation may not be present |
| RIPE_TEST_PERSON | string | AA1-TEST | which person to use in the TEST database, as your person may not be present |
| RIPE_TEST_STATUS_V4 | string | ALLOCATED PA | which status to use in the TEST database, as your status may not be able to be set. Your parent INETNUM object, with your MNT-LOWER attribute set to your maintainer may be missing.  |
| RIPE_TEST_STATUS_V6 | string | ALLOCATED PA | which status to use in the TEST database, as your status may not be able to be set. Your parent INET6NUM object, with your MNT-LOWER attribute set to your maintainer may be missing. |
| SMALLEST_PREFIX_V4 | 0-32 | 31 | prefix length bigger than this limit will not be handled |
| SMALLEST_PREFIX_V6 | 0-128 | 127 | prefix length bigger than this limit will not be handled |
| S3_BACKUP | yes/no | no | enable or disable S3 backups |
| S3_ENDPOINT_URL | url | - | specify url of your s3 endpoint |
| S3_ACCESS_KEY | string | - | access key to your s3 storage |
| S3_SECRET_ACCESS_KEY | string | - | secret access key to your s3 storage |
| S3_BUCKET | string | - | bucket to store backups in |

### NetBox configuration
You'll need to add three custom fields to NetBox and data needs to be structured in a specific way.

#### custom field - lir
* Name: `lir`
* Label: LIR
* Assigned Models: ipam -> aggregates
* Type: Selection
* Required: yes
* Choices: ***all LIRs you are responsible for***
* Description: RIPE Local Internet Registry

#### custom field - ripe_report
* Name: `ripe_report`
* Label: RIPE Report
* Assigned Models: ipam -> prefixes
* Type: Boolean
* Required: no
* Default: false
* Description: should this prefix be in RIPE-DB

#### custom field - ripe_template
* Name: `ripe_template`
* Label: RIPE Template
* Assigned Models: ipam -> prefixes
* Type: Selection
* Required: no
* Choices: ***all templates you have created***

#### region - country
Your sites need to have a country as a parent region found in [iso3166.countries_by_name](https://github.com/deactivated/python-iso3166)

#### Webhook
add a webhook to NetBox:
* Name: `ripe-updater`
* Enabled: yes
* Events: Create, Update, Delete
* HTTP Request
  * HTTP Method: POST
  * Payload URL: http(s)://your-ripe-updater-host/update
  * HTTP Content Type: application/json
* Assigned Models: ipam | prefix
* Additional Headers - ***if you have set a token in ripe-updater config, set it here***
  * `Authorisation: Token YOURTOKEN`
* SSL - enable if you have a valid SSL Certificate for your ripe-updater

## Templates
Templates are devided into three components.
1. `lir_org.json` - a list of LIRs you are responsible for, each mapped to a organisation object.
1. `base_something.json` - a base template with INET(6)NUM attributes. E.g. you have one for yourself and one for each customer which needs to have different attributes (e.g. abuse-c) in RIPE-DB.
1. `templates.json` - a list of templates. These must be also added to NetBox custom field choices of ripe_template. Each mapped to a base template.

> With the provided example .env file you should be able to test your templates in the TEST database.

### setup list of LIRs
* copy and edit lir_org.json `cp templates/lir_org.example.json templates/lir_org.json`
* Add each LIR you are responsible for to an organisation object like `"de.examplelir1": "ORG-EIPB1-TEST",`

### setup your templates
* You should create a template for each case, where you want to document different attributes to your INET(6)NUM objects. E.g. like a different `abuse-c`
* You can take `templates/base_mycompany.example.json` as a starting point.
* You must include an **empty** statement: `{"org": ""},` to autofill organisation attributes from your lir_org list.

### setup list of templates
* Copy and edit templates.json `cp templates/templates.example.json templates/templates.json`
* Add your templates you are planning to use like
    ```
            "CLOUD-POOL": {"attributes": [
            {"descr": "MyCompany Cloud Pool"}
        ],
            "inherit": "base_mycompany.json"
        },
    ```

## Backups
If you have enabled and configured a S3 backup storage, you can browse the json representation of deleted or overwritten objects at `http(s)://your-ripe-updater-host/backups`.
To restore a backup manually, you can post the json file to the RIPE database:
```
curl -X POST -H 'Content-Type: application/json' --data @prefix.json 'https://rest.db.ripe.net/ripe/inetnum?password=RIPE_MNT_PASSWORD'
```

## Development
To run the unit tests, run

```
pip install tox
tox
```

## Known limitations
* Having Ripe-Report set for parent and it's child-prefixes will fail, as you can only have one level of prefixes below your aggregates in RIPE-DB.
  * ***Workaround***: Disable Ripe-Reporting of the parent or child prefixes.
* Extending a prefix in NetBox (e.g. /27 to /26) will fail, as there is not deterministic way of detecting this.
  * ***Workaround***: Disable Ripe-Reporting of this prefix, extend prefix size, reenable Ripe-Reporting

## Initial Authors
* Mohamad Mouselli (https://github.com/mmouselli)
* Christian Harendt (christian at inter.link)