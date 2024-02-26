import pydub
import tempfile
import os
import whisperx

def concatenate_audio_files(audio_files):
    """
    Concatenate a list of audio files into a single audio file.

    Args:
        audio_files: A list of audio file paths.

    Returns:
        A path to the concatenated audio file.
    """
    # Create a temporary file to store the concatenated audio
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
        concatenated_audio = pydub.AudioSegment.empty()

        for audio_file in audio_files:
            # Load each audio file and append it to the concatenated audio
            audio_segment = pydub.AudioSegment.from_file(audio_file)
            concatenated_audio += audio_segment

        # Export the concatenated audio to the temporary file
        concatenated_audio.export(tmp_file.name, format="webm")

        return tmp_file.name

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

def transcribe_audio_files(audio_files, transcription_model, align_model, align_metadata, diarize_model, device):
    """
    Transcribe a single audio file or concatenate and transcribe multiple audio files.

    Args:
        audio_files: A single audio file path or a list of audio file paths.
        transcription_model: The WhisperX transcription model.
        align_model: The WhisperX alignment model.
        align_metadata: Metadata for the alignment model.
        diarize_model: The WhisperX diarization model.
        device: The device to use for transcription (e.g., 'cuda').
    """
    if isinstance(audio_files, str):
        audio_files = [audio_files]

    if len(audio_files) > 1:
        # Concatenate multiple audio files before transcribing
        concatenated_audio_file = concatenate_audio_files(audio_files)
        audio_files = [concatenated_audio_file]

    for audio_file in audio_files:
        # Load the audio file
        audio = whisperx.load_audio(audio_file)

        # Transcribe the audio file
        batch_size = 8
        result = transcription_model.transcribe(audio, batch_size=batch_size)
        result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        transcript = format_transcript(result["segments"])

        # Print or store the transcript as needed
        print(f"Transcript for {audio_file}:")
        print(transcript)
        print("\n")

        # Clean up the temporary concatenated audio file if it was created
        if len(audio_files) > 1:
            os.remove(concatenated_audio_file)



# Old method, ignore this:
def concatenate_audio_segments_old():
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
