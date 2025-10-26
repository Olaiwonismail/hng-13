# Country Currency & Exchange API

Simple Flask API that fetches country data and USD exchange rates, caches results in a database, and exposes CRUD and summary endpoints.

## Features
- Fetch countries from https://restcountries.com and exchange rates from https://open.er-api.com
- Cache country data (name, capital, region, population, currency, exchange rate, estimated_gdp, flag_url, last_refreshed_at)
- Endpoints:
  - POST /countries/refresh
  - GET /countries
  - GET /countries/:name
  - DELETE /countries/:name
  - GET /status
  - GET /countries/image
  - GET /health

## Prerequisites
- Python 3.8+
- git (optional)
- (Optional) MySQL or any database supported by SQLAlchemy if you prefer not to use default SQLite

## Recommended setup (local)
1. Clone or copy project files into a working folder.
2. Create and activate a virtual environment:
   - Windows:
     python -m venv venv
     venv\Scripts\activate
   - macOS / Linux:
     python3 -m venv venv
     source venv/bin/activate

3. Install dependencies:
   pip install flask flask_sqlalchemy requests pillow python-dotenv

   (Alternatively, create a requirements.txt with these and run `pip install -r requirements.txt`)

## Environment variables
Create a `.env` file in the project root or export variables in your shell.

Recommended variables:
- DATABASE_URL (optional) — SQLAlchemy connection string (e.g. mysql+pymysql://user:pass@host/dbname). If not set, defaults to SQLite `sqlite:///countries.db`.
- PORT (optional) — Port to run the Flask app (defaults to 5000).

Example `.env`:
DATABASE_URL=sqlite:///countries.db
PORT=5000

Note: The app reads DATABASE_URL via os.getenv. If using MySQL, install an appropriate DB driver (e.g. `pymysql`).

## Run locally
With the virtualenv activated and dependencies installed:
python app.py

The server will start on 0.0.0.0:5000 (or the port set in PORT).

## Usage examples

- Refresh (fetch and cache countries + generate image):
  curl -X POST http://localhost:5000/countries/refresh

- List countries (filters & sort):
  GET all: http://localhost:5000/countries
  By region: http://localhost:5000/countries?region=Africa
  By currency: http://localhost:5000/countries?currency=NGN
  Sort by GDP desc: http://localhost:5000/countries?sort=gdp_desc

- Get single country:
  GET http://localhost:5000/countries/Nigeria

- Delete a country:
  DELETE http://localhost:5000/countries/Nigeria

- Status:
  GET http://localhost:5000/status

- Summary image:
  GET http://localhost:5000/countries/image
  (image saved as `cache/summary.png` after a successful refresh)

- Health:
  GET http://localhost:5000/health

## Notes
- The refresh endpoint will first fetch external APIs; if they are unavailable it returns 503 and does not modify the database.
- Estimated GDP is computed as: population × random(1000–2000) ÷ exchange_rate (per-country random multiplier on each refresh).
- If a country has no currencies, currency_code and exchange_rate are null and estimated_gdp is 0.
- If currency_code is missing from the exchange rates response, exchange_rate and estimated_gdp are null.

## Troubleshooting
- If you get missing package errors, ensure all dependencies are installed in the active virtual environment.
- If using a remote DB, ensure DATABASE_URL is correctly set and the DB user has appropriate privileges.

## Development tips
- Install Pillow for image generation: pip install pillow
- To switch to MySQL, set DATABASE_URL to a valid SQLAlchemy URI and install the driver (e.g. pymysql).

---
