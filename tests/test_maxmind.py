import random as rand

import pytest
import pycountry
import maxmind


VALID_COUNTRIES = {c.alpha_2 for c in pycountry.countries}  # type: ignore[attr-defined]


def is_valid_country(code: str):
    assert code in VALID_COUNTRIES, f"Invalid country code returned: {code}"


def gen_rand_ipv4():
    """Generates a random IPv4 address."""
    octets = [str(rand.randint(0, 255)) for _ in range(4)]
    return ".".join(octets)


def test_1000_random_ips():
    for _ in range(1000):
        ipv4 = gen_rand_ipv4()
        code = maxmind.get_country_from_ip(ipv4)
        is_valid_country(code)


def test_private_ips_default_to_gb():
    """Local and private IPs should default to GB."""
    assert maxmind.get_country_from_ip("127.0.0.1") == "GB"
    assert maxmind.get_country_from_ip("192.168.0.10") == "GB"
    assert maxmind.get_country_from_ip("10.0.0.1") == "GB"


def test_invalid_ip_defaults_to_gb():
    """Invalid IP formats should default to GB."""
    for ip in ["", "not_an_ip", "999.999.999.999", None]:
        result = maxmind.get_country_from_ip(ip or "")
        assert result == "GB"


@pytest.mark.parametrize(
    "ip",
    [
        "8.8.8.8",  # Google DNS (US)
        "1.1.1.1",  # Cloudflare (AU or US depending on DB)
        "208.67.222.222",  # OpenDNS (US)
    ],
)
def test_real_ip_country_codes_are_valid(ip):
    """Real IPs should return a valid ISO 3166-1 alpha-2 country code."""
    code = maxmind.get_country_from_ip(ip)

    assert isinstance(code, str), f"Expected string, got {type(code)}"
    assert len(code) == 2, f"Expected 2-letter code, got '{code}'"
    assert code in VALID_COUNTRIES, f"Invalid country code returned: {code}"
