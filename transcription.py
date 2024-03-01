##filename:transcription.py
import pydub
import tempfile
import torch
import os
import io
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
            transcript += f"{current_speaker}: "
        transcript += segment.get("text", "") + " "

    return transcript

    
    # Accepts a webm audio file and returns transcription as a string
def transcribe_audio_file(audio_data, transcription_model, align_model, align_metadata, diarize_model, device):
    # Save the audio data to a temporary file
    print("**** transcribe_file -> start ****")
    with tempfile.NamedTemporaryFile(delete=True, suffix='.webm') as tmp_file:
        tmp_file.write(audio_data)
        tmp_file.flush()  # Ensure data is written to disk
        tmp_file_path = tmp_file.name

        # Transcribe the audio file
        batch_size = 4
        audio = whisperx.load_audio(tmp_file_path)
        result = transcription_model.transcribe(audio, batch_size=batch_size)
        result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        formatted_transcript = format_transcript(result["segments"])

        torch.cuda.empty_cache()
        print("**** transcription:")
        print(formatted_transcript)
        print("**** transcribe_file -> end ****")
        return formatted_transcript
    # Transcript processing is complete



def concatenate_audio_segments(audio_segments):
    """Concatenate the audio segments into a single bytes-like object.

    Args:
        audio_segments: A list of bytes-like audio segments.

    Returns:
        A bytes-like object representing the concatenated audio.
    """
    combined_audio = pydub.AudioSegment.empty()
    for segment in audio_segments:
        audio_segment = pydub.AudioSegment.from_file(io.BytesIO(segment), format="webm")
        combined_audio += audio_segment

    # Export the concatenated audio to a bytes-like object
    with io.BytesIO() as buffer:
        combined_audio.export(buffer, format="webm")
        return buffer.getvalue()
