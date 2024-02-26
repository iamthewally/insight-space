import whisperx
import gc
import ollama
import torch
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
import subprocess

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
        audio_data = audio_queue.get()

        # Process the audio data
        # Save the audio data to a temporary file
        with tempfile.NamedTemporaryFile(delete=True, suffix='.webm') as tmp_file:
            tmp_file.write(audio_data)
            tmp_file.flush()  # Ensure data is written to disk
            tmp_file_path = tmp_file.name

            # Transcribe the audio file
            batch_size = 8
            audio = whisperx.load_audio(tmp_file_path)
            result = transcription_model.transcribe(audio, batch_size=batch_size)
            result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            formatted_transcript = format_transcript(result["segments"])

            print("*** transcription:")
            print(formatted_transcript)

            # Emit transcription results back to the client
            socketio.emit('transcription', {'transcript': formatted_transcript})

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
        # Concatenate the audio segments
        combined_audio = concatenate_audio_segments()

        # Generate a unique filename for the temporary file
        tmp_file_name = f"/tmp/{uuid.uuid4()}.webm"

        # Save the combined audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=True, suffix='.webm') as tmp_file:
            tmp_file.write(combined_audio)

            # Save the combined audio to a file
            with open('output.webm', 'wb') as f:
                f.write(combined_audio)
            # Flush the data to disk
            tmp_file.flush()

            # Get the path to the temporary file
            tmp_file_path = tmp_file.name

            # Transcribe the combined audio file
            batch_size = 8
            audio = whisperx.load_audio(tmp_file_path)
            result = transcription_model.transcribe(audio, batch_size=batch_size)
            result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            larger_transcript = format_transcript(result["segments"])

            print("****-> periodic transcription: -> ")
            print(larger_transcript)

            # Emit the larger transcription to the client
            socketio.emit('summary', {'summary_text': larger_transcript})

        # Clear the buffer, but not the audio segments
        transcription_buffer = ""

    except TypeError as e:
        print("Error: ", e)

    # Schedule the next execution
    threading.Timer(10, periodic_transcription).start()


def concatenate_audio_segments():
    """Concatenate the audio segments in the audio_segments array into a single audio file.

    This function uses the pydub library to concatenate the audio segments.
    It handles the conversion of the AudioSegment objects to bytes-like objects
    and ensures that the resulting audio file is in the correct format.

    Returns:
        A single AudioSegment object representing the concatenated audio.
    """

    # Combine the audio segments into a single AudioSegment object
    combined_audio = pydub.AudioSegment.empty()
    for segment in audio_segments:
        # Convert the AudioSegment object to a bytes-like object
        audio_segment = pydub.AudioSegment.from_file_using_temporary_files(
            io.BytesIO(segment)
        )
        # Append the audio segment to the combined audio
        combined_audio += audio_segment

    # Convert the combined audio to the desired format (e.g., 16-bit PCM)
    combined_audio = combined_audio.set_sample_width(2)
    combined_audio = combined_audio.set_frame_rate(16000)

    # Generate a unique filename for the temporary file
    with tempfile.NamedTemporaryFile(delete=True, suffix='.webm') as tmp_file:
        # Save the combined audio to the temporary file
        combined_audio.export(tmp_file.name, format="webm")

        # Return the temporary file as a bytes-like object
        return tmp_file.read()


def format_transcript(segments):
    transcript = ""
    current_speaker = None

    for segment in segments:
        speaker_id = segment.get("speaker", "Unknown")  # Default to "Unknown" if "speaker" key is missing
        if speaker_id != current_speaker:
            if current_speaker is not None:
                transcript += "\n"
            current_speaker = speaker_id
            transcript += f"Speaker {current_speaker}: "
        transcript += segment.get("text", "") + " "

    return transcript

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

@socketio.on('transcribe')
def handle_transcribe(data):
    print("*** begin handle_transcribe ******")

    # Check if the audio data is empty
    if not data['audio']:
        print("Empty audio data. Skipping.")
        return
    # queue it up!
    audio_queue.put(data['audio'])
    audio_segments.append(data['audio'])

    print("*** end handle_transcribe ******")

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


def periodic_transcription():
    """Periodic transcription task that uses the concatenated audio segments."""
    global transcription_buffer

    print("*** periodic_transcription:")

    if not audio_segments:
        print("No audio segments to transcribe. Skipping this iteration.")
        threading.Timer(10, periodic_transcription).start()
        return

    try:
        # Concatenate the audio segments
        combined_audio = concatenate_audio_segments()

        # Generate a unique filename for the temporary file
        tmp_file_name = f"/tmp/{uuid.uuid4()}.webm"

        # Save the combined audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=True, suffix='.webm') as tmp_file:
            tmp_file.write(combined_audio)

            # Flush the data to disk
            tmp_file.flush()

            # Get the path to the temporary file
            tmp_file_path = tmp_file.name

            # Transcribe the combined audio file
            batch_size = 8
            audio = whisperx.load_audio(tmp_file_path)
            result = transcription_model.transcribe(audio, batch_size=batch_size)
            result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            larger_transcript = format_transcript(result["segments"])

            print("****-> periodic transcription: -> ")
            print(larger_transcript)

            # Emit the larger transcription to the client
            socketio.emit('summary', {'summary_text': larger_transcript})

        # Clear the buffer, but not the audio segments
        transcription_buffer = ""

    except TypeError as e:
        print("Error: ", e)

    # Schedule the next execution
    threading.Timer(10, periodic_transcription).start()

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
    threading.Timer(10, periodic_transcription).start()

    # Start the transcription worker thread
    threading.Thread(target=transcription_worker, daemon=True).start()
    socketio.run(app, debug=True, port=2601, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), use_reloader=False)