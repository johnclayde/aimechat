"""
Main application entry point
"""
import eventlet
eventlet.monkey_patch()  # <-- add this FIRST

import os
from chatService import create_app, get_socketio
from config import Config

# Create Flask application instance
app = create_app(Config)

# Get SocketIO instance for running the server
socketio = get_socketio()


if __name__ == '__main__':
    # Get configuration from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting server on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Run the application
    socketio.run(app, host=host, port=port, debug=debug, use_reloader=False)

