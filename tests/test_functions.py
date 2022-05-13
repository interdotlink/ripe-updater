from pytest import raises

from ripeupdater.functions import *
from ripeupdater.exceptions import *


def test_read_json_file():
    d = read_json_file("tests/example.json")
    assert type(d) is dict


def test_flatten_ripe_object():
    obj = {"type": "inetnum","link": {"type": "locator"},"source": {"id": "ripe"},"attributes": {"attribute": [{"name": "country","value": "DE"},{"name": "remarks","value": "Managed by ripeupdater"},{"name": "status","value": "ASSIGNED PA"}]}}
    attr = flatten_ripe_attributes(obj)

    assert attr["country"] == "DE"


def test_format_ripe_object():
    obj = {"type": "inetnum","link": {"type": "locator"},"source": {"id": "ripe"},"attributes": {"attribute": [{"name": "country","value": "DE"},{"name": "remarks","value": "Managed by ripeupdater"},{"name": "status","value": "ASSIGNED PA"}]}}
    string = format_ripe_object(obj, "+")

    assert string.find("+status\t\tASSIGNED PA")


def test_is_v6():
    assert is_v6("2001:db8:f::/48")
    assert not is_v6("198.51.100.0/24")


def test_validate_prefix():
    with raises(ErrorSmallPrefix) as execinfo:
        validate_prefix("2001:db8::/128")
    assert "too small" in str(execinfo.value)

    with raises(NotRoutedNetwork) as execinfo:
        validate_prefix("fe80::/64")
    assert "not routed" in str(execinfo.value)

    with raises(ErrorSmallPrefix) as execinfo:
        validate_prefix("127.0.0.0/32")
    assert "too small" in str(execinfo.value)

    with raises(NotRoutedNetwork) as execinfo:
        validate_prefix("127.0.0.0/8")
    assert "not routed" in str(execinfo.value)

    with raises(NotRoutedNetwork) as execinfo:
        validate_prefix("172.16.0.0/12")
    assert "not routed" in str(execinfo.value)

    assert validate_prefix("2001:1234:4567::/64")
    assert validate_prefix("1.0.0.0/24")


def test_format_cidr():
    assert "198.51.100.0 - 198.51.100.255" == format_cidr("198.51.100.0/24")


def test_notify():
    obj = {"type": "inetnum","link": {"type": "locator"},"source": {"id": "ripe"},"attributes": {"attribute": [{"name": "country","value": "DE"},{"name": "remarks","value": "Managed by ripeupdater"},{"name": "status","value": "ASSIGNED PA"}]}}
    notify(obj, "POST", "198.51.100.0/24", "testuser", 200, [])


def test_find():
    assert find("elem1.elem2", {"elem1": {"elem2": "foo"}}) == "foo"