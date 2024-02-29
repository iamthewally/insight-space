# file: test_transcription.py

import unittest
import os
from transcription import concatenate_audio_files, transcribe_audio_files, format_transcript
import whisperx

class TestTranscription(unittest.TestCase):
    def setUp(self):
        # Set up the necessary models and data for the tests
        self.device = "cuda"
        self.compute_type = "float16"
        self.model_dir = "./models/"
        self.transcription_model = whisperx.load_model("base", self.device, compute_type=self.compute_type, download_root=self.model_dir, language='en')
        self.align_model, self.align_metadata = whisperx.load_align_model(language_code='en', device=self.device)
        self.diarize_model = whisperx.DiarizationPipeline(use_auth_token="your_hugging_face_token", device=self.device)

        # Sample audio files for testing
        self.audio_file_1 = "testaudio_01.webm"
        self.audio_file_2 = "testaudio_02.webm"
        self.audio_file_3 = "testaudio_03.webm"

    def test_concatenate_audio_files(self):
        # Test the concatenation of audio files
        concatenated_file = concatenate_audio_files([self.audio_file_1, self.audio_file_2, self.audio_file_3])
        self.assertTrue(os.path.exists(concatenated_file))
        os.remove(concatenated_file)  # Clean up the temporary file

    def test_transcribe_audio_files(self):
        # Test the transcription of individual audio files
        transcript_1 = transcribe_audio_files(self.audio_file_1, self.transcription_model, self.align_model, self.align_metadata, self.diarize_model, self.device)
        self.assertIn("terminal", transcript_1.lower())

        transcript_2 = transcribe_audio_files(self.audio_file_2, self.transcription_model, self.align_model, self.align_metadata, self.diarize_model, self.device)
        self.assertIn("start", transcript_2.lower())

        # Test the transcription of concatenated audio files
        concatenated_file = concatenate_audio_files([self.audio_file_1, self.audio_file_2, self.audio_file_3])
        concatenated_transcript = transcribe_audio_files(concatenated_file, self.transcription_model, self.align_model, self.align_metadata, self.diarize_model, self.device)
        self.assertIn("terminal", concatenated_transcript.lower())
        self.assertIn("start", concatenated_transcript.lower())
        os.remove(concatenated_file)  # Clean up the temporary file

if __name__ == '__main__':
    unittest.main()
