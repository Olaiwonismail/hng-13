from flask import Flask, request, jsonify
from hashlib import sha256
from datetime import datetime

app = Flask(__name__)

# In-memory database
strings_db = {}

# ---------- Helper Functions ----------

def analyze_string(value):
    value_stripped = value.strip()
    hash_value = sha256(value_stripped.encode()).hexdigest()
    length = len(value_stripped)
    is_palindrome = value_stripped.lower() == value_stripped[::-1].lower()
    unique_chars = len(set(value_stripped))
    word_count = len(value_stripped.split())
    freq_map = {}
    for ch in value_stripped:
        freq_map[ch] = freq_map.get(ch, 0) + 1

    return {
        "id": hash_value,
        "value": value_stripped,
        "properties": {
            "length": length,
            "is_palindrome": is_palindrome,
            "unique_characters": unique_chars,
            "word_count": word_count,
            "sha256_hash": hash_value,
            "character_frequency_map": freq_map
        },
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

# ---------- Routes ----------

@app.route("/strings", methods=["POST"])
def create_string():
    data = request.get_json()
    if not data or "value" not in data:
        return jsonify({"error": "Missing 'value' field"}), 400
    if not isinstance(data["value"], str):
        return jsonify({"error": "'value' must be a string"}), 422

    analyzed = analyze_string(data["value"])
    if analyzed["id"] in strings_db:
        return jsonify({"error": "String already exists"}), 409

    strings_db[analyzed["id"]] = analyzed
    return jsonify(analyzed), 201


@app.route("/strings/<string_value>", methods=["GET"])
def get_specific_string(string_value):
    hash_value = sha256(string_value.encode()).hexdigest()
    if hash_value not in strings_db:
        return jsonify({"error": "String not found"}), 404
    return jsonify(strings_db[hash_value]), 200


@app.route("/strings", methods=["GET"])
def get_all_strings():
    # Filtering
    filters = {
        "is_palindrome": request.args.get("is_palindrome"),
        "min_length": request.args.get("min_length", type=int),
        "max_length": request.args.get("max_length", type=int),
        "word_count": request.args.get("word_count", type=int),
        "contains_character": request.args.get("contains_character")
    }

    results = list(strings_db.values())

    if filters["is_palindrome"] is not None:
        val = filters["is_palindrome"].lower() == "true"
        results = [r for r in results if r["properties"]["is_palindrome"] == val]

    if filters["min_length"] is not None:
        results = [r for r in results if r["properties"]["length"] >= filters["min_length"]]

    if filters["max_length"] is not None:
        results = [r for r in results if r["properties"]["length"] <= filters["max_length"]]

    if filters["word_count"] is not None:
        results = [r for r in results if r["properties"]["word_count"] == filters["word_count"]]

    if filters["contains_character"]:
        results = [r for r in results if filters["contains_character"] in r["value"]]

    response = {
        "data": results,
        "count": len(results),
        "filters_applied": {k: v for k, v in filters.items() if v is not None}
    }
    return jsonify(response), 200


@app.route("/strings/filter-by-natural-language", methods=["GET"])
def natural_language_filter():
    query = request.args.get("query", "")
    parsed_filters = {}

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    q = query.lower()

    # Very simple parsing logic (can improve later)
    if "palindromic" in q:
        parsed_filters["is_palindrome"] = True
    if "single word" in q:
        parsed_filters["word_count"] = 1
    if "longer than" in q:
        try:
            num = int(q.split("longer than")[1].split()[0])
            parsed_filters["min_length"] = num + 1
        except:
            pass
    if "contain" in q:
        parts = q.split("contain")
        if len(parts) > 1:
            ch = parts[1].strip().split()[0]
            parsed_filters["contains_character"] = ch

    if not parsed_filters:
        return jsonify({"error": "Unable to parse query"}), 400

    # Reuse filter logic
    results = list(strings_db.values())
    if "is_palindrome" in parsed_filters:
        results = [r for r in results if r["properties"]["is_palindrome"]]
    if "word_count" in parsed_filters:
        results = [r for r in results if r["properties"]["word_count"] == parsed_filters["word_count"]]
    if "min_length" in parsed_filters:
        results = [r for r in results if r["properties"]["length"] >= parsed_filters["min_length"]]
    if "contains_character" in parsed_filters:
        results = [r for r in results if parsed_filters["contains_character"] in r["value"]]

    response = {
        "data": results,
        "count": len(results),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed_filters
        }
    }
    return jsonify(response), 200


@app.route("/strings/<string_value>", methods=["DELETE"])
def delete_string(string_value):
    hash_value = sha256(string_value.encode()).hexdigest()
    if hash_value not in strings_db:
        return jsonify({"error": "String not found"}), 404
    del strings_db[hash_value]
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
