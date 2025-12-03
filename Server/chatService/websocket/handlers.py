"""
WebSocket event handlers
"""
from flask import request
from flask_socketio import emit
from datetime import datetime
import logging

from chatService.services import MessageService, ConnectionService
from chatService.services.connection_service import connection_service
from chatService import get_celery

logger = logging.getLogger(__name__)


def register_websocket_handlers(socketio):
    """
    Register all WebSocket event handlers
    
    Args:
        socketio: Flask-SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        sid = request.sid
        connection_service.add_connection(sid)
        
        emit('connected', {
            'message': 'Connected to server',
            'sid': sid,
            'timestamp': datetime.utcnow().isoformat(),
            'connections': connection_service.get_connection_count()
        })
        
        logger.info(f"Client connected: {sid}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        sid = request.sid
        connection_service.remove_connection(sid)
        logger.info(f"Client disconnected: {sid}")
    
    @socketio.on('message')
    def handle_message(data):
        """Handle incoming message from client"""
        try:
            sid = request.sid

            # Type check
            if not isinstance(data, dict):
                emit('error', {'message': 'Invalid message format'})
                return

            # Attach sender sid so downstream (e.g. Celery task) can use it
            data['sid'] = sid

            # Process message using MessageService
            message, error = MessageService.process_incoming_message(data, sender_sid=sid)
            
            if error:
                emit('error', {'message': error})
                return
            
            # Message processed successfully
            logger.info(f"Message {message.id} handled successfully")
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            emit('error', {'message': f'Internal server error: {str(e)}'})
    
    
    logger.info("WebSocket handlers registered successfully")

