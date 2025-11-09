"""
Server that fetches isitchristmas.com, renders it, and returns a screenshot.
"""
import re
import ipaddress
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
import geoip2.database
import geoip2.errors

app = FastAPI(title="IsItChristmas Screenshot Service")

# Mount static files directory for CSS
app.mount("/styles", StaticFiles(directory="styles"), name="styles")

# Try to load MaxMind GeoIP database (optional)
# Check multiple possible locations
GEOIP_DB_PATHS = [
    Path(r"C:\ProgramData\MaxMind\GeoIPUpdate\GeoIP\GeoLite2-Country.mmdb"),  # Windows MaxMind default
    Path("GeoLite2-Country.mmdb"),  # Current directory
    Path("/usr/share/GeoIP/GeoLite2-Country.mmdb"),  # Linux default
]

geoip_reader = None

for db_path in GEOIP_DB_PATHS:
    if db_path.exists():
        try:
            geoip_reader = geoip2.database.Reader(str(db_path))
            print(f"✓ GeoIP database loaded from {db_path}")
            break
        except Exception as e:
            print(f"⚠ Failed to load GeoIP database from {db_path}: {e}")

if geoip_reader is None:
    print("⚠ GeoIP database not found in any standard location")
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


async def capture_isitchristmas_screenshot(country_code: str = "SE") -> bytes:
    """
    Fetches isitchristmas.com, renders it with a headless browser,
    and returns a PNG screenshot.

    Args:
        country_code: The country code to inject (default: "SE" for Sweden)
    """
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        # Intercept the main HTML document and modify the country code
        async def handle_route(route):
            # Only intercept the main document
            if route.request.resource_type == "document":
                # Fetch the original response
                response = await route.fetch()
                body = await response.text()

                # Replace the server-generated country code with our desired one
                # Pattern matches: var country = "XX"; or var country = 'XX';
                modified_body = re.sub(
                    r'var country = ["\'][A-Z]{2}["\'];',
                    f'var country = "{country_code}";',
                    body
                )

                # Return the modified HTML
                await route.fulfill(
                    response=response,
                    body=modified_body
                )
            else:
                # Let other resources (JS, CSS, images) load normally
                await route.continue_()

        # Set up the route interception
        await page.route("**/*", handle_route)

        # Navigate to isitchristmas.com
        await page.goto("https://isitchristmas.com", wait_until="networkidle")

        # Wait a bit for any animations/websockets to settle
        await page.wait_for_timeout(2000)

        # Take screenshot
        screenshot_bytes = await page.screenshot(type="png", full_page=True)

        await browser.close()

        return screenshot_bytes


@app.get("/screenshot")
async def get_screenshot(request: Request, country: Optional[str] = None):
    """
    Screenshot endpoint that returns a screenshot of isitchristmas.com

    Args:
        request: FastAPI request object (used to extract client IP)
        country: Optional two-letter country code to override IP detection
                 If not provided, uses IP-based geolocation
                 Examples: US, FR, DE, JP, SE, etc.
    """
    # If country not specified, detect from IP
    if country is None:
        # Get client IP, checking X-Forwarded-For header first (for proxies)
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "127.0.0.1"

        country = get_country_from_ip(client_ip)
        print(f"Detected IP: {client_ip} → Country: {country}")
    else:
        country = country.upper()
        print(f"Using provided country: {country}")

    screenshot = await capture_isitchristmas_screenshot(country)

    return Response(
        content=screenshot,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=isitchristmas-{country}.png"
        }
    )


@app.get("/")
async def index():
    """
    Main landing page with animated progress UI
    """
    f = open("templates/index.html", encoding="utf8")
    html_content = f.read()
    return Response(content=html_content, media_type="text/html")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}


def main():
    """
    Entry point for running the server
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
