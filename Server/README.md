# Chat Service Backend

A professional, scalable Flask-based backend service for real-time chat with support for text, image, and audio messages.

## Features

- **RESTful API**: Complete REST API for frontend integration
- **WebSocket Support**: Real-time bidirectional communication via Flask-SocketIO
- **Server-Sent Events (SSE)**: Real-time data streaming for clients
- **Celery Integration**: Background task processing
- **Message Types**: Support for text, image (base64), and audio (base64) messages
- **Scalable Architecture**: Modular design with service layer separation

## Project Structure

```
Server/
├── app.py                 # Main application entry point
├── celery_worker.py       # Celery worker entry point
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── chatService/          # Main service package
│   ├── __init__.py       # Application factory
│   ├── models/           # Data models and schemas
│   ├── services/         # Business logic layer
│   ├── routes/           # API route handlers
│   ├── websocket/        # WebSocket event handlers
│   ├── tasks/            # Celery background tasks
│   └── utils/            # Utility functions
└── README.md
```

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Redis:**
   ```bash
   # Install Redis (if not already installed)
   # Ubuntu/Debian:
   sudo apt-get install redis-server
   
   # macOS:
   brew install redis
   
   # Start Redis:
   redis-server
   ```

3. **Configure environment variables:**
   Create a `.env` file (or set environment variables):
   ```env
   SECRET_KEY=your-secret-key-here
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   SSE_REDIS_URL=redis://localhost:6379/0
   CORS_ORIGINS=*
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   FLASK_DEBUG=False
   ```

## Running the Application

### Start the Flask Application

```bash
python app.py
```

Or using Flask CLI:
```bash
flask run --host=0.0.0.0 --port=5000
```

### Start the Celery Worker

In a separate terminal:
```bash
celery -A celery_worker.celery worker --loglevel=info
```

Or:
```bash
python celery_worker.py
```

## API Endpoints

### REST API

#### Health Check
- **GET** `/api/health`
  - Returns service health status

#### Send Message
- **POST** `/api/message`
  - Request body:
    ```json
    {
      "type": "text|image|audio",
      "content": "message content or base64 encoded data",
      "sender": "sender identifier",
      "format": "optional format (png, jpg, wav, mp3, etc.)"
    }
    ```

#### Broadcast Message
- **POST** `/api/messages/broadcast`
  - Broadcasts a system message to all connected clients
  - Same request body format as `/api/message`

#### SSE Events
- **GET** `/api/events`
  - Server-Sent Events stream endpoint

#### Publish Event
- **POST** `/api/events/publish`
  - Request body:
    ```json
    {
      "event_type": "event type name",
      "data": {}
    }
    ```

### WebSocket Events

Connect to WebSocket at the root URL (same as Flask app).

#### Client → Server Events

- `connect` - Client connection
- `message` - Send a message
  ```json
  {
    "type": "text|image|audio",
    "content": "message content",
    "sender": "sender identifier",
    "format": "optional format"
  }
  ```
- `send_text` - Send text message
  ```json
  {
    "text": "message text",
    "sender": "sender identifier"
  }
  ```
- `send_image` - Send image message (base64)
  ```json
  {
    "image": "base64 encoded image",
    "sender": "sender identifier",
    "format": "png|jpg|jpeg"
  }
  ```
- `send_audio` - Send audio message (base64)
  ```json
  {
    "audio": "base64 encoded audio",
    "sender": "sender identifier",
    "format": "wav|mp3|ogg"
  }
  ```
- `ping` - Keep-alive ping

#### Server → Client Events

- `connected` - Connection confirmation
- `message` - New message received
- `message_received` - Message delivery confirmation
- `broadcast` - System broadcast message
- `notification` - System notification
- `pong` - Ping response
- `error` - Error message

## Architecture

### Service Layer

The application follows a clean architecture pattern:

- **Models**: Data structures and schemas (`chatService/models/`)
- **Services**: Business logic (`chatService/services/`)
  - `MessageService`: Message creation and broadcasting
  - `BroadcastService`: System broadcasts and events
  - `ConnectionService`: WebSocket connection management
- **Routes**: API endpoints (`chatService/routes/`)
- **WebSocket**: Real-time event handlers (`chatService/websocket/`)
- **Tasks**: Background processing (`chatService/tasks/`)

### Application Factory Pattern

The application uses Flask's application factory pattern for better testability and scalability. The `create_app()` function in `chatService/__init__.py` initializes all components.

## Development

### Code Structure

- **Separation of Concerns**: Business logic separated from route handlers
- **Service Layer**: Reusable services for common operations
- **Error Handling**: Comprehensive error handling with logging
- **Type Hints**: Type annotations for better code clarity
- **Logging**: Structured logging throughout the application

### Adding New Features

1. **New API Endpoint**: Add route in `chatService/routes/api_routes.py`
2. **New WebSocket Event**: Add handler in `chatService/websocket/handlers.py`
3. **New Service**: Create service class in `chatService/services/`
4. **New Celery Task**: Add task in `chatService/tasks/message_tasks.py`

## Production Considerations

1. **Security**:
   - Change `SECRET_KEY` to a strong random value
   - Configure proper CORS origins
   - Add authentication/authorization
   - Use HTTPS

2. **Scalability**:
   - Use Redis pub/sub for multi-instance deployments
   - Consider using a message queue (RabbitMQ) for Celery
   - Use a production WSGI server (Gunicorn, uWSGI)
   - Implement connection pooling

3. **Monitoring**:
   - Add application monitoring (e.g., Prometheus, New Relic)
   - Set up log aggregation
   - Monitor Redis and Celery workers

4. **Deployment**:
   - Use environment-specific configuration
   - Containerize with Docker
   - Use process managers (systemd, supervisord)

## License

This project is provided as-is for development purposes.

