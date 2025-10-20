# String Analyzer API

A Flask-based RESTful API service that analyzes strings and stores their computed properties including length, palindrome status, character frequency, and more.

## 🚀 Features

- **String Analysis**: Compute comprehensive string properties
- **Flexible Filtering**: Filter strings by multiple criteria
- **Natural Language Queries**: Use plain English to search strings
- **RESTful Design**: Proper HTTP status codes and error handling
- **SHA256 Identification**: Unique hash-based string identification

## 📊 API Endpoints

### 1. Create/Analyze String
**POST** `/strings`
```bash
curl -X POST http://localhost:5000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "hello world"}'
```

**Response (201 Created):**
```json
{
  "id": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
  "value": "hello world",
  "properties": {
    "length": 11,
    "is_palindrome": false,
    "unique_characters": 8,
    "word_count": 2,
    "sha256_hash": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
    "character_frequency_map": {
      "h": 1, "e": 1, "l": 3, "o": 2, " ": 1, "w": 1, "r": 1, "d": 1
    }
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Get Specific String
**GET** `/strings/{string_value}`
```bash
curl http://localhost:5000/strings/hello%20world
```

### 3. Get All Strings with Filtering
**GET** `/strings?filters`
```bash
# Get palindromic strings between 5-20 characters with 2 words containing 'a'
curl "http://localhost:5000/strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a"
```

**Available Filters:**
- `is_palindrome` (boolean): `true` or `false`
- `min_length` (integer): Minimum string length
- `max_length` (integer): Maximum string length  
- `word_count` (integer): Exact word count
- `contains_character` (string): Single character to search for

### 4. Natural Language Filtering
**GET** `/strings/filter-by-natural-language?query={natural_language_query}`

**Examples:**
```bash
# Single word palindromes
curl "http://localhost:5000/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings"

# Strings longer than 10 characters
curl "http://localhost:5000/strings/filter-by-natural-language?query=strings%20longer%20than%2010%20characters"

# Palindromic strings containing 'a'
curl "http://localhost:5000/strings/filter-by-natural-language?query=palindromic%20strings%20that%20contain%20the%20letter%20a"
```

### 5. Delete String
**DELETE** `/strings/{string_value}`
```bash
curl -X DELETE http://localhost:5000/strings/hello%20world
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Local Development

1. **Clone and setup the project:**
```bash
# Create project directory
mkdir string-analyzer-api
cd string-analyzer-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Testing
```bash
# Run the test suite
python -m pytest tests/ -v

# Or run specific test file
python -m pytest tests/test_app.py
```

## 📦 Dependencies

### Production Dependencies
- **Flask==2.3.3**: Web framework
- **Werkzeug==2.3.7**: WSGI web application library

### Development Dependencies
- **pytest**: Testing framework

### Installation
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install manually
pip install Flask==2.3.3 Werkzeug==2.3.7
```

## 🌐 Deployment

### Railway Deployment
1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Deploy:
```bash
railway init
railway deploy
```

### Heroku Deployment
1. Create `Procfile`:
```
web: python app.py
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

### Other Deployment Options
- **AWS Elastic Beanstalk**
- **Google App Engine** 
- **PythonAnywhere**
- **DigitalOcean App Platform**

## 🔧 Environment Variables

No environment variables are required for basic operation. For production, consider setting:

```bash
FLASK_ENV=production
```

## 🧪 Testing the API

### Using curl
```bash
# Create a string
curl -X POST http://localhost:5000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "madam"}'

# Get all strings
curl http://localhost:5000/strings

# Natural language search
curl "http://localhost:5000/strings/filter-by-natural-language?query=palindromic%20strings"

# Delete a string
curl -X DELETE http://localhost:5000/strings/madam
```

### Using Python requests
```python
import requests

# Create string
response = requests.post('http://localhost:5000/strings', 
                        json={'value': 'test string'})
print(response.json())
```

## 📋 Properties Computed

For each analyzed string, the API computes:
- **length**: Number of characters
- **is_palindrome**: Boolean (case-insensitive)
- **unique_characters**: Count of distinct characters  
- **word_count**: Number of whitespace-separated words
- **sha256_hash**: Unique identifier hash
- **character_frequency_map**: Dictionary of character counts

## ❌ Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input or missing parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: String already exists
- `422 Unprocessable Entity`: Invalid data type
- `500 Internal Server Error`: Server error

## 📝 Notes

- Uses in-memory storage (resets on server restart)
- For production, consider adding a database (SQLite, PostgreSQL, etc.)
- Case-insensitive palindrome detection (ignores spaces and punctuation)
- Natural language parsing supports common query patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.