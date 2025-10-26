from datetime import datetime
import os
from flask import Flask, request, jsonify, send_file
import requests
from flask_sqlalchemy import SQLAlchemy
import random
from sqlalchemy import func
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
# Use DATABASE_URL if provided, otherwise fallback to sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/data.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CountryModel(db.Model):
	# ...existing code...
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	capital = db.Column(db.String(100))
	region = db.Column(db.String(100))
	population = db.Column(db.Integer, nullable=False)
	currency_code = db.Column(db.String(10), nullable=True)  # allow null per spec
	exchange_rate = db.Column(db.Float, nullable=True)
	estimated_gdp = db.Column(db.Float, nullable=True)
	flag_url = db.Column(db.String(200))
	last_refreshed_at = db.Column(db.DateTime)

with app.app_context():
		
    db.create_all() 

# Helper: fetch external data (countries + exchange rates)
def fetch_external_data():
	try:
		countries_resp = requests.get('https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies', timeout=10)
	except requests.RequestException:
		return None, None, ("External data source unavailable", "Could not fetch data from Countries API")
	if countries_resp.status_code != 200:
		return None, None, ("External data source unavailable", "Could not fetch data from Countries API")
	try:
		countries_json = countries_resp.json()
	except ValueError:
		return None, None, ("External data source unavailable", "Invalid JSON from Countries API")

	try:
		rates_resp = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
	except requests.RequestException:
		return None, None, ("External data source unavailable", "Could not fetch data from Exchange Rates API")
	if rates_resp.status_code != 200:
		return None, None, ("External data source unavailable", "Could not fetch data from Exchange Rates API")
	try:
		rates_json = rates_resp.json()
	except ValueError:
		return None, None, ("External data source unavailable", "Invalid JSON from Exchange Rates API")

	return countries_json, rates_json, None

# Helper: process countries into record dicts according to spec
def process_countries(countries_json, rates_json, refresh_ts):
	processed = []
	validation_errors = {}
	for idx, country in enumerate(countries_json):
		name = country.get('name')
		population = country.get('population')
		capital = country.get('capital')
		region = country.get('region')
		flag_url = country.get('flag')
		currencies = country.get('currencies') or []

		# Validation: name and population required
		if not name or population is None:
			validation_errors[name or f'index_{idx}'] = {}
			if not name:
				validation_errors[name or f'index_{idx}']['name'] = 'is required'
			if population is None:
				validation_errors[name or f'index_{idx}']['population'] = 'is required'
			# stop processing when validation fails (do not modify DB)
			continue

		# Currency handling per spec
		if not currencies:
			currency_code = None
			exchange_rate = None
			estimated_gdp = 0.0
		else:
			currency_code = (currencies[0] or {}).get('code')
			# rates may not have currency_code
			exchange_rate = None
			if rates_json and isinstance(rates_json, dict):
				rates = rates_json.get('rates', {})
				if currency_code:
					exchange_rate = rates.get(currency_code)
			if exchange_rate is None:
				estimated_gdp = None
			else:
				rand = random.randint(1000, 2000)
				# simplified GDP estimate
				estimated_gdp = (population * rand) / exchange_rate

		processed.append({
			'name': name,
			'capital': capital,
			'region': region,
			'population': population,
			'currency_code': currency_code,
			'exchange_rate': exchange_rate,
			'estimated_gdp': estimated_gdp,
			'flag_url': flag_url,
			'last_refreshed_at': refresh_ts
		})

	if validation_errors:
		return None, validation_errors

	return processed, None

# Helper: save processed records to DB (update or insert; match by name case-insensitive)
def save_countries(processed):
	for rec in processed:
		name = rec['name']
		# case-insensitive lookup
		existing = CountryModel.query.filter(func.lower(CountryModel.name) == name.lower()).first()
		if existing:
			# update all fields
			existing.capital = rec['capital']
			existing.region = rec['region']
			existing.population = rec['population']
			existing.currency_code = rec['currency_code']
			existing.exchange_rate = rec['exchange_rate']
			existing.estimated_gdp = rec['estimated_gdp']
			existing.flag_url = rec['flag_url']
			existing.last_refreshed_at = rec['last_refreshed_at']
		else:
			new = CountryModel(
				name = rec['name'],
				capital = rec['capital'],
				region = rec['region'],
				population = rec['population'],
				currency_code = rec['currency_code'],
				exchange_rate = rec['exchange_rate'],
				estimated_gdp = rec['estimated_gdp'],
				flag_url = rec['flag_url'],
				last_refreshed_at = rec['last_refreshed_at']
			)
			db.session.add(new)
	db.session.commit()

