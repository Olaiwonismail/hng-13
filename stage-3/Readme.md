# Documentation

## WAEC Questions Agent with AI Explanations

### What It Does
This A2A agent provides random WAEC (West African Examinations Council) questions from various subjects along with AI-powered explanations. It helps students practice with past exam questions and understand the concepts behind each answer.

### Features
- 📚 **Multiple Subjects**: Mathematics, English, Chemistry, Physics, Biology, Economics, Government, Geography, Accounting, Commerce, Literature, History
- 🤖 **AI Explanations**: Uses Google Gemini to generate clear explanations for answers
- 🎯 **Random Questions**: Fetches random past WAEC questions from ALOC API
- 📊 **Structured Responses**: Returns questions, options, answers, and explanations in A2A format

### How to Run

#### Prerequisites
- Python 3.8+
- Gemini API key
- ALOC API access

#### Installation
1. **Clone and setup:**
```bash
pip install fastapi uvicorn pydantic httpx google-genai
```

2. **Set environment variables:**
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export PORT=5001
```

3. **Run the server:**
```bash
python app.py
```

#### API Usage
**Endpoint:** `POST /a2a/questions`

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "test-001",
  "method": "message/send",
  "params": {
    "message": {
      "kind": "message",
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "chemistry"
        }
      ],
      "messageId": "msg-001",
      "taskId": "task-001"
    }
  }
}
```

**Response:** Returns WAEC question with AI explanation

---

# Blog Post

## Building an Educational A2A Agent: WAEC Questions with AI Explanations

### The Journey Begins
As part of HNG 13, I built an educational A2A agent that provides random WAEC questions with AI-powered explanations. The goal was simple but powerful: help students practice with past exam questions while understanding the "why" behind each answer.

### Why A2A Protocol?
The Agent-to-Agent protocol provides a standardized way for AI agents to communicate. Instead of building yet another chatbot interface, I wanted to create something that could integrate seamlessly with existing A2A ecosystems.

### The Integration Process

#### Step 1: Starting with FastAPI
I chose Python and FastAPI because of their excellent async support and rapid development capabilities. The initial setup was straightforward:

```python
app = FastAPI(
    title="Question Bank Agent A2A",
    description="An agent that fetches educational questions with AI explanations",
    version="1.0.0"
)
```

#### Step 2: Integrating ALOC API
The ALOC API provides a treasure trove of past WAEC questions. Integration was smooth with `httpx`:

```python
async def fetch_question_from_aloc(subject: str):
    response = await client.get(
        ALOC_API_URL,
        params={"subject": subject.lower(), "random": "true"},
        headers={"AccessToken": ALOC_ACCESS_TOKEN}
    )
    return response.json()
```

#### Step 3: Adding AI Explanations with Gemini
This was the game-changer. Using Google's Gemini API, I could provide intelligent explanations:

```python
async def get_ai_explanation(question_data, subject):
    prompt = f"Explain this {subject} question: {question_data.question}"
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    return response.text
```

