# app.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any, Union
from uuid import uuid4
from datetime import datetime
import httpx
import uvicorn
import os
from google import genai

# A2A Protocol Models
class MessagePart(BaseModel):
    kind: Literal["text", "data", "file"]
    text: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    file_url: Optional[str] = None

class A2AMessage(BaseModel):
    kind: Literal["message"] = "message"
    role: Literal["user", "agent", "system"]
    parts: List[MessagePart]
    messageId: str = Field(default_factory=lambda: str(uuid4()))
    taskId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PushNotificationConfig(BaseModel):
    url: str
    token: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None

class MessageConfiguration(BaseModel):
    blocking: bool = True
    acceptedOutputModes: List[str] = ["text/plain"]
    pushNotificationConfig: Optional[PushNotificationConfig] = None

class MessageParams(BaseModel):
    message: A2AMessage
    configuration: MessageConfiguration = Field(default_factory=MessageConfiguration)

class ExecuteParams(BaseModel):
    contextId: Optional[str] = None
    taskId: Optional[str] = None
    messages: List[A2AMessage]

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str
    method: Literal["message/send", "execute"]
    params: Union[MessageParams, ExecuteParams, Dict[str, Any]]  # More flexible

class TaskStatus(BaseModel):
    state: Literal["working", "completed", "input-required", "failed"]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    message: Optional[A2AMessage] = None

class Artifact(BaseModel):
    artifactId: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    parts: List[MessagePart]

class TaskResult(BaseModel):
    id: str
    contextId: str
    status: TaskStatus
    artifacts: List[Artifact] = []
    history: List[A2AMessage] = []
    kind: Literal["task"] = "task"

class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: str
    result: Optional[TaskResult] = None
    error: Optional[Dict[str, Any]] = None

# ALOC API Response Models
class ALOCQuestionOption(BaseModel):
    a: Optional[str] = None
    b: Optional[str] = None
    c: Optional[str] = None
    d: Optional[str] = None
    e: Optional[str] = None

class ALOCQuestionData(BaseModel):
    id: int
    question: str
    option: ALOCQuestionOption
    section: str
    image: str
    answer: str
    solution: str
    examtype: str
    examyear: str

class ALOCAPIResponse(BaseModel):
    subject: str
    status: int
    data: ALOCQuestionData

# FastAPI App
app = FastAPI(
    title="Question Bank Agent A2A",
    description="An agent that fetches educational questions from ALOC API with AI explanations",
    version="1.0.0"
)

# API Configuration
ALOC_API_URL = "https://questions.aloc.com.ng/api/v2/q"
ALOC_ACCESS_TOKEN = os.getenv("ALOC_ACCESS_TOKEN")

# Initialize Gemini client
gemini_client = None

@app.on_event("startup")
async def startup_event():
    global gemini_client
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def fetch_question_from_aloc(subject: str) -> ALOCAPIResponse:
    """Fetch a random question from ALOC API for the given subject"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            ALOC_API_URL,
            params={
                "subject": subject.lower(),
                "random": "true"
            },
            headers={
                "AccessToken": ALOC_ACCESS_TOKEN
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ALOC API error: {response.text}"
            )
        
        return ALOCAPIResponse(**response.json())

async def get_ai_explanation(question_data: ALOCQuestionData, subject: str) -> str:
    """Get AI explanation for the question and correct answer using Gemini"""
    try:
        # Build the prompt for Gemini
        prompt = f"""
        Please provide a clear, concise explanation for this {subject} question:
        
        QUESTION: {question_data.question}
        
        OPTIONS:
        A. {question_data.option.a or 'N/A'}
        B. {question_data.option.b or 'N/A'}
        C. {question_data.option.c or 'N/A'}
        D. {question_data.option.d or 'N/A'}
        E. {question_data.option.e or 'N/A'}
        
        CORRECT ANSWER: {question_data.answer.upper()}
        
        Please explain:
        1. Why the correct answer is right
        2. Brief context about the concept
        3. Keep it educational and easy to understand (2-3 sentences max)
        
        Format your response as a clear explanation without markdown.
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        return response.text.strip()
        
    except Exception as e:
        return f"🤖 AI Explanation temporarily unavailable. Correct answer: {question_data.answer.upper()}"

def format_question_response(question_data: ALOCQuestionData, explanation: str, subject: str) -> str:
    """Format the question, options, and AI explanation into a readable string"""
    question_text = f"📚 {subject.upper()} Question:\n\n{question_data.question}\n\n"
    
    options = []
    for key, value in question_data.option.model_dump().items():
        if value:  # Only include non-null options
            options.append(f"{key.upper()}. {value}")
    
    question_text += "\n".join(options)
    question_text += f"\n\n✅ Correct Answer: {question_data.answer.upper()}"
    question_text += f"\n\n🤖 AI Explanation:\n{explanation}"
    question_text += f"\n\n📝 Exam: {question_data.examtype.upper()} {question_data.examyear}"
    
    if question_data.solution:
        question_text += f"\n💡 Original Solution: {question_data.solution}"
    
    return question_text

