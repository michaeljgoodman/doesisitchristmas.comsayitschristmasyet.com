"""
Screenshot capture functionality using Playwright.
"""

import re
from playwright.async_api import async_playwright


async def capture_isitchristmas_screenshot(country_code: str = "SE") -> bytes:
    """
    Fetches isitchristmas.com, renders it with a headless browser,
    and returns a PNG screenshot.

    Args:
        country_code: The country code to inject (default: "SE" for Sweden)

    Returns:
        PNG screenshot as bytes
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
                    body,
                )

                # Return the modified HTML
                await route.fulfill(response=response, body=modified_body)
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
