"""
Server that fetches isitchristmas.com, renders it, and returns a screenshot.
"""

from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

import uvicorn

from maxmind import get_country_from_ip
from screenshot import capture_isitchristmas_screenshot


app = FastAPI(title="IsItChristmas Screenshot Service")

# Mount static files directory for CSS
app.mount("/styles", StaticFiles(directory="styles"), name="styles")


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
        },
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

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
