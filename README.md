# String Analyzer API

A RESTful API service that analyzes strings and stores their computed properties.

## Features

- Analyze string properties (length, palindrome check, unique characters, word count, SHA256 hash, character frequency)
- Filter strings by various criteria
- Natural language query support
- RESTful endpoints with proper HTTP status codes

## Endpoints

### 1. Create/Analyze String
**POST** `/strings`
```json
{
  "value": "string to analyze"
}