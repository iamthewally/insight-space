import whisperx
import gc 
import torch

device = "cuda" 
audio_file = "Recording.webm"
batch_size = 12 # reduce if low on GPU mem
compute_type = "float16" # change to "int8" if low on GPU mem (may reduce accuracy)

print("garbage collection...")
gc.collect()

print("empty torch cache...")
torch.cuda.empty_cache()
# save model to local path (optional)
model_dir = "./models/"
model = whisperx.load_model("large-v3", device, compute_type=compute_type, download_root=model_dir, language='en')
audio = whisperx.load_audio(audio_file)
result = model.transcribe(audio, batch_size=batch_size)
print(result["segments"]) # before alignment

# delete model if low on GPU resources
# import gc; gc.collect(); torch.cuda.empty_cache(); del model

# 2. Align whisper output
model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

print(result["segments"]) # after alignment

# delete model if low on GPU resources, for now we should probably leave it in so we cna call it repeatedly
# import gc; gc.collect(); torch.cuda.empty_cache(); del model_a

# 3. Assign speaker labels
diarize_model = whisperx.DiarizationPipeline(use_auth_token="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", device=device)

# add min/max number of speakers if known
diarize_segments = diarize_model(audio)
# diarize_model(audio, min_speakers=min_speakers, max_speakers=max_speakers)

result = whisperx.assign_word_speakers(diarize_segments, result)
print(diarize_segments)
print(result["segments"]) # segments are now assigned speaker IDs


def format_transcript(diarized_segments, word_segments):
    """
    Formats the diarized segments into a transcript.

    Args:
        diarized_segments (list): List of diarized segments with speaker IDs.
        word_segments (list): List of word segments with corresponding text.

    Returns:
        str: Formatted transcript with speaker labels.
    """
    transcript = ""
    current_speaker = None
    for word_segment in word_segments:
        speaker_id = word_segment.get("speaker")
        if speaker_id != current_speaker:
            current_speaker = speaker_id
            transcript += f"\nSpeaker {speaker_id}: "
        transcript += word_segment.get("text") + " "

    return transcript.strip()

def format_transcript(segments):
    transcript = ""
    current_speaker = None
    for segment in segments:
        if segment["speaker"] != current_speaker:
            if current_speaker is not None:
                transcript += "\n"
            current_speaker = segment["speaker"]
            transcript += f"Speaker {current_speaker}: "
        transcript += segment["text"] + " "
    return transcript

# Usage
formatted_transcript = format_transcript(result["segments"])
print(formatted_transcript)
