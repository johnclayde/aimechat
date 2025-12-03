"""
API routes blueprints
"""
from chatService.routes.api_routes import api_bp
from chatService.routes.sse_routes import sse_bp
from chatService.routes.ws_routes import ws_bp

__all__ = ['api_bp', 'sse_bp', 'ws_bp']

