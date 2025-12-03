"""
Broadcast service for system-wide broadcasts
"""
import json
import logging
from typing import Dict, Any

from chatService.models import Message
from chatService import get_redis_client, get_socketio

logger = logging.getLogger(__name__)


class BroadcastService:
    """Service for system broadcasts and notifications"""
    
    @staticmethod
    def broadcast_system_message(message: Message):
        """
        Broadcast a system message to all clients
        
        Args:
            message: Message instance to broadcast
        """
        try:
            socketio = get_socketio()
            redis_client = get_redis_client()
            
            message_dict = message.to_dict()
            
            # Broadcast via WebSocket
            socketio.emit('broadcast', message_dict, broadcast=True)
            
            # Publish to Redis channel for SSE
            redis_client.publish('broadcasts', json.dumps(message_dict))
            
            logger.info(f"System message {message.id} broadcasted successfully")
            
        except Exception as e:
            logger.error(f"Error broadcasting system message: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def publish_event(event_type: str, event_data: Dict[str, Any]):
        """
        Publish an event to SSE stream
        
        Args:
            event_type: Type of event
            event_data: Event data dictionary
        """
        try:
            from chatService.models import Event
            redis_client = get_redis_client()
            
            event = Event.create(event_type, event_data)
            event_dict = event.to_dict()
            
            # Publish to Redis channel for SSE
            redis_client.publish('events', json.dumps(event_dict))
            
            logger.info(f"Event {event_type} published successfully")
            
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}", exc_info=True)
            raise

