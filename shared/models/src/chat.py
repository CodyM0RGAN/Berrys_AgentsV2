from typing import Optional, List
from pydantic import BaseModel, Field

from .enums import MessageRole

class ChatMessage(BaseModel):
    """
    Model for a chat message.
    
    This model represents a message in a chat conversation, with a role
    (system, user, assistant, etc.) and content.
    """
    role: MessageRole
    content: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[dict] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
