import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Redis configuration for Celery and SocketIO
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or REDIS_URL
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or REDIS_URL
    
    # Flask-SSE configuration
    SSE_REDIS_URL = os.environ.get('SSE_REDIS_URL') or REDIS_URL
    
    # CORS configuration (adjust as needed)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Flask-SocketIO async mode configuration
    # Options: 'eventlet', 'gevent', 'threading', 'gevent_uwsgi'
    # If not specified, will auto-detect available mode
    SOCKETIO_ASYNC_MODE = os.environ.get('SOCKETIO_ASYNC_MODE')
    
    # WebSocket configuration
    # Set to '/ws/chat/' to match client's expected path
    SOCKETIO_PATH = os.environ.get('SOCKETIO_PATH', '/ws/chat/')
    WS_PATH = os.environ.get('WS_PATH', '/ws/chat/')

