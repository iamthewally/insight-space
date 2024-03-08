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
socketio = SocketIO(app, cors_allowed_origins="*",)  # Allow all origins for Socket.IO
audio_queue = Queue()
audio_segments = []
final_transcript = ""
processing_active = True

# Global lock for thread-safe operations on audio_segments
audio_segments_lock = threading.Lock()

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

from pydub import AudioSegment  # Make sure we have pydub imported to handle audio operations

def periodic_transcription():
    global transcription_buffer, final_transcript, audio_segments  # Ensure audio_segments is accessible
    print("*** periodic_transcription:")
    if not audio_segments:
        print("No audio segments to transcribe. Skipping this iteration.")
        threading.Timer(10, periodic_transcription).start()
        return

    with audio_segments_lock:  # Use the lock to safely manipulate audio_segments
        try:
            # Remember to convert audio_segments to AudioSegment instances if not already, and handle concatenation accordingly
            concatenated_audio = concatenate_audio_segments(audio_segments)  # Assuming this function returns an AudioSegment instance

            # Check the length of the concatenated audio
            audio_length_minutes = len(concatenated_audio) / (1000 * 60)  # AudioSegment.length is in milliseconds

            # If audio is longer than 10 minutes, adjust the processing logic as per requirements
            if len(audio_segments) > 100:
                print(f"Audio length is {audio_length_minutes} minutes, trimming to last 10 minutes for processing")            # IMPORTANT: Clear the processed audio segments to avoid re-processing
                audio_segments = [] 
                # Trim or split the audio here if necessary, assuming we just proceed with a simple condition

            # Transcribe the audio (consider modifying this function to accept AudioSegment instances if necessary)
            transcript = transcribe_audio_file(concatenated_audio, transcription_model, align_model, align_metadata, diarize_model, device)
            socketio.emit('summary', {'summary_text': final_transcript + transcript})
            if len(audio_segments) > 100:
                final_transcript += '\n' + transcript
        except Exception as e:  # Catching a generic exception to handle any unforeseen errors
            print("********************************************************\n PERIODIC TRANSCRIPTION FAILURE\n********************************************************", e, "********************************************************")

    # Schedule the next execution regardless of success/failure to ensure continuity
    threading.Timer(60, periodic_transcription).start()

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

@app.route('/asr', methods=['POST'])
def whisper_transcribe():
    if not request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = next(iter(request.files.values()))
    
    # Read the audio file content into a bytes-like object
    audio_data = audio_file.read()
    start_time = time.time()
    with tempfile.NamedTemporaryFile(delete=True, suffix='.webm') as tmp_file:
        tmp_file.write(audio_data)
        tmp_file.flush()  # Ensure data is written to disk
        tmp_file_path = tmp_file.name

        # Load the audio to find out the duration
        waveform, sample_rate = torchaudio.load(tmp_file_path)
        duration = waveform.shape[1] / float(sample_rate)

        # Transcribe the audio file
        batch_size = 6
        audio = whisperx.load_audio(tmp_file_path)
        result = transcription_model.transcribe(audio, batch_size=batch_size)
        print("*******************************************************")
        result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
        print ("Result: ",result)
        diarize_segments = diarize_model(audio)
        print("Diarized: ", diarize_segments)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        formatted_transcript = format_transcript(result["segments"])
        torch.cuda.empty_cache()
    elapsed_time = time.time() - start_time
    print(formatted_transcript)
    print(f"Duration of Audio: {duration:.2f} seconds")
    print(f"Processing Time: {elapsed_time:.2f} seconds")
    # Return the transcript as a JSON response
    print(jsonify({'transcript': formatted_transcript}, {'map': 'text'}))
    return jsonify({'transcript': formatted_transcript})


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
    # Clear the buffer and update the finalized transcript
    socketio.emit('summary', {'summary_text': transcript})
    final_transcript = transcript


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

    # Schedule the next execution
    threading.Timer(60, periodic_transcription).start()

    # Start the transcription worker thread
    threading.Thread(target=transcription_worker, daemon=True).start()
    socketio.run(app, debug=True, port=2601, host='0.0.0.0', use_reloader=False)