def extract_subject_from_message(user_message: A2AMessage) -> str:
    """Extract subject from user message, handling nested data structures"""
    subject = ""
    
    for part in user_message.parts:
        if part.kind == "text" and part.text:
            # Clean and extract subject from text
            clean_text = part.text.strip().lower()
            # Look for subject keywords in the text
            subjects = ["chemistry", "physics", "mathematics", "biology", 
                       "english", "economics", "government", "geography",
                       "accounting", "commerce", "literature", "history"]
            
            for subj in subjects:
                if subj in clean_text:
                    subject = subj
                    break
            if subject:
                break
                
        elif part.kind == "data" and part.data:
            # Handle nested data structure - recursively look for text in data
            for data_item in part.data:
                if isinstance(data_item, dict):
                    # Look for text fields in the data
                    for key, value in data_item.items():
                        if isinstance(value, str) and value.strip():
                            clean_value = value.strip().lower()
                            subjects = ["chemistry", "physics", "mathematics", "biology", 
                                       "english", "economics", "government", "geography",
                                       "accounting", "commerce", "literature", "history"]
                            
                            for subj in subjects:
                                if subj in clean_value:
                                    subject = subj
                                    break
                        if subject:
                            break
                if subject:
                    break
        if subject:
            break
    
    return subject or "chemistry"  # Default to chemistry if no subject found

async def process_messages(
    messages: List[A2AMessage],
    context_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> TaskResult:
    """Process messages by fetching questions from ALOC API and generating AI explanations"""
    
    # Generate IDs if not provided
    context_id = context_id or str(uuid4())
    task_id = task_id or str(uuid4())

    # Get the last user message
    user_message = None
    for msg in reversed(messages):
        if msg.role == "user":
            user_message = msg
            break
    
    if not user_message:
        raise ValueError("No user message found")

    # Extract subject from user message using the improved function
    subject = extract_subject_from_message(user_message)

    # Fetch question from ALOC API
    try:
        aloc_response = await fetch_question_from_aloc(subject)
        question_data = aloc_response.data
        
        # Get AI explanation
        explanation = await get_ai_explanation(question_data, subject)
        
        # Format the response
        response_text = format_question_response(question_data, explanation, subject)
        
    except Exception as e:
        response_text = f"❌ Error fetching question for subject '{subject}': {str(e)}\n\nAvailable subjects: chemistry, physics, mathematics, biology, english, economics, etc."

    # Create response message
    response_message = A2AMessage(
        role="agent",
        parts=[MessagePart(kind="text", text=response_text)],
        messageId=str(uuid4()),
        taskId=task_id
    )

    # Build artifacts with question metadata (only if we have question data)
    artifacts = []
    if 'question_data' in locals() and question_data:
        artifacts = [
            Artifact(
                name="question_data",
                parts=[
                    MessagePart(
                        kind="data",
                        data=[{
                            "subject": subject,
                            "question_id": question_data.id,
                            "exam_type": question_data.examtype,
                            "exam_year": question_data.examyear,
                            "correct_answer": question_data.answer,
                            "ai_explanation": explanation
                        }]
                    )
                ]
            )
        ]

    # Build history
    history = messages + [response_message]

    return TaskResult(
        id=task_id,
        contextId=context_id,
        status=TaskStatus(
            state="completed",
            message=response_message
        ),
        artifacts=artifacts,
        history=history
    )

@app.post("/a2a/agent/waecBot")
async def a2a_endpoint(request: Request):
    """Main A2A endpoint for question bank agent"""
    try:
        # Parse request body
        body = await request.json()

        # Validate JSON-RPC request
        if body.get("jsonrpc") != "2.0" or "id" not in body:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required"
                    }
                }
            )

        # Handle flexible params structure without strict Pydantic validation
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Extract messages based on method
        messages = []
        context_id = None
        task_id = None

        if method == "message/send":
            if "message" in params:
                # Convert message dict to A2AMessage
                message_dict = params["message"]
                message = A2AMessage(**message_dict)
                messages = [message]
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params: message is required for message/send"
                        }
                    }
                )
                
        elif method == "execute":
            messages_list = params.get("messages", [])
            # Convert each message dict to A2AMessage
            messages = [A2AMessage(**msg) for msg in messages_list]
            context_id = params.get("contextId")
            task_id = params.get("taskId")
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )

        # Process messages
        result = await process_messages(
            messages=messages,
            context_id=context_id,
            task_id=task_id
        )

        # Build response
        response = JSONRPCResponse(
            id=request_id,
            result=result
        )

        return response.model_dump()

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            }
        )

@app.get("/")
async def root():
    return {"message": "Question Bank Agent with AI Explanations is running! Send POST requests to /a2a/agent/waecBot"}

@app.get("/health")
async def health_check():
    gemini_status = "connected" if gemini_client else "disconnected"
    return {"status": "healthy", "agent": "question_bank", "gemini": gemini_status}

@app.get("/subjects")
async def available_subjects():
    """Endpoint to show available subjects"""
    subjects = [
        "chemistry", "physics", "mathematics", "biology", 
        "english", "economics", "government", "geography",
        "accounting", "commerce", "literature", "history"
    ]
    return {"available_subjects": subjects}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)