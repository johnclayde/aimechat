"""
Celery tasks for message processing
"""
import json
import logging
from typing import Dict, Any

import requests  # make sure this is imported
from chatService import get_socketio, get_redis_client

import base64
from io import BytesIO
from PIL import Image
import os, uuid
from pathlib import Path

# Faster-Whisper model for local transcription
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None  # Will be checked at runtime
from faster_whisper import WhisperModel


logger = logging.getLogger(__name__)


    

def register_celery_tasks(celery):
    
    @celery.task(name='chatService.process_message_async')
    def process_message_async(message_data: Dict[str, Any]):
        
        try:
            logger.info(f"Processing message asynchronously: {message_data.get('id', 'unknown')}")
            
            # 1) Read message type and content
            msg_type = message_data.get('type', '')
            content = message_data.get('content', '')
            logger.info(f"[TASK] Message type={msg_type}, content preview={str(content)[:80]}")
            
            # 2) If message type is 'text', start async image generation task
            if msg_type == 'text' and content:
                try:
                    logger.info(f"[TASK] Queuing generate_image_async for message {message_data.get('id', 'unknown')}")
                    # Call the other Celery task with full message_data
                    generate_image_async.delay(message_data)
                except Exception as t_err:
                    logger.error(f"[TASK] Failed to queue generate_image_async: {t_err}", exc_info=True)
            else:
                logger.info(f"[TASK] Message type={msg_type} is not text, skipping image generation")

            # 3) if message type is 'audio'
            if msg_type == 'audio' and content:
                try:
                    logger.info(f"[TASK] Queuing generate_audio_async for message {message_data.get('id', 'unknown')}")
                    # Call the other Celery task with full message_data
                    whisper_audio_async.delay(message_data)
                except Exception as t_err:
                    logger.error(f"[TASK] Failed to queue generate_audio_async: {t_err}", exc_info=True)
                else:
                    logger.info(f"[TASK] Message type={msg_type} is not audio, skipping audio generation")
            # 4) Any other processing logic can be added here
            result = {
                'status': 'processed',
                'message_id': message_data.get('id'),
                'data': message_data
            }
            
            logger.info(f"Message {message_data.get('id', 'unknown')} processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message asynchronously: {str(e)}", exc_info=True)
            raise
    
    @celery.task(name='chatService.broadcast_notification_async')
    def broadcast_notification_async(notification: Dict[str, Any]):

        try:
            socketio = get_socketio()
            redis_client = get_redis_client()
            
            # Broadcast via WebSocket
            socketio.emit('notification', notification, broadcast=True)
            
            # Publish to Redis channel
            redis_client.publish('notifications', json.dumps(notification))
            
            logger.info(f"Notification broadcasted asynchronously: {notification.get('type', 'unknown')}")
            
            return {
                'status': 'broadcasted',
                'notification': notification
            }
            
        except Exception as e:
            logger.error(f"Error broadcasting notification: {str(e)}", exc_info=True)
            raise
    
    logger.info("Celery tasks registered successfully")
    
        
    @celery.task(name='chatService.generate_image_async')
    def generate_image_async(message_data: Dict[str, Any]):
        """
        Generate image based on prompt in message_data['content'] by calling remote API.
        
        Args:
            message_data: Message data dictionary (must contain 'content' as prompt)
        
        Returns:
            (result, error) tuple:
              - result: dict with prompt and images list (if success), or None
              - error: error message string or None
        """
        try:
            # 1) Read the message data and get the content as prompt
            image_prompt = message_data.get('content', '')
            logger.info(f"[TASK] Generating image for prompt: {image_prompt[:80]}")

            generate_image_URL = "http://localhost:9000/generate"
            headers = {"x-api-key": "1234567890"}

            # 2) Parse the prompt if it's a JSON string, otherwise use it directly
            if isinstance(image_prompt, str):
                try:
                    prompt_data = json.loads(image_prompt)
                    # Extract the text from the JSON message
                    prompt_text = prompt_data.get("text", image_prompt)
                except json.JSONDecodeError:
                    # If it's not JSON, use it as-is
                    prompt_text = image_prompt
            else:
                prompt_text = image_prompt

            json_data = {
                "positive": prompt_text,  # Use the actual prompt from the message
                "negative": "",           # Empty negative prompt
                "height": 512,
                "width": 512,
            }

            # 3) Call the remote image generation API
            response = requests.post(
                generate_image_URL,
                json=json_data,
                headers=headers,
                timeout=30,  # optional timeout
            )

            if response.status_code != 200:
                error = f"API Error: {response.status_code}"
                logger.error(f"[TASK] {error}")
                return None, error

            data = response.json()

            # 4) Validate response contains images
            if "images" not in data or len(data["images"]) == 0:
                error = "API Error: No images returned from API"
                logger.error(f"[TASK] {error}")
                return None, error

            # At this point, data["images"] is a list (e.g., base64 strings or URLs, depending on API)
            result = {
                "prompt": prompt_text,
                "images": data["images"],
            }

            logger.info(f"[TASK] Image generated successfully for prompt: {prompt_text[:80]}")

            # Get sender sid from message_data
            sender_sid = message_data.get('sid')

            try:
                from chatService import get_socketio
                socketio = get_socketio()

                if sender_sid:
                    # Send an "image" event back only to that client
                    img_data_base64 = data["images"][0]          # base64 string from API
                    img_bytes = base64.b64decode(img_data_base64)

                    img = Image.open(BytesIO(img_bytes))

                    # Optional: normalize to JPEG
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='JPEG')
                    img_bytes_jpeg = img_buffer.getvalue()
                    img_base64 = base64.b64encode(img_bytes_jpeg).decode('utf-8')

                    # Then emit img_base64 instead of data["images"][0]
                    socketio.emit(
                        'image',
                        {
                            'status': 'success',       # add this
                            'type': 'image',
                            'image_data': img_base64,
                            'message_id': message_data.get('id'),
                            'prompt': prompt_text,
                            'sender': 'Server',
                        },
                        room=sender_sid,
                    )
                    logger.info(f"[TASK] Image sent back to client sid={sender_sid}")
                else:
                    logger.warning("[TASK] No sender sid provided in message_data; cannot send image to specific client")

            except Exception as send_err:
                logger.error(f"[TASK] Failed to emit image to client: {send_err}", exc_info=True)

            # Also return the data to caller if needed
            return {
                "prompt": prompt_text,
                "images": [data["images"][0]], # Assuming the first image is the one to send back
            }, None

        except Exception as e:
            error = f"Error generating image: {str(e)}"
            logger.error(f"[TASK] {error}", exc_info=True)
            return None, error    

    @celery.task(name='chatService.whisper_audio_async')
    def whisper_audio_async(message_data: Dict[str, Any]):
        """
        Transcribe audio message using local Faster-Whisper model.
        Expects base64-encoded WAV data in message_data['content'].
        """
        result = " "
        model_path = "/home/andy/share/aiproj/servers/chatserver/model_from_whisper/models--deepdml--faster-whisper-large-v3-turbo-ct2/snapshots/44cbbd1adefe7387c83df88963a6d9ac4c9adea5"
        model_name = "deepdml/faster-whisper-large-v3-turbo-ct2"
        device = "cpu"   
        model_dir = os.path.join(os.getcwd(), "model_from_whisper")
        model = WhisperModel(model_name, device="cpu", compute_type="int8", download_root=model_dir, local_files_only=True)
        
        try:
            if WhisperModel is None:
                raise RuntimeError("faster-whisper is not installed or WhisperModel import failed")

            #get the audio base64 data from message_data
            audio_base64 = message_data.get('content', '')
            if not audio_base64:
                raise ValueError("No audio content provided in message_data['content']")

            #save the audio base64 data to a file
            temp_path = "temp.wav"
            with open(temp_path, 'wb') as f:
                f.write(base64.b64decode(audio_base64))

            segments, info = model.transcribe(temp_path, beam_size=5)
            for segment in segments:  
                result = result + f"{segment.text.lstrip()}\n\n"  

            message_data['content'] = result
            generate_image_async.delay(message_data)
            logger.info(f"[TASK] Transcription complete for message {message_data.get('id', 'unknown')}")
            return {"text": result}, None

        except Exception as e:
            logger.error(f"Error processing message asynchronously: {str(e)}", exc_info=True)
            return None, str(e)
    