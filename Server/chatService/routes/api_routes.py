"""
RESTful API routes
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from chatService.services import MessageService, BroadcastService
from chatService.models import Message

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'chat-service'
    }), 200


@api_bp.route('/message', methods=['POST'])
def send_message():
    """Send a message via REST API"""
    try:
        data = request.get_json()
        
        # Validate message data
        is_valid, error_message = MessageService.validate_message(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Create message
        message_type = data.get('type', 'text')
        content = data.get('content')
        sender = data.get('sender', 'anonymous')
        format = data.get('format')
        
        message = MessageService.create_message(message_type, content, sender, format)
        
        # Broadcast message
        MessageService.broadcast_message(message, include_sender=True)
        
        logger.info(f"Message {message.id} sent via REST API from {sender}")
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending message via REST API: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/messages/broadcast', methods=['POST'])
def broadcast_message():
    """Broadcast a message to all connected clients"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate message data
        is_valid, error_message = MessageService.validate_message(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Create system message
        message_type = data.get('type', 'text')
        content = data.get('content')
        sender = data.get('sender', 'system')
        format = data.get('format')
        
        message = MessageService.create_message(message_type, content, sender, format)
        
        # Broadcast system message
        BroadcastService.broadcast_system_message(message)
        
        logger.info(f"System message {message.id} broadcasted via REST API")
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

