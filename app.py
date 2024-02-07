from flask import Flask, render_template, request
from flask_socketio import SocketIO
import numpy as np
from pydub import AudioSegment
import whisper
import io

app = Flask(__name__)
socketio = SocketIO(app, logger=True, engineio_logger=True)

#model = whisper.load_model("base")
model = whisper.load_model("medium")
print("Whisper model loaded successfully.")

client_audio_chunks = {}  # Audio data storage per client

def calculate_duration(audio_np):
    """Calculate the duration of the audio in seconds from the numpy array."""
    return audio_np.shape[0] / 16000  # Assuming 16kHz sample rate

def convert_audio_for_transcription(audio_data_bytes):
    """Converts received audio bytes to the format expected by Whisper."""
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_data_bytes), format="mp4").set_frame_rate(16000).set_sample_width(2).set_channels(1)
    audio_np = np.array(audio_segment.get_array_of_samples(), dtype=np.float32) / 32768.0  # Normalize
    return audio_np

def transcribe_audio(audio_np):
    """Transcribes audio using the Whisper model."""
    try:
        result = model.transcribe(audio_np)
        text = result['text'].strip()
        print(f"Transcription result: {text}")
        socketio.emit('transcription', {'text': text})
    except Exception as e:
        print(f"Error in processing audio data: {e}")
        socketio.emit('error', {'message': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    client_audio_chunks.pop(request.sid, None)

@socketio.on('audio_chunk')
def handle_audio_chunk(audio_data):
    sid = request.sid
    if sid not in client_audio_chunks:
        client_audio_chunks[sid] = []

    audio_np = convert_audio_for_transcription(audio_data)
    client_audio_chunks[sid].append(audio_np)  # Store for potential future use

    print("Transcribing...")
    socketio.start_background_task(transcribe_audio, audio_np)

if __name__ == '__main__':
    print("Starting Flask socketio server...")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
