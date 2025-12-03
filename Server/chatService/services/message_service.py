"""
Message service for handling message operations
"""
import json
import logging
from typing import Dict, Any, Tuple, Optional

from chatService.models import Message
from chatService import get_redis_client, get_socketio, get_celery

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message handling and broadcasting"""
    
    @staticmethod
    def create_message(message_type: str, content: str, sender: str, format: str = None) -> Message:
        """Create a new message"""
        return Message.create(message_type, content, sender, format)
    
    @staticmethod
    def validate_message(data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate message data"""
        if not data:
            return False, 'No data provided'
        
        content = data.get('content')
        if not content:
            return False, 'Content is required'
        
        message_type = data.get('type', 'text')
        if message_type not in ['text', 'image', 'audio']:
            return False, f'Invalid message type: {message_type}'
        
        return True, ''
    
    @staticmethod
    def normalize_message_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize incoming message data
        
        Args:
            data: Raw message data dictionary
            
        Returns:
            Normalized data dictionary
        """
        # Ensure 'content' field exists (use 'text' if 'content' is missing)
        if 'content' not in data or not data.get('content'):
            if 'text' in data and data.get('text'):
                data['content'] = data['text']
        
        return data
    
    @staticmethod
    def process_incoming_message(data: Dict[str, Any], sender_sid: str, 
                                  send_confirmation: bool = False,
                                  broadcast_to_others: bool = False,
                                  queue_async_task: bool = True) -> Tuple[Optional[Message], Optional[str]]:
        
        try:
            # Normalize data
            data = MessageService.normalize_message_data(data)
            
            # Validate message data
            is_valid, error_message = MessageService.validate_message(data)
            if not is_valid:
                return None, error_message
            
            # Extract message fields
            message_type = data.get('type', 'text')
            content = data.get('content')
            sender = data.get('sender', 'anonymous')
            format = data.get('format')
            
            # Create message object
            message = MessageService.create_message(message_type, content, sender, format)
            message_dict = message.to_dict()  # ← define here
            
            # Send confirmation to sender
            if send_confirmation:
                MessageService.send_to_sender(message, sender_sid)
            
            # Broadcast to all other clients
            if broadcast_to_others:
                MessageService.broadcast_message(message, include_sender=False, skip_sid=sender_sid)
            
            # Queue Celery task for async processing
            if queue_async_task:
                try:
                    message_dict['sid'] = sender_sid
                    celery = get_celery()
                    celery.send_task(
                        'chatService.process_message_async',
                        args=[message_dict],
                        kwargs={}
                    )
                    logger.debug(f"Celery task queued for message {message.id}")
                except Exception as celery_error:
                    logger.warning(f"Failed to queue Celery task: {str(celery_error)}")
            
            logger.info(f"Message {message.id} processed successfully from {sender}")
            return message, None
            
        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}", exc_info=True)
            return None, f'Internal server error: {str(e)}'
    
    @staticmethod
    def broadcast_message(message: Message, include_sender: bool = True, skip_sid: str = None):
        """Broadcast message via WebSocket and Redis"""
        try:
            socketio = get_socketio()
            redis_client = get_redis_client()
            
            message_dict = message.to_dict()
            
            # Debug: Log what's being broadcast
            logger.debug(f"Broadcasting message - type in dict: {message_dict.get('type')}, full dict: {message_dict}")
            
            # Broadcast via WebSocket
            if include_sender:
                socketio.emit('message', message_dict)
            else:
                if skip_sid:
                    socketio.emit('message', message_dict, skip_sid=skip_sid)
                else:
                    socketio.emit('message', message_dict)
            
            # Publish to Redis channel for SSE
            redis_client.publish('messages', json.dumps(message_dict))
            
            logger.info(f"Message {message.id} broadcasted successfully")
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def send_to_sender(message: Message, sid: str):
        """Send message confirmation to sender"""
        try:
            socketio = get_socketio()
            message_dict = message.to_dict()    
            socketio.emit('message', message_dict, room=sid)
            logger.debug(f"Message confirmation sent to {sid}")
        except Exception as e:
            logger.error(f"Error sending confirmation: {str(e)}", exc_info=True)

