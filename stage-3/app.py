# app.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime
import uvicorn
import os

# A2A Protocol Models
class MessagePart(BaseModel):
    kind: Literal["text", "data", "file"]
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
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
    params: MessageParams | ExecuteParams

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

# FastAPI App
app = FastAPI(
    title="Hehe Agent A2A",
    description="A simple agent that adds 'hehe' to messages",
    version="1.0.0"
)

def add_hehe_to_message(message: A2AMessage) -> A2AMessage:
    """Add 'hehe' to all text parts of a message"""
    modified_parts = []
    
    for part in message.parts:
        if part.kind == "text" and part.text:
            modified_text = f"{part.text} hehe"
            modified_parts.append(MessagePart(
                kind="text",
                text=modified_text
            ))
        else:
            # Keep non-text parts as-is
            modified_parts.append(part)
    
    return A2AMessage(
        role="agent",
        parts=modified_parts,
        messageId=str(uuid4()),
        taskId=message.taskId,
        metadata=message.metadata
    )

async def process_messages(
    messages: List[A2AMessage],
    context_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> TaskResult:
    """Process messages by adding 'hehe' to the last user message"""
    
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

    # Add 'hehe' to the message
    response_message = add_hehe_to_message(user_message)

    # Build artifacts (optional)
    artifacts = [
        Artifact(
            name="modified_message",
            parts=[MessagePart(kind="text", text="Message processed with hehe")]
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

@app.post("/a2a/hehe")
async def a2a_endpoint(request: Request):
    """Main A2A endpoint for hehe agent"""
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

        rpc_request = JSONRPCRequest(**body)

        # Extract messages
        messages = []
        context_id = None
        task_id = None

        if rpc_request.method == "message/send":
            messages = [rpc_request.params.message]
        elif rpc_request.method == "execute":
            messages = rpc_request.params.messages
            context_id = rpc_request.params.contextId
            task_id = rpc_request.params.taskId

        # Process messages
        result = await process_messages(
            messages=messages,
            context_id=context_id,
            task_id=task_id
        )

        # Build response
        response = JSONRPCResponse(
            id=rpc_request.id,
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
    return {"message": "Hehe Agent is running! Send POST requests to /a2a/hehe"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "hehe"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5005))
    uvicorn.run(app, host="0.0.0.0", port=port)