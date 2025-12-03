# Android Connection Guide

## Problem Identified

Your Android app is trying to connect with an incorrect URL format:
- ❌ Wrong: `/10.88.216.33:8000` (missing protocol)
- ✅ Correct: `http://10.88.216.33:8000` (with protocol)

Also, **you must use Socket.IO client library**, not native WebSocket, because the server uses Socket.IO protocol.

## Solution

### 1. Add Socket.IO Client Library to Android

**For React Native:**
```bash
npm install socket.io-client
```

**For Native Android (Java/Kotlin):**
Add to `build.gradle`:
```gradle
dependencies {
    implementation 'io.socket:socket.io-client:2.1.0'
}
```

### 2. Correct Connection Code

#### React Native Example:
```javascript
import io from 'socket.io-client';

// Correct connection URL format
const SERVER_URL = 'http://10.88.216.33:8000';
const SOCKET_PATH = '/ws/chat/';

// Connect to server
const socket = io(SERVER_URL, {
    path: SOCKET_PATH,
    transports: ['websocket', 'polling'], // Fallback options
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5
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

socket.on('error', (error) => {
    console.error('Socket error:', error);
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
});

// Send a message
socket.emit('message', {
    type: 'text',
    content: 'Hello from Android',
    sender: 'android-user'
});
```

#### Native Android (Java) Example:
```java
import io.socket.client.IO;
import io.socket.client.Socket;
import io.socket.emitter.Emitter;

try {
    // Correct URL format with protocol
    IO.Options options = IO.Options.builder()
        .setPath("/ws/chat/")
        .setTransports(new String[]{"websocket", "polling"})
        .setReconnection(true)
        .setReconnectionDelay(1000)
        .setReconnectionAttempts(5)
        .build();
    
    Socket socket = IO.socket("http://10.88.216.33:8000", options);
    
    socket.on(Socket.EVENT_CONNECT, new Emitter.Listener() {
        @Override
        public void call(Object... args) {
            Log.d("Socket", "Connected to server");
        }
    });
    
    socket.on("connected", new Emitter.Listener() {
        @Override
        public void call(Object... args) {
            Log.d("Socket", "Server confirmation: " + args[0]);
        }
    });
    
    socket.on("message", new Emitter.Listener() {
        @Override
        public void call(Object... args) {
            Log.d("Socket", "Received message: " + args[0]);
        }
    });
    
    socket.on(Socket.EVENT_DISCONNECT, new Emitter.Listener() {
        @Override
        public void call(Object... args) {
            Log.d("Socket", "Disconnected: " + args[0]);
        }
    });
    
    socket.connect();
    
    // Send a message
    JSONObject message = new JSONObject();
    message.put("type", "text");
    message.put("content", "Hello from Android");
    message.put("sender", "android-user");
    socket.emit("message", message);
    
} catch (Exception e) {
    Log.e("Socket", "Connection error", e);
}
```

#### Native Android (Kotlin) Example:
```kotlin
import io.socket.client.IO
import io.socket.client.Socket
import org.json.JSONObject

val options = IO.Options.builder()
    .setPath("/ws/chat/")
    .setTransports(arrayOf("websocket", "polling"))
    .setReconnection(true)
    .setReconnectionDelay(1000)
    .setReconnectionAttempts(5)
    .build()

val socket = IO.socket("http://10.88.216.33:8000", options)

socket.on(Socket.EVENT_CONNECT) {
    Log.d("Socket", "Connected to server")
}

socket.on("connected") { args ->
    Log.d("Socket", "Server confirmation: ${args[0]}")
}

socket.on("message") { args ->
    Log.d("Socket", "Received message: ${args[0]}")
}

socket.on(Socket.EVENT_DISCONNECT) { args ->
    Log.d("Socket", "Disconnected: ${args[0]}")
}

socket.connect()

// Send a message
val message = JSONObject().apply {
    put("type", "text")
    put("content", "Hello from Android")
    put("sender", "android-user")
}
socket.emit("message", message)
```

## Important Points

1. **URL Format**: Always include `http://` or `https://` protocol
   - ✅ `http://10.88.216.33:8000`
   - ❌ `/10.88.216.33:8000`
   - ❌ `10.88.216.33:8000`

2. **Socket.IO Path**: Must specify the path `/ws/chat/` in connection options

3. **Network Permissions**: For Android, add to `AndroidManifest.xml`:
   ```xml
   <uses-permission android:name="android.permission.INTERNET" />
   ```

4. **Network Security**: For HTTP (not HTTPS), add to `AndroidManifest.xml`:
   ```xml
   <application
       android:usesCleartextTraffic="true"
       ...>
   ```

5. **Server Accessibility**: Ensure:
   - Server is running on `0.0.0.0:8000` (not just `localhost`)
   - Firewall allows port 8000
   - Android device can reach the server IP (same network or VPN)

## Testing Connection

### Test from Android device:
```bash
# Test if server is reachable
ping 10.88.216.33

# Test HTTP connection
curl http://10.88.216.33:8000/api/health
```

### Check Server Logs:
When Android app connects, you should see in server logs:
```
Client connected: <session-id>
Flask-SocketIO initialized successfully
```

## Troubleshooting

1. **Connection Refused**: Check if server is running and accessible
2. **Timeout**: Check firewall and network connectivity
3. **Protocol Error**: Make sure you're using Socket.IO client, not native WebSocket
4. **CORS Error**: Server already allows all origins (`CORS_ORIGINS=*`)

## Quick Fix for Your Current Code

If you're using React Native with native WebSocket, change to:

```javascript
// OLD (doesn't work):
const ws = new WebSocket("ws://10.88.216.33:8000/ws/chat/");

// NEW (correct):
import io from 'socket.io-client';
const socket = io("http://10.88.216.33:8000", {
    path: "/ws/chat/"
});
```

