import React, { Component } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Platform,
  PermissionsAndroid,
} from 'react-native';
import AudioRecord from 'react-native-audio-record';

// Base URL for API - adjust as needed
const BASE_URL = 'http://192.168.119.2:8000';

interface RecorderState {
  hasPermission: boolean | undefined;
  audioPath: string;
  stop: boolean;
  currentTime: number;
  recording: boolean;
  playing: boolean;
}

interface RecorderProps {
  // Add any props if needed
}

class Recorder extends Component<RecorderProps, RecorderState> {
  constructor(props: RecorderProps) {
    super(props);
    
    // Initialize audio recorder
    const options = {
      sampleRate: 16000,
      channels: 1,
      bitsPerSample: 16,
      audioSource: 6, // android only
      wavFile: 'temp.wav',
    };
    AudioRecord.init(options);
    
    this.state = {
      hasPermission: undefined,
      audioPath: 'temp.wav',
      stop: false,
      currentTime: 0,
      recording: false,
      playing: false,
    };
  }

  componentDidMount() {
    this.getAudioAuthorize();
  }

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
          grants['android.permission.RECORD_AUDIO'] === PermissionsAndroid.RESULTS.GRANTED &&
          grants['android.permission.WRITE_EXTERNAL_STORAGE'] === PermissionsAndroid.RESULTS.GRANTED
        ) {
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


  // Start recording
  handleStartAudio = async (): Promise<void> => {
    if (!this.state.hasPermission) {
      Alert.alert(
        'Permission Required',
        'This app needs microphone access to record audio. Please enable it in settings.'
      );
      return;
    }

    try {
      await AudioRecord.start();
      this.setState({ recording: true, stop: false, currentTime: 0, playing: false });
      console.log('Recording started');
    } catch (err) {
      console.error('Recording error:', err);
      Alert.alert('Error', 'Failed to start recording');
    }
  };

  // Stop recording
  handleStopAudio = async (): Promise<void> => {
    try {
      const uri = await AudioRecord.stop();
      console.log('Recording stopped:', uri);
      this.setState({ stop: true, recording: false, audioPath: uri });
    } catch (error) {
      console.error('Stop recording error:', error);
      Alert.alert('Error', 'Failed to stop recording');
    }
  };

  // Toggle play/stop audio
  handleTogglePlay = async (): Promise<void> => {
    // Note: react-native-audio-record doesn't support playback
    // This would require react-native-sound or another playback library
    Alert.alert('Info', 'Playback feature requires additional library. Audio recording is saved.');
  };


  // Toggle recording (start or stop)
  handleToggleRecording = async (): Promise<void> => {
    if (this.state.recording) {
      await this.handleStopAudio();
    } else {
      await this.handleStartAudio();
    }
  };

  // Submit recording (placeholder for API call)
  handleSubmit = async (): Promise<void> => {
    const { stop, audioPath, recording, playing } = this.state;
    
    if (recording || playing) {
      Alert.alert('Busy', 'Please stop recording or playback before submitting.');
      return;
    }

    if (!stop) {
      Alert.alert('No Recording', 'Please record audio first');
      return;
    }

    try {
      // Build multipart form data
      const formData = new FormData();
      const uri = audioPath.startsWith('file://') ? audioPath : `file://${audioPath}`;
      formData.append('file', {
        uri,
        type: 'audio/wav',
        name: 'temp.wav',
      } as any);

      // Upload to server
      const response = await fetch(`${BASE_URL}/enalbum/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        body: formData,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Upload failed with status ${response.status}`);
      }

      const resultText = await response.text();
      Alert.alert('Upload Success', `Server response:\n${resultText}`);
    } catch (error: any) {
      Alert.alert('Upload Failed', error?.message || 'Unknown error');
    }
  };

  render(): JSX.Element {
    const { recording, stop, currentTime, hasPermission, playing } = this.state;

    return (
      <View style={styles.container}>
      
        
        <View style={styles.statusContainer}>
          <Text style={styles.statusText}>
            Permission: {hasPermission ? 'Granted' : 'Not Granted'}
          </Text>
          
          <Text style={styles.statusText}>
            Duration: {currentTime}s
          </Text>
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[
              styles.button, 
              recording ? styles.stopButton : styles.recordButton,
              playing && styles.disabledButton
            ]}
            onPress={this.handleToggleRecording}
            disabled={playing}
          >
            <Text style={styles.iconText}>
              {recording ? '⏹' : '🎤'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.button, 
              playing ? styles.stopButton : styles.playButton,
              (!stop || recording) && styles.disabledButton
            ]}
            onPress={this.handleTogglePlay}
            disabled={!stop || recording}
          >
            <Text style={styles.iconText}>
              {playing ? '⏹' : '▶️'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.button, 
              styles.submitButton,
              (!stop || recording) && styles.disabledButton
            ]}
            onPress={this.handleSubmit}
            disabled={!stop || recording}
          >
            <Text style={styles.iconText}>
              📤
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
    color: '#333',
  },
  statusContainer: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginBottom: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusText: {
    fontSize: 16,
    marginBottom: 5,
    color: '#666',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    gap: 15,
  },
  button: {
    flex: 1,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    minHeight: 60,
  },
  recordButton: {
    backgroundColor: '#e74c3c',
  },
  stopButton: {
    backgroundColor: '#95a5a6',
  },
  playButton: {
    backgroundColor: '#27ae60',
  },
  deleteButton: {
    backgroundColor: '#e67e22',
  },
  submitButton: {
    backgroundColor: '#3498db',
  },
  disabledButton: {
    backgroundColor: '#bdc3c7',
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  iconText: {
    fontSize: 24,
    color: '#fff',
  },
});

export default Recorder;
