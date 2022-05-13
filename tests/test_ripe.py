import os
from unittest.mock import patch, Mock
import requests_mock

from ripeupdater.backup_manager import BackupManager
from ripeupdater.netbox import ObjectBuilder
from ripeupdater.ripe import RipeObjectManager

_dir_path = os.path.dirname(os.path.realpath(__file__))


@patch("pynetbox.api")
@patch("ripeupdater.netbox.TEMPLATES_DIR", f"{_dir_path}/")
@patch("ripeupdater.ripe.TEMPLATES_DIR", f"{_dir_path}/")
@patch("ripeupdater.ripe.TEMPLATES", f"example.json")
def test_ripe(netbox_api):
    # putting it all together.
    webhook = {
        "data": {
            "prefix": "2001:1234:4567::/64",
            "site": {
                "slug": "myslug"
            },
            "custom_fields": {
                "ripe_report": True,
                "ripe_template": "CLOUD-POOL",
            }
        },
        "username": "username",
    }
    netbox_api.return_value.ipam.aggregates.get.return_value = Mock(custom_fields={"lir": "de.examplelir1"})
    netbox_api.return_value.dcim.regions.get.return_value = Mock(slug="germany")
    netbox_object = ObjectBuilder(webhook)
    assert netbox_object.org() == "ORG-EIPB1-TEST"
    assert netbox_object.country() == "DE"

    with requests_mock.Mocker() as m:
        old_object = {
            "objects": {
                "object": [
                    {
                        "attributes": {
                            "attribute": {

                            }
                        }
                    }
                ]
            }
        }
        m.get("https://rest-test.db.ripe.net/test/inet6num/2001:1234:4567::/64?unfiltered",  json=old_object)
        ripe = RipeObjectManager(netbox_object, BackupManager())
        o = ripe.get_old_object()
        assert o == old_object

        put_out = {
            "objects": {
                "object": [
                    {
                        "attributes": {
                            "attribute": {
                            }
                        }
                    }
                ]
            }
        }
        m.put("https://rest-test.db.ripe.net/test/inet6num/2001:1234:4567::/64", json=put_out)
        ripe.push_object()
        assert m.last_request.json() == {
            'objects': {
                'object': [
                    {
                        'source': {'id': 'TEST'},
                        'attributes': {
                            'attribute': [
                                {'name': 'inet6num', 'value': '2001:1234:4567::/64'},
                                {'name': 'netname', 'value': 'CLOUD-POOL'},
                                {'name': 'descr', 'value': 'MyCompany Cloud Pool'},
                                {'name': 'org', 'value': 'ORG-EIPB1-TEST'},
                                {'name': 'country', 'value': 'DE'},
                                {'name': 'remarks', 'value': 'Managed by ripeupdater'},
                                {'name': 'admin-c', 'value': 'AA1-TEST'},
                                {'name': 'tech-c', 'value': 'AA1-TEST'},
                                {'name': 'notify', 'value': 'noc@example.com'},
                                {'name': 'mnt-by', 'value': 'TEST-DBM-MNT'},
                                {'name': 'status', 'value': 'ALLOCATED PA'},
                                {'name': 'source', 'value': 'TEST'}
                            ]
                        }
                    }
                ]
            }
        }

