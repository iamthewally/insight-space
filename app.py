##filename:app.py
import whisperx
import gc
import ollama
import torch
import datetime
import io
import tempfile
import os
import threading
import pydub
import uuid
from flask_cors import CORS
from flask import Flask, render_template
from flask_socketio import SocketIO
from queue import Queue
from transcription import *
import subprocess
from flask import request, jsonify


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for all routes
socketio = SocketIO(app, cors_allowed_origins="*", )  # Allow all origins for Socket.IO
audio_queue = Queue()
audio_segments = []
processing_active = True

# Gemini API Key = AIzaSyDsz_wwN52subou8dbKP3X-vH0_vfx8MxY
# Declare the model variables
transcription_model = None
transcription_buffer = "" # Buffer for ongoing transcription
align_model = None
align_metadata = None
diarize_model = None
ollama_client = None

# Load models outside the request handling function
device = "cuda"
compute_type = "float16"
model_dir = "./models/"

def transcription_worker():
    global transcription_buffer

    while True:
        # Wait for audio data to be available in the queue
        # print("*** transcription worker waiting ")
        audio_data = audio_queue.get()

        transcript = transcribe_audio_file(audio_data, transcription_model, align_model, align_metadata, diarize_model, device)

        # Emit transcription results back to the client
        # print("*** transcription worker emit ")
        socketio.emit('transcription', {'transcript': transcript})

        # Indicate that the processing is complete
        audio_queue.task_done()

def periodic_transcription():
    """Periodic transcription task that uses the concatenated audio segments."""
    global transcription_buffer

    print("*** periodic_transcription:")

    if not audio_segments:
        print("No audio segments to transcribe. Skipping this iteration.")
        threading.Timer(10, periodic_transcription).start()
        return

    try:
        # Concatenate the audio segments in memory
        concatenated_audio = concatenate_audio_segments(audio_segments)

        # Save the concatenated audio to a file
        # timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # output_file_path = f"concatenated_audio_{timestamp}.webm"
        # with open(output_file_path, "wb") as output_file:
            # output_file.write(concatenated_audio)
        # print(f"Saved concatenated audio to {output_file_path}")
        
        # Transcribe the concatenated audio
        transcript = transcribe_audio_file(concatenated_audio, transcription_model, align_model, align_metadata, diarize_model, device)

        # Clear the buffer and audio segments
        socketio.emit('summary', {'summary_text': transcript})
        transcription_buffer = ""

        print("*** periodic_transcription:")

    except TypeError as e:
        print("Error: ", e)

    # Schedule the next execution
    threading.Timer(60, periodic_transcription).start()



def query_ollama(transcript, query):
    prompt = f"{transcript}\n{query}"
    response = ollama_client.generate(model='tinyllama', prompt=prompt)
    return response['message']['content']

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('transcribe_stream')
def handle_transcribe(data):
    # Check if the audio data is empty
    if not data['audio']:
        print("Empty audio data. Skipping.")
        return
    # queue it up!
    audio_queue.put(data['audio'])
    audio_segments.append(data['audio'])

@app.route('/transcribe', methods=['POST'])
def whisper_transcribe():
    # Check if the request contains audio data
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    # Get the audio file from the request
    audio_file = request.files['audio']

    # Read the audio file content into a bytes-like object
    audio_data = audio_file.read()

    # Transcribe the audio data using your transcription logic
    transcript = transcribe_audio_file(audio_data, transcription_model, align_model, align_metadata, diarize_model, device)

    # Return the transcript as a JSON response
    return jsonify({'transcript': transcript})


@socketio.on('summarize')
def handle_summarize(data):
    print("*** begin handle_summarize ***")
    print("* data:  ")
    print(data)
    transcript = data['transcript']
    query = "Summarize this DnD campaign"
    # this next line definitely works, but takes forever so we're jsut returning a literal for a moment
    # summary = query_ollama(transcript, query)
    summary = "Test transcription summary. "
    print("* summary: ")
    print(summary)
    print("*** end handle_summarize ***")

    # Emit summarization results back to the client
    socketio.emit('summary', {'summary': summary})



    # TODO: add the output of nvidia-smi to the startup so we know where we are with VRAM
if __name__ == '__main__':
    device = "cuda"
    compute_type = "float16"
    model_dir = "./models/"

    print("******** Clear and load models ********")
    print("empty garbage and torch cache...")
    torch.cuda.empty_cache()
    gc.collect()
    print("load transcription model...")
    transcription_model = whisperx.load_model("large-v3", device, compute_type=compute_type, download_root=model_dir, language='en')
    print("load alignment model...")
    align_model, align_metadata = whisperx.load_align_model(language_code='en', device=device)
    print("load diarization model...")
    diarize_model = whisperx.DiarizationPipeline(use_auth_token="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", device=device)
    ollama_client = ollama.Client(host='http://192.168.1.25:11434')
    print("******** All models loaded ********")

    # Start the periodic transcription task (new version)
    threading.Timer(60, periodic_transcription).start()

    # Start the transcription worker thread
    threading.Thread(target=transcription_worker, daemon=True).start()
    socketio.run(app, debug=True, port=2601, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), use_reloader=False)