![example workflow](https://github.com/michaeljgoodman/doesisitchristmas.comsayitschristmasyet.com/actions/workflows/test.yml/badge.svg)
# IsItChristmas Screenshot Service

A Python web service that fetches [isitchristmas.com](https://isitchristmas.com), renders it server-side using a headless browser, and returns a screenshot.

## Requirements

- Python 3.10 or higher
- Poetry

## Setup

### 1. Install Poetry (if not already installed)

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Install Playwright Browsers

```bash
poetry run playwright install chromium

# For Debian
poetry run playwright install-deps
```


### 4. GeoIP Database (Optional but Recommended)

For automatic IP-based country detection, the server will check these locations automatically:
1. `C:\ProgramData\MaxMind\GeoIPUpdate\GeoIP\GeoLite2-Country.mmdb` (Windows MaxMind default)
2. `./GeoLite2-Country.mmdb` (Current directory)
3. `/usr/share/GeoIP/GeoLite2-Country.mmdb` (Linux default)

**If you don't have the database:**
1. Create a free account at https://www.maxmind.com/en/geolite2/signup
2. Download and install GeoIP Update tool, or manually download the database
3. The server will find it automatically in the standard locations

**For testing locale**
- Local requests (127.0.0.1) will default to GB
- You can still specify country via query parameter: `/?country=SE`

## Usage

### Start the Server

```bash
poetry run python app.py
```

Or using the configured script:

```bash
poetry run start
```

The server will start on `http://localhost:8000`

### Use the Web Interface

Visit `http://localhost:8000/` in your browser to see the animated progress UI.

The interface should:
1. Show progress stages
2. Make a request to our /screenshot endpoint
4. Show the final screenshot

### Get a Screenshot Directly (API)

You can also call the screenshot endpoint directly:

```bash
# Auto-detect country from your IP
curl http://localhost:8000/screenshot -o screenshot.png

# Override with a specific country
curl http://localhost:8000/screenshot?country=JP -o screenshot-japan.png
curl http://localhost:8000/screenshot?country=FR -o screenshot-france.png
curl http://localhost:8000/screenshot?country=US -o screenshot-usa.png
curl http://localhost:8000/screenshot?country=SE -o screenshot-sweden.png
```

### Health Check

```bash
curl http://localhost:8000/health
```


This just confirms the server is online. Todos: check that maxmind DBs are present and valid (check global var for confirmation, to avoid unnescessary resource usage).


## Development

### Run with Auto-Reload

```bash
poetry run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
poetry run pytest
```

Todos: There are no tests right now...

## Configuration

You can modify the following in `app.py`:

- Viewport size: `viewport={"width": 1920, "height": 1080}`
- Wait timeout: `page.wait_for_timeout(2000)` (milliseconds)
- Server host/port: `uvicorn.run(app, host="0.0.0.0", port=8000)`

## License

MIT
