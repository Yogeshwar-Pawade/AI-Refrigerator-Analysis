import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

from lib.supabase_client import supabase

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    created_at: Optional[datetime] = None

class ChatConversation(BaseModel):
    id: str
    diagnosis_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = []

class CreateConversationRequest(BaseModel):
    diagnosis_id: str
    title: str

class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str

class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessage

async def create_conversation(request: CreateConversationRequest) -> ChatConversation:
    """Create a new chat conversation for a refrigerator diagnosis"""
    try:
        # Verify the diagnosis exists
        diagnosis_response = supabase.table("refrigerator_diagnoses").select("*").eq("id", request.diagnosis_id).execute()
        if not diagnosis_response.data:
            raise HTTPException(status_code=404, detail="Refrigerator diagnosis not found")
        
        # Create conversation
        conversation_data = {
            "diagnosis_id": request.diagnosis_id,
            "title": request.title
        }
        
        response = supabase.table("chat_conversations").insert(conversation_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        conversation = response.data[0]
        return ChatConversation(
            id=conversation["id"],
            diagnosis_id=conversation["diagnosis_id"],
            title=conversation["title"],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            messages=[]
        )
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

async def get_conversations(diagnosis_id: str) -> List[ChatConversation]:
    """Get all conversations for a refrigerator diagnosis"""
    try:
        response = supabase.table("chat_conversations").select("*").eq("diagnosis_id", diagnosis_id).order("created_at", desc=True).execute()
        
        conversations = []
        for conv_data in response.data:
            # Get messages for this conversation
            messages_response = supabase.table("chat_messages").select("*").eq("conversation_id", conv_data["id"]).order("created_at", desc=False).execute()
            
            messages = [
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    created_at=msg["created_at"]
                )
                for msg in messages_response.data
            ]
            
            conversations.append(ChatConversation(
                id=conv_data["id"],
                diagnosis_id=conv_data["diagnosis_id"],
                title=conv_data["title"],
                created_at=conv_data["created_at"],
                updated_at=conv_data["updated_at"],
                messages=messages
            ))
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

async def get_conversation(conversation_id: str) -> ChatConversation:
    """Get a specific conversation with its messages"""
    try:
        # Get conversation
        conv_response = supabase.table("chat_conversations").select("*").eq("id", conversation_id).execute()
        if not conv_response.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv_data = conv_response.data[0]
        
        # Get messages
        messages_response = supabase.table("chat_messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
        
        messages = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                created_at=msg["created_at"]
            )
            for msg in messages_response.data
        ]
        
        return ChatConversation(
            id=conv_data["id"],
            diagnosis_id=conv_data["diagnosis_id"],
            title=conv_data["title"],
            created_at=conv_data["created_at"],
            updated_at=conv_data["updated_at"],
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

async def send_message(request: SendMessageRequest) -> ChatResponse:
    """Send a message and get AI response about refrigerator diagnosis"""
    try:
        # Get conversation and verify it exists
        conversation = await get_conversation(request.conversation_id)
        
        # Get the original refrigerator diagnosis for context
        diagnosis_response = supabase.table("refrigerator_diagnoses").select("*").eq("id", conversation.diagnosis_id).execute()
        if not diagnosis_response.data:
            raise HTTPException(status_code=404, detail="Refrigerator diagnosis not found")
        
        diagnosis_data = diagnosis_response.data[0]
        
        # Save user message
        user_message_data = {
            "conversation_id": request.conversation_id,
            "role": "user",
            "content": request.message
        }
        
        user_msg_response = supabase.table("chat_messages").insert(user_message_data).execute()
        if not user_msg_response.data:
            raise HTTPException(status_code=500, detail="Failed to save user message")
        
        # Prepare comprehensive refrigerator context for AI
        context = f"""
REFRIGERATOR DIAGNOSIS CONTEXT:
File Name: {diagnosis_data.get('file_name', 'Unknown')}
Brand: {diagnosis_data.get('brand', 'Unknown')}
Model: {diagnosis_data.get('model', 'Unknown')}
Refrigerator Type: {diagnosis_data.get('refrigerator_type', 'Unknown')}
Issue Category: {diagnosis_data.get('issue_category', 'Unknown')}
Severity Level: {diagnosis_data.get('severity_level', 'Unknown')}

AUDIO SUMMARY:
{diagnosis_data.get('audio_summary', 'No audio summary available')}

DETAILED DIAGNOSIS:
{diagnosis_data.get('diagnosis_result', 'No diagnosis available')}

SOLUTIONS PROVIDED:
{diagnosis_data.get('solutions', 'No solutions available')}

PREVIOUS CONVERSATION:
"""
        
        # Add previous messages to context
        for msg in conversation.messages:
            context += f"{msg.role.capitalize()}: {msg.content}\n"
        
        # Add current user message
        context += f"User: {request.message}\n"
        
        # Generate AI response using Gemini
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-001')
            
            prompt = f"""You are an expert refrigerator technician and appliance repair specialist AI assistant. You help users with refrigerator-related questions based on a specific diagnosis that was performed on their refrigerator.

GUIDELINES FOR RESPONSES:
1. **Primary Focus**: Answer questions about the specific refrigerator diagnosis and solutions provided
2. **Additional Help**: Provide general refrigerator maintenance, troubleshooting, and repair advice
3. **Expertise Areas**: All refrigerator brands, models, common problems, repair techniques, safety procedures
4. **Safety First**: Always emphasize safety warnings for electrical work, refrigerant handling, or complex repairs
5. **Cost Awareness**: Provide realistic cost estimates for repairs vs replacement decisions
6. **When to Call Professionals**: Clearly advise when professional service is needed

CAPABILITIES:
- Explain diagnosis results in simple terms
- Clarify step-by-step repair instructions
- Suggest alternative solutions or temporary fixes
- Recommend maintenance schedules and best practices
- Help identify refrigerator parts and tools needed
- Provide troubleshooting for related issues
- Explain warranty considerations
- Compare repair costs vs replacement value

RESPONSE STYLE:
- Be conversational, helpful, and encouraging
- Use clear, jargon-free explanations
- Provide specific, actionable advice
- Include safety reminders when relevant
- Ask clarifying questions if needed

{context}

Based on the refrigerator diagnosis above and your expertise, please provide a helpful, detailed response to the user's question. If the question goes beyond the specific diagnosis, feel free to provide general refrigerator advice while relating it back to their specific situation when possible."""
            
            response = model.generate_content(prompt)
            ai_response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Save AI message
            ai_message_data = {
                "conversation_id": request.conversation_id,
                "role": "assistant",
                "content": ai_response_text
            }
            
            ai_msg_response = supabase.table("chat_messages").insert(ai_message_data).execute()
            if not ai_msg_response.data:
                raise HTTPException(status_code=500, detail="Failed to save AI message")
            
            return ChatResponse(
                conversation_id=request.conversation_id,
                message=ChatMessage(
                    role="assistant",
                    content=ai_response_text,
                    created_at=ai_msg_response.data[0]["created_at"]
                )
            )
        
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

async def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages"""
    try:
        # Delete conversation (messages will be deleted automatically due to CASCADE)
        response = supabase.table("chat_conversations").delete().eq("id", conversation_id).execute()
        return len(response.data) > 0
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}") 