import React, { Component } from 'react';
import { View, TextInput, TouchableOpacity, Text, StyleSheet, Platform, Alert, NativeEventEmitter, NativeModules } from 'react-native';
import AudioRecord from 'react-native-audio-record';
import { PermissionsAndroid } from 'react-native';
import RNFS from 'react-native-fs';
import { Socket } from 'socket.io-client';

// Check if RNFS is properly initialized
const isRNFSAvailable = (): boolean => {
  try {
    return typeof RNFS !== 'undefined' && !!RNFS.DocumentDirectoryPath;
  } catch (error) {
    console.warn('RNFS not properly initialized:', error);
    return false;
  }
};


interface InputContainerProps {
  inputText: string;
  setInputText: (text: string) => void;
  sendMessage: () => void;
  isConnected: boolean;
  // Reuse the existing Socket.IO connection from App.tsx
  wsRef: React.RefObject<Socket | null>;
}

interface InputContainerState {
  hasPermission: boolean;
  isRecording: boolean;
  isSubmitting: boolean;
  audioPath: string;
}

class InputContainer extends Component<InputContainerProps, InputContainerState> {

  // Request audio recording permission
  getAudioAuthorize = async (): Promise<void> => {
    try {
      if (Platform.OS === 'android') {
        const grants = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
        ]);

        if (
          grants['android.permission.RECORD_AUDIO'] === PermissionsAndroid.RESULTS.GRANTED ) {
          this.setState({ hasPermission: true });
        } else {
          Alert.alert(
            'Permission Required',
            'This app needs microphone access to record audio. Please enable it in settings.',
            [{ text: 'OK' }]
          );
        }
      } else {
        // iOS permissions are handled via Info.plist
        this.setState({ hasPermission: true });
      }
    } catch (error) {
      console.error('Permission error:', error);
      Alert.alert('Error', 'Failed to request microphone permission');
    }
  };

  
  private eventEmitter: NativeEventEmitter | null = null;
  private dataSubscription: any = null;

  constructor(props: InputContainerProps) {
    super(props);
    
    // Initialize audio path safely - always use the same file
    let audioPath: string;
    if (isRNFSAvailable()) {
      audioPath = RNFS.DocumentDirectoryPath + '/temp.wav';
    } else {
      audioPath = 'temp.wav';
    }
    
    // Initialize state
    this.state = {
      hasPermission: false,
      isRecording: false,
      isSubmitting: false,
      audioPath,
    };

    // Initialize audio recorder with options
    const options = {
      sampleRate: 16000,
      channels: 1,
      bitsPerSample: 16,
      audioSource: 6, // android only
      wavFile: 'temp.wav',
    };
    
    try {
      AudioRecord.init(options);
      console.log('Audio recorder initialized');
      
      // Set up event listener for audio data events to prevent "no listeners" warning
      if (NativeModules.RNAudioRecord) {
        this.eventEmitter = new NativeEventEmitter(NativeModules.RNAudioRecord);
        // Listen to 'data' events to prevent the warning
        this.dataSubscription = this.eventEmitter.addListener('data', () => {
          // Silently consume the data events to prevent warnings
        });
      }
    } catch (error) {
      console.error('Failed to initialize audio recorder:', error);
    }
  }

  componentWillUnmount() {
    // Cleanup if needed
    if (this.state.isRecording) {
      AudioRecord.stop().catch((err: any) => {
        console.error('Error stopping recording on cleanup:', err);
      });
    }
    
    // Remove event listener
    if (this.dataSubscription) {
      this.dataSubscription.remove();
      this.dataSubscription = null;
    }
  }

  componentDidMount() {
    this.getAudioAuthorize();
  }


  startRecording = async (): Promise<void> => {
    if (!this.state.hasPermission) {
      Alert.alert(
        'Permission Required',
        'This app needs microphone access to record audio. Please enable it in settings.'
      );
      return;
    }

    try {
      await AudioRecord.start();
      this.setState({ isRecording: true });
      console.log('Recording started');
    } catch (err) {
      console.error('Recording error:', err);
    }
  };

  stopRecording = async (): Promise<void> => {
    try {
      const uri = await AudioRecord.stop();
      this.setState({
        audioPath: uri,
        isRecording: false,
      });
      console.log('Recording stopped and saved as temp.wav at:', uri);
    } catch (err) {
      console.error('Failed to stop recording:', err);
      this.setState({ isRecording: false });
    }
  };

  handleRecordPressIn = (): void => {
    if (this.props.isConnected) {
      this.startRecording();
    }
  };

  handleRecordPressOut = async (): Promise<void> => {
    if (this.state.isRecording) {
      // Wait for recording to stop before submitting
      await this.stopRecording();
      // Small delay to ensure state is updated
      await new Promise(resolve => setTimeout(resolve, 100));
      this.submitRecording();
    }
  };

  // Submit recording via WebSocket
  submitRecording = async (): Promise<void> => {
    console.log('submitRecording');
    const { audioPath, isSubmitting, isRecording } = this.state;
    
    if (isRecording) {
      Alert.alert('Busy', 'Please stop recording or playback before submitting.');
      return;
    }

    if (isSubmitting) {
      Alert.alert('Busy', 'Please wait for the previous submission to complete.');
      return;
    }

    const socket = this.props.wsRef.current;

    if (!this.props.isConnected || !socket) {
      Alert.alert('Not Connected', 'Socket is not connected. Please wait for connection.');
      return;
    }

    this.setState({ isSubmitting: true, isRecording: false });

    try {
      // Read the audio file as base64
      let base64Audio: string;
      
      if (isRNFSAvailable()) {
        // Read file using RNFS (works on both Android and iOS)
        base64Audio = await RNFS.readFile(audioPath, 'base64');
      } else {
        // Fallback for iOS: read file using RNFS with full path
        const fullPath = audioPath.startsWith('/') ? audioPath : `/${audioPath}`;
        try {
          base64Audio = await RNFS.readFile(fullPath, 'base64');
        } catch (err) {
          // If that fails, try with file:// prefix removed
          const cleanPath = audioPath.replace('file://', '');
          base64Audio = await RNFS.readFile(cleanPath, 'base64');
        }
      }

      // Send audio data via existing Socket.IO connection
      if (socket && socket.connected) {
        socket.emit('message', {
          type: 'audio',
          content: base64Audio, // server expects 'content' field
          format: 'wav',
          timestamp: new Date().toISOString(),
        });

        console.log('Audio sent via Socket.IO');
        this.setState({ isSubmitting: false });
      } else {
        throw new Error('Socket.IO connection is not open');
      }
    } catch (error: any) {
      console.error('Failed to send audio:', error);
      Alert.alert('Upload Failed', error?.message || 'Failed to send audio recording');
      this.setState({ isSubmitting: false, isRecording: false });
    }
  };


  render(): JSX.Element {
    const { inputText, setInputText, sendMessage, isConnected } = this.props;
    const { isRecording } = this.state;

    return (
      <View style={styles.inputContainer}>
        <TouchableOpacity
          style={[
            styles.recordButton,
            isRecording && styles.recordButtonActive,
            !isConnected && styles.recordButtonDisabled,
          ]}
          onPressIn={this.handleRecordPressIn}
          onPressOut={this.handleRecordPressOut}
          disabled={!isConnected}
        >
          <Text style={styles.recordButtonText}>
            {isRecording ? '●' : '🎤'}
          </Text>
        </TouchableOpacity>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Describe an image to generate..."
          placeholderTextColor="#999"
          multiline
          maxLength={1000}
          onSubmitEditing={sendMessage}
          editable={isConnected}
        />
        <TouchableOpacity
          style={[styles.sendButton, !isConnected && styles.sendButtonDisabled]}
          onPress={sendMessage}
          disabled={!isConnected || !inputText.trim()}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    alignItems: 'flex-end',
  },
  recordButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  recordButtonActive: {
    backgroundColor: '#f44336',
    borderColor: '#d32f2f',
  },
  recordButtonDisabled: {
    backgroundColor: '#e0e0e0',
    opacity: 0.5,
  },
  recordButtonText: {
    fontSize: 20,
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
    fontSize: 16,
    maxHeight: 100,
    backgroundColor: '#f5f5f5',
  },
  sendButton: {
    backgroundColor: '#6200ee',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default InputContainer;

