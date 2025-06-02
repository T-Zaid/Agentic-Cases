
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional, Any
from agents import Runner, TResponseInputItem, MessageOutputItem, ItemHelpers

from cases.shoe_store_case.context import UserContext
from cases.shoe_store_case.main import ShoeStoreAgent, voice_pipeline

app = FastAPI(title="Agentic Cases API",
              description="API for Agentic Cases.",
              version="1.0.0")

# In-memory storage for conversations
conversations = {}

# Pydantic models for request/response
class TextMessageRequest(BaseModel):
    message: str = Field(..., description="User's text message")
    user_id: str = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(..., description="User's email address")

class TextMessageResponse(BaseModel):
    response: str = Field(..., description="Agent's text response")

class VoiceSessionRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User's email address")

class HealthResponse(BaseModel):
    status: str
    message: str

class ConversationState(BaseModel):
    messages: List[dict]


@app.post("/chat/text", response_model=TextMessageResponse)
async def text_chat(request: TextMessageRequest):
    """
    Text-based chat endpoint for the shoe store agent
    """
    try:
        context = UserContext(user_id=request.user_id, email=request.email)
        input_items: List[TResponseInputItem] = [{"content": request.message, "role": "user"}]
        
        # Get or create conversation state
        conversation_key = f"{request.user_id}:{request.email}"
        if conversation_key in conversations:
            input_items = conversations[conversation_key]["messages"] + input_items
        
        result = await Runner.run(ShoeStoreAgent, input_items, context=context)
        
        # Extract response
        response_text = ""
        
        for new_item in result.new_items:
            if isinstance(new_item, MessageOutputItem):
                response_text += ItemHelpers.text_message_output(new_item)
                # agent_name = new_item.agent.name
        
        # Update conversation state
        conversations[conversation_key] = {
            "messages": result.to_input_list()
        }
        
        return TextMessageResponse(response=response_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )