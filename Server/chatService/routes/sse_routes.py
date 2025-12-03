"""
SSE (Server-Sent Events) routes
"""
from flask import Blueprint, request, jsonify
import logging

from chatService.services import BroadcastService

logger = logging.getLogger(__name__)

sse_bp = Blueprint('sse_routes', __name__)


@sse_bp.route('/events', methods=['GET'])
def stream_events():
    """SSE endpoint for real-time data streaming"""
    from flask_sse import sse
    return sse.stream()


@sse_bp.route('/events/publish', methods=['POST'])
def publish_event():
    """Publish an event to SSE stream"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        event_type = data.get('event_type', 'message')
        event_data = data.get('data', {})
        
        if not isinstance(event_data, dict):
            return jsonify({'error': 'Event data must be a dictionary'}), 400
        
        # Publish event
        BroadcastService.publish_event(event_type, event_data)
        
        logger.info(f"Event {event_type} published via REST API")
        
        return jsonify({
            'success': True,
            'message': 'Event published'
        }), 200
        
    except Exception as e:
        logger.error(f"Error publishing event: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

