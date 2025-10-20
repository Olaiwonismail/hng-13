from flask import Flask, request, jsonify
from datetime import datetime
import hashlib
import re


from typing import Dict, Any, List
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
# In-memory storage (in production, use a database)
strings_storage = {}

def compute_string_properties(value: str) -> Dict[str, Any]:
    """Compute all required properties for a string"""
    # Basic properties
    length = len(value)
    
    # Case-insensitive palindrome check
    cleaned_value = re.sub(r'[^a-zA-Z0-9]', '', value.lower())
    is_palindrome = cleaned_value == cleaned_value[::-1] and len(cleaned_value) > 0
    
    # Unique characters count
    unique_characters = len(set(value))
    
    # Word count (split by whitespace)
    word_count = len(value.split())
    
    # SHA256 hash
    sha256_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()
    
    # Character frequency map
    character_frequency = {}
    for char in value:
        character_frequency[char] = character_frequency.get(char, 0) + 1
    
    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency
    }

def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """Parse natural language query into filters"""
    query = query.lower().strip()
    filters = {}
    
    # Word count patterns
    if "single word" in query or "one word" in query:
        filters["word_count"] = 1
    elif "two words" in query:
        filters["word_count"] = 2
    elif "three words" in query:
        filters["word_count"] = 3
    
    # Palindrome patterns
    if "palindromic" in query or "palindrome" in query:
        filters["is_palindrome"] = True
    
    # Length patterns
    length_match = re.search(r'longer than (\d+) characters?', query)
    if length_match:
        filters["min_length"] = int(length_match.group(1)) + 1
    
    length_match = re.search(r'shorter than (\d+) characters?', query)
    if length_match:
        filters["max_length"] = int(length_match.group(1)) - 1
    
    length_match = re.search(r'(\d+) characters?', query)
    if length_match and "word" not in query:
        filters["min_length"] = int(length_match.group(1))
        filters["max_length"] = int(length_match.group(1))
    
    # Character containment patterns
    char_match = re.search(r'contain(s|ing)? the letter ([a-z])', query)
    if char_match:
        filters["contains_character"] = char_match.group(2)
    
    char_match = re.search(r'contain(s|ing)? the character ([a-z])', query)
    if char_match:
        filters["contains_character"] = char_match.group(2)
    
    # Vowel detection
    if "vowel" in query:
        if "first vowel" in query:
            filters["contains_character"] = "a"
        else:
            # Default to 'a' if no specific vowel mentioned
            filters["contains_character"] = "a"
    
    return filters

def apply_filters(strings_data: Dict, filters: Dict) -> List[Dict]:
    """Apply filters to the strings data"""
    filtered_data = []
    
    for string_data in strings_data.values():
        include = True
        
        # Apply each filter
        if "is_palindrome" in filters and string_data["properties"]["is_palindrome"] != filters["is_palindrome"]:
            include = False
        
        if "min_length" in filters and string_data["properties"]["length"] < filters["min_length"]:
            include = False
        
        if "max_length" in filters and string_data["properties"]["length"] > filters["max_length"]:
            include = False
        
        if "word_count" in filters and string_data["properties"]["word_count"] != filters["word_count"]:
            include = False
        
        if "contains_character" in filters and filters["contains_character"] not in string_data["value"]:
            include = False
        
        if include:
            filtered_data.append(string_data)
    
    return filtered_data

@app.route('/strings', methods=['POST'])
def create_analyze_string():
    """Create/Analyze String endpoint"""
    # Validate request
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({"error": "Missing 'value' field in request body"}), 400
    
    if not isinstance(data['value'], str):
        return jsonify({"error": "Invalid data type for 'value' (must be string)"}), 422
    
    string_value = data['value']
    
    # Check if string already exists
    sha256_hash = hashlib.sha256(string_value.encode('utf-8')).hexdigest()
    if sha256_hash in strings_storage:
        return jsonify({"error": "String already exists in the system"}), 409
    
    # Compute properties
    properties = compute_string_properties(string_value)
    
    # Store the string data
    string_data = {
        "id": sha256_hash,
        "value": string_value,
        "properties": properties,
        "created_at": datetime.utcnow().isoformat() + 'Z'
    }
    
    strings_storage[sha256_hash] = string_data
    
    return jsonify(string_data), 201

@app.route('/strings/<string:string_value>', methods=['GET'])
def get_specific_string(string_value):
    """Get Specific String endpoint"""
    # Find string by value (this is inefficient for large datasets)
    for string_data in strings_storage.values():
        if string_data["value"] == string_value:
            return jsonify(string_data), 200
    
    return jsonify({"error": "String does not exist in the system"}), 404

@app.route('/strings', methods=['GET'])
def get_all_strings():
    """Get All Strings with Filtering endpoint"""
    # Get query parameters
    is_palindrome = request.args.get('is_palindrome', type=lambda x: x.lower() == 'true')
    min_length = request.args.get('min_length', type=int)
    max_length = request.args.get('max_length', type=int)
    word_count = request.args.get('word_count', type=int)
    contains_character = request.args.get('contains_character', type=str)
    
    # Validate contains_character if provided
    if contains_character and len(contains_character) != 1:
        return jsonify({"error": "contains_character must be a single character"}), 400
    
    # Build filters
    filters = {}
    if is_palindrome is not None:
        filters["is_palindrome"] = is_palindrome
    if min_length is not None:
        filters["min_length"] = min_length
    if max_length is not None:
        filters["max_length"] = max_length
    if word_count is not None:
        filters["word_count"] = word_count
    if contains_character is not None:
        filters["contains_character"] = contains_character
    
    # Apply filters
    filtered_data = apply_filters(strings_storage, filters)
    
    response = {
        "data": filtered_data,
        "count": len(filtered_data),
        "filters_applied": filters
    }
    
    return jsonify(response), 200

@app.route('/strings/filter-by-natural-language', methods=['GET'])
def natural_language_filter():
    """Natural Language Filtering endpoint"""
    query = request.args.get('query')
    
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    
    try:
        parsed_filters = parse_natural_language_query(query)
    except Exception as e:
        return jsonify({"error": "Unable to parse natural language query"}), 400
    
    # Check for conflicting filters
    if ("min_length" in parsed_filters and "max_length" in parsed_filters and 
        parsed_filters["min_length"] > parsed_filters["max_length"]):
        return jsonify({"error": "Conflicting filters: min_length greater than max_length"}), 422
    
    # Apply filters
    filtered_data = apply_filters(strings_storage, parsed_filters)
    
    response = {
        "data": filtered_data,
        "count": len(filtered_data),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed_filters
        }
    }
    
    return jsonify(response), 200

@app.route('/strings/<string:string_value>', methods=['DELETE'])
def delete_string(string_value):
    """Delete String endpoint"""
    # Find and delete string by value
    for hash_id, string_data in list(strings_storage.items()):
        if string_data["value"] == string_value:
            del strings_storage[hash_id]
            return '', 204
    
    return jsonify({"error": "String does not exist in the system"}), 404

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)