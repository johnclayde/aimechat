# Client Connection Guide

## WebSocket Connection

The server is configured to accept WebSocket connections at `ws://localhost:8000/ws/chat/`.

### Important Note

Flask-SocketIO uses the **Socket.IO protocol**, which is built on top of WebSocket but includes additional features like automatic reconnection, rooms, namespaces, etc.

### Option 1: Use Socket.IO Client Library (Recommended)

For best compatibility, use the Socket.IO client library:

```html
<!-- Include Socket.IO client library -->
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<script>
    // Connect to the server
    const socket = io("http://localhost:8000", {
        path: "/ws/chat/"
    });

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('connected', (data) => {
        console.log('Server confirmation:', data);
    });

    socket.on('message', (data) => {
        console.log('Received message:', data);
    });

    // Send a message
    socket.emit('message', {
        type: 'text',
        content: 'Hello, server!',
        sender: 'client-user'
    });
</script>
```

### Option 2: Native WebSocket (Limited Support)

Native WebSocket API may work, but Socket.IO protocol includes handshaking that native WebSocket doesn't handle automatically. The connection might fail or be unstable.

```javascript
// This may not work reliably due to Socket.IO protocol
const ws = new WebSocket("ws://localhost:8000/ws/chat/");

ws.onopen = () => {
    console.log("WebSocket connected");
    // Send message
    ws.send(JSON.stringify({
        type: 'text',
        content: 'Hello',
        sender: 'user'
    }));
};

ws.onmessage = (event) => {
    console.log("Received:", event.data);
};
```

### Recommended: Use Socket.IO Client

The Socket.IO client library provides:
- Automatic reconnection
- Better error handling
- Protocol compatibility
- Room and namespace support
- Binary data support

Install via npm:
```bash
npm install socket.io-client
```

Or use CDN:
```html
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
```

## API Endpoints

### REST API

- **Health Check**: `GET http://localhost:8000/api/health`
- **Send Message**: `POST http://localhost:8000/api/message`
- **Broadcast**: `POST http://localhost:8000/api/messages/broadcast`
- **SSE Events**: `GET http://localhost:8000/api/events`
- **Publish Event**: `POST http://localhost:8000/api/events/publish`

### WebSocket Events

#### Client → Server

- `connect` - Automatic on connection
- `message` - Send a message
  ```javascript
  socket.emit('message', {
      type: 'text|image|audio',
      content: 'message content',
      sender: 'sender identifier',
      format: 'optional format'
  });
  ```
- `send_text` - Send text message
- `send_image` - Send image (base64)
- `send_audio` - Send audio (base64)
- `ping` - Keep-alive

#### Server → Client

- `connected` - Connection confirmation
- `message` - New message received
- `message_received` - Message delivery confirmation
- `broadcast` - System broadcast
- `notification` - System notification
- `pong` - Ping response
- `error` - Error message

## Example Client Code

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat Client</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type a message">
    <button onclick="sendMessage()">Send</button>

    <script>
        const socket = io("http://localhost:8000", {
            path: "/ws/chat/"
        });

        socket.on('connect', () => {
            console.log('Connected');
            addMessage('System', 'Connected to server');
        });

        socket.on('connected', (data) => {
            addMessage('System', data.message);
        });

        socket.on('message', (data) => {
            addMessage(data.sender, data.content);
        });

        socket.on('error', (data) => {
            addMessage('Error', data.message);
        });

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if (text) {
                socket.emit('message', {
                    type: 'text',
                    content: text,
                    sender: 'User'
                });
                input.value = '';
            }
        }

        function addMessage(sender, content) {
            const div = document.createElement('div');
            div.innerHTML = `<strong>${sender}:</strong> ${content}`;
            document.getElementById('messages').appendChild(div);
        }

        // Allow Enter key to send
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

