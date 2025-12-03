"""
Chat Service Application Factory
"""
from flask import Flask
from flask_sse import sse
from flask_socketio import SocketIO
from celery import Celery
import redis
import logging

from config import Config

# Initialize extensions (will be initialized in create_app)
socketio = SocketIO()
celery = Celery('chatService')
redis_client = None

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """
    Application factory pattern for creating Flask app instances
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize Redis connection .Important
    global redis_client
    redis_client = redis.from_url(app.config['SSE_REDIS_URL'])
    
    # Initialize Flask-SSE
    app.register_blueprint(sse, url_prefix='/stream')
    
    # Determine async mode for Flask-SocketIO
    async_mode = app.config.get('SOCKETIO_ASYNC_MODE')
    if not async_mode:
        # Auto-detect available async mode
        try:
            import eventlet
            async_mode = 'eventlet'
            logger.info("Using eventlet as async mode")
        except ImportError:
            try:
                import gevent
                async_mode = 'gevent'
                logger.info("Using gevent as async mode")
            except ImportError:
                async_mode = 'threading'
                logger.info("Using threading as async mode (eventlet/gevent not available)")
    else:
        logger.info(f"Using configured async mode: {async_mode}")
    
    # Initialize Flask-SocketIO with error handling
    socketio_path = app.config.get('SOCKETIO_PATH', '/ws/chat/')
    
    # Handle CORS origins - Flask-SocketIO needs '*' as string when allowing all
    cors_origins = app.config['CORS_ORIGINS']
    if isinstance(cors_origins, list) and len(cors_origins) == 1 and cors_origins[0] == '*':
        cors_origins = '*'  # Flask-SocketIO accepts '*' as string to allow all origins
    
    try:
        socketio.init_app(
            app,
            cors_allowed_origins=cors_origins,
            async_mode=async_mode,
            logger=True,
            engineio_logger=True,
            path=socketio_path,
            message_queue=app.config['REDIS_URL']
        )
        logger.info(f"Flask-SocketIO initialized successfully with async_mode: {async_mode}, path: {socketio_path}")
    except ValueError as e:
        logger.error(f"Failed to initialize Flask-SocketIO with async_mode '{async_mode}': {e}")
        # Fallback to threading mode
        logger.warning("Falling back to threading mode")
        socketio.init_app(
            app,
            cors_allowed_origins=cors_origins,
            async_mode='threading',
            logger=True,
            engineio_logger=True,
            path=socketio_path
        )
    
    # Initialize Celery
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    celery.conf.task_serializer = 'json'
    celery.conf.accept_content = ['json']
    celery.conf.result_serializer = 'json'
    celery.conf.timezone = 'UTC'
    celery.conf.enable_utc = True
    
    # Register blueprints
    from chatService.routes import api_bp, sse_bp, ws_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(sse_bp, url_prefix='/api')
    app.register_blueprint(ws_bp)  # WebSocket routes at root level
    
    # Register WebSocket handlers
    from chatService.websocket import register_websocket_handlers
    register_websocket_handlers(socketio)
    
    # Register Celery tasks
    from chatService.tasks import register_celery_tasks
    register_celery_tasks(celery)
    
    logger.info("Application initialized successfully")
    
    return app


def get_redis_client():
    """Get Redis client instance"""
    return redis_client


def get_socketio():
    """Get SocketIO instance"""
    return socketio


def get_celery():
    """Get Celery instance"""
    return celery

