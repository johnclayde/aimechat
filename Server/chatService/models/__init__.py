"""
Data models and schemas for the chat service
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime
import uuid


@dataclass
class Message:
    """Message data model"""
    id: str
    type: Literal['text', 'image', 'audio']
    content: str
    sender: str
    timestamp: str
    format: Optional[str] = None
    
    @classmethod
    def create(cls, message_type: str, content: str, sender: str, format: Optional[str] = None) -> 'Message':
        """Create a new message instance"""
        return cls(
            id=f"msg_{uuid.uuid4().hex[:12]}_{int(datetime.utcnow().timestamp() * 1000)}",
            type=message_type,
            content=content,
            sender=sender,
            timestamp=datetime.utcnow().isoformat(),
            format=format
        )
    
    def to_dict(self) -> dict:
        """Convert message to dictionary"""
        result = {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'sender': self.sender,
            'timestamp': self.timestamp
        }
        if self.format:
            result['format'] = self.format
        return result


@dataclass
class Event:
    """Event data model for SSE"""
    type: str
    data: dict
    timestamp: str
    
    @classmethod
    def create(cls, event_type: str, data: dict) -> 'Event':
        """Create a new event instance"""
        return cls(
            type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        return {
            'type': self.type,
            'data': self.data,
            'timestamp': self.timestamp
        }

