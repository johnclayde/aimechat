import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  Image,
} from 'react-native';
import io, { Socket } from 'socket.io-client';

import InputContainer from './components/InputContainer';

interface Message {
  id: string;
  text?: string;
  imageData?: string; // Base64 image data
  timestamp: Date;
  sender: string;
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [username, setUsername] = useState('Guest');
  const socketRef = useRef<Socket | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  // Socket.IO connection URL - Flask server with Socket.IO
  // Server URL from ANDROID_CONNECTION.md
  const SERVER_URL = 'http://10.252.7.33:8000';
  const SOCKET_PATH = '/ws/chat/';

  useEffect(() => {
    connectSocket();

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const connectSocket = () => {
    try {
      // Create Socket.IO connection
      const socket = io(SERVER_URL, {
        path: SOCKET_PATH,
        transports: ['websocket', 'polling'], // Fallback options
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
        timeout: 20000,
      });

      // Connection event
      socket.on('connect', () => {
        console.log('Socket.IO connected');
        setIsConnected(true);
        addSystemMessage('Connected to server');
      });

      // Server confirmation event
      socket.on('connected', (data: any) => {
        console.log('Server confirmation:', data);
        if (data.message) {
          addSystemMessage(data.message);
        }
      });

      // Receive messages
      socket.on('message', (data: any) => {
        console.log('Received message:', data);
        
        // Handle different message types
        if (data.type === 'image' && data.image_data) {
          const newMessage: Message = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            imageData: data.image_data,
            timestamp: new Date(data.timestamp || Date.now()),
            sender: data.sender || 'Server',
          };
          setMessages((prev) => [...prev, newMessage]);
        } else if (data.type === 'text' || data.text || data.content) {
          const newMessage: Message = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            text: data.text || data.content || data.message,
            timestamp: new Date(data.timestamp || Date.now()),
            sender: data.sender || data.username || 'Unknown',
          };
          setMessages((prev) => [...prev, newMessage]);
        } else {
          // Handle generic JSON messages
          const newMessage: Message = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            text: JSON.stringify(data),
            timestamp: new Date(),
            sender: data.sender || 'Server',
          };
          setMessages((prev) => [...prev, newMessage]);
        }
      });

      // Handle image responses (if server sends separate event)
      socket.on('image', (data: any) => {
        console.log('Received image:', data);
        if (data.status === 'success' && data.image_data) {
          const newMessage: Message = {
            id: data.message_id,
            imageData: data.image_data,
            timestamp: new Date(),
            sender: 'Server',
          };
          setMessages((prev) => [...prev, newMessage]);
        } else if (data.status === 'error') {
          addSystemMessage(data.message || 'Error receiving image');
        }
      });

      // Error event
      socket.on('error', (error: any) => {
        console.error('Socket error:', error);
        addSystemMessage('Connection error occurred');
      });

      // Disconnect event
      socket.on('disconnect', (reason: string) => {
        console.log('Socket disconnected:', reason);
        setIsConnected(false);
        addSystemMessage('Disconnected from server');
        
        // Attempt to reconnect (Socket.IO handles this automatically, but we can trigger manually)
        if (reason === 'io server disconnect') {
          // Server disconnected, need to reconnect manually
          setTimeout(() => {
            connectSocket();
          }, 3000);
        }
      });

      // Connection error
      socket.on('connect_error', (error: any) => {
        console.error('Connection error:', error);
        setIsConnected(false);
        addSystemMessage('Failed to connect to server');
      });

      socketRef.current = socket;
    } catch (error) {
      console.error('Failed to create Socket.IO connection:', error);
      addSystemMessage('Failed to connect to server');
    }
  };

  const addSystemMessage = (text: string) => {
    const systemMessage: Message = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      text,
      timestamp: new Date(),
      sender: 'System',
    };
    setMessages((prev) => [...prev, systemMessage]);
  };

  const sendMessage = () => {
    if (!inputText.trim() || !isConnected) {
      return;
    }

    const message: Message = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      text: inputText.trim(),
      timestamp: new Date(),
      sender: username,
    };

    // Add message to local state immediately for better UX
    setMessages((prev) => [...prev, message]);

    // Send message via Socket.IO
    if (socketRef.current && socketRef.current.connected) {
      try {
        // Send message in format expected by Flask-SocketIO server
        socketRef.current.emit('message', {
          type: 'text',
          content: inputText.trim(),
          text: inputText.trim(), // Some servers expect 'text' field
          sender: username,
          timestamp: new Date().toISOString(),
        });
      } catch (error) {
        console.error('Failed to send message:', error);
        addSystemMessage('Failed to send message');
      }
    } else {
      addSystemMessage('Not connected to server');
    }

    setInputText('');
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Navbar */}
        <View style={styles.navbar}>
          <Text style={styles.navbarTitle}>Chat App</Text>
          <View style={styles.navbarRight}>
            <View
              style={[
                styles.connectionIndicator,
                isConnected ? styles.connected : styles.disconnected,
              ]}
            />
            <Text style={styles.connectionText}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Text>
          </View>
        </View>

        {/* Message Window */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messageWindow}
          contentContainerStyle={styles.messageContent}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {messages.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>
                No messages yet. Start chatting!
              </Text>
            </View>
          ) : (
            messages.map((message) => (
              <View
                key={message.id}
                style={[
                  styles.messageBubble,
                  message.sender === username
                    ? styles.myMessage
                    : message.sender === 'System'
                    ? styles.systemMessage
                    : styles.otherMessage,
                ]}
              >
                {message.sender !== 'System' && (
                  <Text style={styles.messageSender}>{message.sender}</Text>
                )}
                
                {/* Display image if imageData exists */}
                {message.imageData ? (
                  <Image
                    source={{ uri: `data:image/jpeg;base64,${message.imageData}` }}
                    style={styles.messageImage}
                    resizeMode="contain"
                  />
                ) : null}
                
                {/* Display text if text exists */}
                {message.text ? (
                  <Text
                    style={[
                      styles.messageText,
                      message.sender === 'System' && styles.systemMessageText,
                    ]}
                  >
                    {message.text}
                  </Text>
                ) : null}
                
                <Text style={styles.messageTime}>{formatTime(message.timestamp)}</Text>
              </View>
            ))
          )}
        </ScrollView>

        {/* Input Area */}
        <InputContainer
          inputText={inputText}
          setInputText={setInputText}
          sendMessage={sendMessage}
          isConnected={isConnected}
          wsRef={socketRef}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  keyboardView: {
    flex: 1,
  },
  navbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#6200ee',
    paddingHorizontal: 16,
    paddingVertical: 12,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  navbarTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  navbarRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  connectionIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  connected: {
    backgroundColor: '#4caf50',
  },
  disconnected: {
    backgroundColor: '#f44336',
  },
  connectionText: {
    color: '#fff',
    fontSize: 12,
  },
  messageWindow: {
    flex: 1,
    backgroundColor: '#fff',
  },
  messageContent: {
    padding: 16,
    paddingBottom: 8,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    color: '#999',
    fontSize: 16,
    textAlign: 'center',
  },
  messageBubble: {
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    maxWidth: '80%',
  },
  myMessage: {
    backgroundColor: '#6200ee',
    alignSelf: 'flex-end',
  },
  otherMessage: {
    backgroundColor: '#e0e0e0',
    alignSelf: 'flex-start',
  },
  systemMessage: {
    backgroundColor: '#fff3cd',
    alignSelf: 'center',
    maxWidth: '90%',
  },
  messageSender: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
    color: '#666',
  },
  messageText: {
    fontSize: 16,
    color: '#000',
    marginBottom: 4,
  },
  systemMessageText: {
    color: '#856404',
    textAlign: 'center',
  },
  messageImage: {
    width: 250,
    height: 250,
    borderRadius: 8,
    marginBottom: 4,
    backgroundColor: '#f0f0f0',
  },
  messageTime: {
    fontSize: 10,
    color: '#999',
    alignSelf: 'flex-end',
  },
});

export default App;
