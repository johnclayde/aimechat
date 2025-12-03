"""
Raw WebSocket routes for native WebSocket clients
"""
from flask import Blueprint, request, Response
import json
import logging
from datetime import datetime

from chatService.services import MessageService, BroadcastService
from chatService.services.connection_service import connection_service
from chatService import get_socketio, get_redis_client

logger = logging.getLogger(__name__)

ws_bp = Blueprint('ws', __name__)

# Store WebSocket connections (in production, use Redis or database)
raw_ws_connections = {}


def handle_raw_websocket(ws, path):
    """
    Handle raw WebSocket connection using eventlet WebSocket
    
    Args:
        ws: WebSocket connection object
        path: Connection path
    """
    import uuid
    import json as json_lib
    
    connection_id = str(uuid.uuid4())
    raw_ws_connections[connection_id] = ws
    connection_service.add_connection(connection_id)
    
    logger.info(f"Raw WebSocket connected: {connection_id}")
    
    try:
        # Send welcome message
        welcome_msg = {
            'type': 'connected',
            'message': 'Connected to server',
            'connection_id': connection_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        ws.send(json_lib.dumps(welcome_msg))
        
        # Handle incoming messages
        while True:
            try:
                message = ws.wait()
                if not message:
                    break
                
                # Parse message
                try:
                    data = json_lib.loads(message) if isinstance(message, str) else message
                except (json_lib.JSONDecodeError, TypeError):
                    # Handle binary or non-JSON messages
                    data = {'type': 'text', 'content': str(message), 'sender': 'anonymous'}
                
                # Process message
                message_type = data.get('type', 'text')
                content = data.get('content') or data.get('text') or data.get('data', '')
                sender = data.get('sender', 'anonymous')
                
                if content:
                    # Create and broadcast message
                    message_obj = MessageService.create_message(
                        message_type,
                        content,
                        sender,
                        data.get('format')
                    )
                    
                    # Broadcast via Socket.IO (for Socket.IO clients)
                    socketio = get_socketio()
                    socketio.emit('message', message_obj.to_dict(), broadcast=True)
                    
                    # Broadcast via Redis for SSE
                    redis_client = get_redis_client()
                    redis_client.publish('messages', json_lib.dumps(message_obj.to_dict()))
                    
                    # Echo back to sender
                    response = {
                        'type': 'message_received',
                        'message': message_obj.to_dict()
                    }
                    ws.send(json_lib.dumps(response))
                    
                    logger.info(f"Message {message_obj.id} processed from raw WebSocket")
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}", exc_info=True)
                error_msg = {
                    'type': 'error',
                    'message': str(e)
                }
                try:
                    ws.send(json_lib.dumps(error_msg))
                except:
                    break
                    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
    finally:
        # Cleanup
        raw_ws_connections.pop(connection_id, None)
        connection_service.remove_connection(connection_id)
        logger.info(f"Raw WebSocket disconnected: {connection_id}")
        try:
            ws.close()
        except:
            pass


@ws_bp.route('/ws/chat/')
def ws_chat_info():
    """
    WebSocket endpoint information
    
    ⚠️ IMPORTANT: This endpoint uses Socket.IO protocol, NOT raw WebSocket!
    
    Why native WebSocket fails:
    - Flask-SocketIO uses Socket.IO protocol (layered on top of WebSocket)
    - Native WebSocket sends raw frames, but server expects Socket.IO packets
    - Socket.IO requires HTTP polling handshake before WebSocket upgrade
    - Protocol mismatch causes connection failure
    
    Solution: You MUST use Socket.IO client library, not native WebSocket API.
    
    ❌ This will NOT work:
       const ws = new WebSocket('ws://10.88.216.33:8000/ws/chat/');
    
    ✅ This WILL work:
       const socket = io('http://10.88.216.33:8000', {path: '/ws/chat/'});
    """
    socketio_path = request.app.config.get('SOCKETIO_PATH', '/ws/chat/')
    
    return Response(
        json.dumps({
            'info': 'WebSocket endpoint (Socket.IO protocol)',
            'path': socketio_path,
            'warning': 'This endpoint uses Socket.IO protocol, NOT raw WebSocket',
            'why_native_websocket_fails': {
                'reason': 'Protocol mismatch',
                'explanation': 'Flask-SocketIO expects Socket.IO protocol packets, not raw WebSocket frames',
                'details': 'Socket.IO uses a layered protocol: Application → Socket.IO → Engine.IO → WebSocket'
            },
            'correct_usage': {
                'javascript': 'const socket = io("http://10.88.216.33:8000", {path: "/ws/chat/"});',
                'react_native': 'import io from "socket.io-client"; const socket = io("http://10.88.216.33:8000", {path: "/ws/chat/"});',
                'android_java': 'Socket socket = IO.socket("http://10.88.216.33:8000", options.setPath("/ws/chat/"));',
                'android_kotlin': 'val socket = IO.socket("http://10.88.216.33:8000", options.setPath("/ws/chat/"))'
            },
            'incorrect_usage': {
                'example': 'const ws = new WebSocket("ws://10.88.216.33:8000/ws/chat/");',
                'why_fails': 'Native WebSocket sends raw frames, but server expects Socket.IO protocol packets'
            },
            'server_info': {
                'port': 8000,
                'protocol': 'Socket.IO (WebSocket transport)',
                'supported_transports': ['websocket', 'polling'],
                'library': 'Flask-SocketIO (python-socketio)'
            },
            'documentation': 'See WHY_NATIVE_WEBSOCKET_FAILS.md for detailed explanation'
        }),
        status=200,
        mimetype='application/json'
    )

