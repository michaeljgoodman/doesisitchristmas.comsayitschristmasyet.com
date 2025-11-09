"""
GeoIP functionality using MaxMind GeoLite2-Country database.
"""

import ipaddress
from pathlib import Path
from typing import Optional
import geoip2.database
import geoip2.errors


# Try to load MaxMind GeoIP database (optional)
# Check multiple possible locations
GEOIP_DB_PATHS = [
    Path(
        r"C:\ProgramData\MaxMind\GeoIPUpdate\GeoIP\GeoLite2-Country.mmdb"
    ),  # Windows MaxMind default
    Path("GeoLite2-Country.mmdb"),  # Current directory
    Path("/usr/share/GeoIP/GeoLite2-Country.mmdb"),  # Linux default
]

geoip_reader: Optional[geoip2.database.Reader] = None

# Try to initialize the GeoIP reader
for db_path in GEOIP_DB_PATHS:
    if db_path.exists():
        try:
            geoip_reader = geoip2.database.Reader(str(db_path))
            print(f"[OK] GeoIP database loaded from {db_path}")
            break
        except Exception as e:
            print(f"[WARNING] Failed to load GeoIP database from {db_path}: {e}")

if geoip_reader is None:
    print("[WARNING] GeoIP database not found in any standard location")
    print("  Checked:")
    for db_path in GEOIP_DB_PATHS:
        print(f"    - {db_path}")
    print("  Country detection will use query parameter or default to GB")


def get_country_from_ip(ip_address: str) -> str:
    """
    Get country code from IP address using MaxMind GeoIP2.

    Args:
        ip_address: IP address string

    Returns:
        Two-letter country code (defaults to GB for local/private IPs)
    """
    # Check if IP is local/private
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        if ip_obj.is_private or ip_obj.is_loopback:
            return "GB"  # Default for local requests
    except ValueError:
        return "GB"

    # Try GeoIP lookup if database is available
    if geoip_reader:
        try:
            response = geoip_reader.country(ip_address)
            country_code = response.country.iso_code
            if country_code:
                return country_code
        except geoip2.errors.AddressNotFoundError:
            pass
        except Exception as e:
            print(f"GeoIP lookup error for {ip_address}: {e}")

    return "GB"  # Default fallback
