from flask import Flask, render_template, request
from flask_socketio import SocketIO
import numpy as np
import io
import subprocess
import whisper
from pydub import AudioSegment
import threading
from queue import Queue


app = Flask(__name__)
socketio = SocketIO(app, logger=True, engineio_logger=True)

model = whisper.load_model("base")
#model = whisper.load_model("large-v3")
print("Whisper model loaded successfully.")


def calculate_duration(audio_np, sample_rate=16000):
    """
    Calculate the duration of the audio in seconds.
    audio_np: The numpy array containing the audio samples.
    sample_rate: The number of audio samples per second.
    """
    num_samples = audio_np.shape[0]
    duration = num_samples / sample_rate
    return duration

client_audio_chunks = {}  # Stores audio data
client_audio_duration = {}  # Tracks the duration of audio per client


def process_audio_chunk(audio_data_bytes):
    # Convert bytes data to an audio segment
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_data_bytes), format="mp4")

    # Sample rate from the audio segment
    sample_rate = audio_segment.frame_rate
    print(f"Sample Rate: {sample_rate} Hz")

    # For codec, we'd typically need to interact with the data as a file.
    # One approach is to temporarily save the audio data to a file and then inspect it.
    temp_file = "temp_audio.mp4"
    with open(temp_file, "wb") as f:
        f.write(audio_data_bytes)

    # Now using ffmpeg to inspect the temporary audio file for codec information
    command = ['ffmpeg', '-i', temp_file, '-hide_banner']
    result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    # Parsing ffmpeg output for codec information
    for line in result.stderr.split('\n'):
        if "Audio:" in line:
            print("Audio details:", line.strip())
            break

def process_audio_data(audio_data):
    try:
        # The actual processing logic here, including transcription
        result = model.transcribe(audio_data)
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
    # Initialize storage for this client

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Optionally, process remaining audio or clean up
    if request.sid in client_audio_chunks:
        del client_audio_chunks[request.sid]

def transcribe_audio(audio_data):
    try:
        print("Transcription started. Data size:", len(audio_data))
        # Read audio data from BytesIO and convert to an AudioSegment
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp4")

        # convert to expected format
        if audio_segment.frame_rate != 16000: # 16 kHz
            audio_segment = audio_segment.set_frame_rate(16000)
        if audio_segment.sample_width != 2:   # int16
            audio_segment = audio_segment.set_sample_width(2)
        if audio_segment.channels != 1:       # mono
            audio_segment = audio_segment.set_channels(1)        
        arr = np.array(audio_segment.get_array_of_samples())
        arr = arr.astype(np.float32)/32768.0


        # Transcribe using Whisper model
        print("Transcribing...")
        result = model.transcribe(arr)
        print(f"Transcription result: {result['text']}")

        # Emit transcription result with acknowledgment
        def ack():
            print("Transcription result successfully received by client")

        socketio.emit('transcription', {'text': result['text']})
        


    except Exception as e:
        print("Error in transcription:", e)

        # Emit error with acknowledgment
        def error_ack():
            print("Error message successfully received by client")

        socketio.emit('error', {'message': str(e)}, callback=error_ack)

def align_audio_data(audio_data, alignment=2):
    """Ensure audio data byte length is a multiple of `alignment`."""
    remainder = len(audio_data) % alignment
    if remainder:
        # Pad the audio data to make it aligned
        audio_data += b'\x00' * (alignment - remainder)
    return audio_data

@socketio.on('audio_chunk')
def handle_audio_chunk(audio_data):
    sid = request.sid
    if sid not in client_audio_chunks:
        print("Initializing audio storage for client:", sid)
        client_audio_chunks[sid] = []
        client_audio_duration[sid] = 0
    process_audio_chunk(audio_data)

    # Align the audio data before conversion
    aligned_audio_data = align_audio_data(audio_data)

    # Convert the binary data to a numpy array
    audio_np = np.frombuffer(aligned_audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    #duration = calculate_duration(audio_np)
    
    print("Transcribing...")
    result = model.transcribe(audio_np)
    print(f"Transcription result: {result['text']}")
    # Update the stored audio data and duration
    client_audio_chunks[sid].append(audio_np)
    #client_audio_duration[sid] += duration

    print(f"Audio Array New Size: {client_audio_duration[sid]}")
    # if client_audio_duration[sid] > 0:
        # Concatenate the audio chunks into a single array
        # full_audio = np.concatenate(client_audio_chunks[sid])
        # Use Flask-SocketIO's start_background_task to run the processing in a background task
        # process_audio_chunk(audio_np)
    socketio.start_background_task(process_audio_data, audio_np)
        
        # Reset the client's stored audio and duration
        # client_audio_chunks[sid] = []
        # client_audio_duration[sid] = 0

if __name__ == '__main__':
    print("Starting Flask socketio server...")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=True)