# Helper: generate summary image (cache/summary.png)
def generate_summary_image(refresh_ts):
	os.makedirs('cache', exist_ok=True)
	image_path = os.path.join('cache', 'summary.png')
	total = CountryModel.query.count()
	top5 = CountryModel.query.filter(CountryModel.estimated_gdp != None).order_by(CountryModel.estimated_gdp.desc()).limit(5).all()

	# Create a simple image
	width, height = 800, 400
	img = Image.new('RGB', (width, height), color=(255,255,255))
	draw = ImageDraw.Draw(img)
	# Try to load a default font
	try:
		font = ImageFont.truetype("arial.ttf", 18)
		title_font = ImageFont.truetype("arial.ttf", 24)
	except Exception:
		font = ImageFont.load_default()
		title_font = font

	draw.text((20, 20), "Countries Summary", font=title_font, fill=(0,0,0))
	draw.text((20, 60), f"Total countries: {total}", font=font, fill=(0,0,0))
	draw.text((20, 90), f"Last refreshed at: {refresh_ts.isoformat()}Z", font=font, fill=(0,0,0))

	draw.text((20, 130), "Top 5 by estimated GDP:", font=font, fill=(0,0,0))
	y = 160
	for i, c in enumerate(top5, start=1):
		name = c.name
		gdp = f"{c.estimated_gdp:,.2f}" if c.estimated_gdp is not None else "N/A"
		draw.text((40, y), f"{i}. {name} — {gdp}", font=font, fill=(0,0,0))
		y += 24

	img.save(image_path)
	return image_path

# POST /countries/refresh
@app.route('/countries/refresh', methods=['POST'])
def refresh_countries():
	# Fetch external data first
	countries_json, rates_json, err = fetch_external_data()
	if err:
		return jsonify({"error": err[0], "details": err[1]}), 503

	# Use a single refresh timestamp
	refresh_ts = datetime.utcnow()

	# Process data (validation happens here)
	processed, validation = process_countries(countries_json, rates_json, refresh_ts)
	if validation:
		return jsonify({"error": "Validation failed", "details": validation}), 400

	# If processing ok, persist (update/insert)
	try:
		# Persist within DB session; do not delete all first to preserve update logic
		save_countries(processed)
		# After saving, generate image
		generate_summary_image(refresh_ts)
	except Exception as e:
		db.session.rollback()
		return jsonify({"error": "Internal server error"}), 500

	return jsonify({"message": "Countries data refreshed", "total_countries": CountryModel.query.count(), "last_refreshed_at": refresh_ts.isoformat() + "Z"}), 200

# GET /countries
@app.route('/countries', methods=['GET'])
def list_countries():
	region = request.args.get('region')
	currency = request.args.get('currency')
	sort = request.args.get('sort')

	query = CountryModel.query
	if region:
		query = query.filter(CountryModel.region == region)
	if currency:
		query = query.filter(CountryModel.currency_code == currency)
	if sort == 'gdp_desc':
		query = query.order_by(CountryModel.estimated_gdp.desc().nulls_last())
	countries = query.all()

	result = []
	for country in countries:
		result.append({
			'id': country.id,
			'name': country.name,
			'capital': country.capital,
			'region': country.region,
			'population': country.population,
			'currency_code': country.currency_code,
			'exchange_rate': country.exchange_rate,
			'estimated_gdp': country.estimated_gdp,
			'flag_url': country.flag_url,
			'last_refreshed_at': country.last_refreshed_at.isoformat() + "Z" if country.last_refreshed_at else None
		})
	return jsonify(result), 200

# GET /countries/:name
@app.route('/countries/<string:name>', methods=['GET'])
def get_country(name):
	country = CountryModel.query.filter(func.lower(CountryModel.name) == name.lower()).first()
	if not country:
		return jsonify({"error": "Country not found"}), 404
	return jsonify({
		'id': country.id,
		'name': country.name,
		'capital': country.capital,
		'region': country.region,
		'population': country.population,
		'currency_code': country.currency_code,
		'exchange_rate': country.exchange_rate,
		'estimated_gdp': country.estimated_gdp,
		'flag_url': country.flag_url,
		'last_refreshed_at': country.last_refreshed_at.isoformat() + "Z" if country.last_refreshed_at else None
	}), 200

# DELETE /countries/:name
@app.route('/countries/<string:name>', methods=['DELETE'])
def delete_country(name):
	country = CountryModel.query.filter(func.lower(CountryModel.name) == name.lower()).first()
	if not country:
		return jsonify({"error": "Country not found"}), 404
	deleted = {
		'id': country.id,
		'name': country.name,
		'capital': country.capital,
		'region': country.region,
		'population': country.population,
		'currency_code': country.currency_code,
		'exchange_rate': country.exchange_rate,
		'estimated_gdp': country.estimated_gdp,
		'flag_url': country.flag_url,
		'last_refreshed_at': country.last_refreshed_at.isoformat() + "Z" if country.last_refreshed_at else None
	}
	db.session.delete(country)
	db.session.commit()
	return jsonify(deleted), 200

# GET /status
@app.route('/status', methods=['GET'])
def get_status():
	total_countries = CountryModel.query.count()
	last_refreshed_country = CountryModel.query.order_by(CountryModel.last_refreshed_at.desc()).first()
	last_refreshed_at = last_refreshed_country.last_refreshed_at.isoformat() + "Z" if last_refreshed_country and last_refreshed_country.last_refreshed_at else None
	return jsonify({
		'total_countries': total_countries,
		'last_refreshed_at': last_refreshed_at
	}), 200

# GET /countries/image
@app.route('/countries/image', methods=['GET'])
def get_countries_image():
	image_path = "cache/summary.png"
	if not os.path.exists(image_path):
		return jsonify({"error": "Summary image not found"}), 404
	return send_file(image_path, mimetype='image/png')

# Health endpoint
@app.route('/health', methods=['GET'])
def health_check():
	return "OK", 200

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)