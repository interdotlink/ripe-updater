import os

from unittest.mock import patch, Mock

from ripeupdater.netbox import ObjectBuilder

_dir_path = os.path.dirname(os.path.realpath(__file__))

@patch("pynetbox.api")
def test_prefix(netbox_api):
    webhook = {
        "data": {
            "prefix": "2001:1234:4567::/64"
        }
    }
    netbox_object = ObjectBuilder(webhook)
    assert netbox_object.prefix() == "2001:1234:4567::/64"


@patch("pynetbox.api")
@patch("ripeupdater.netbox.TEMPLATES_DIR", f"{_dir_path}/")
def test_org(netbox_api):
    webhook = {
        "data": {
            "prefix": "2001:1234:4567::/64"
        }
    }
    netbox_api.return_value.ipam.aggregates.get.return_value = Mock(custom_fields={"lir": "de.examplelir1"})
    netbox_object = ObjectBuilder(webhook)
    assert netbox_object.org() == "ORG-EIPB1-TEST"\


@patch("pynetbox.api")
@patch("ripeupdater.netbox.TEMPLATES_DIR", f"{_dir_path}/")
def test_country(netbox_api):
    webhook = {
        "data": {
            "site": {
                "slug": "myslug"
            }
        }
    }
    netbox_api.return_value.dcim.regions.get.return_value = Mock(slug="germany")
    netbox_object = ObjectBuilder(webhook)
    assert netbox_object.country() == "DE"