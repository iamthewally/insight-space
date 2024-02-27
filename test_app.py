# test_app.py

import unittest
import os
from app import app, socketio
from transcription import concatenate_audio_files, format_transcript

class TestApp(unittest.TestCase):

    def setUp(self):
        # Set up the Flask test client and initialize the SocketIO test client
        self.flask_test_client = app.test_client()
        self.socketio_test_client = socketio.test_client(app, flask_test_client=self.flask_test_client)

    def test_index_route(self):
        response = self.flask_test_client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)

    def test_concatenate_audio_files(self):
        # Test the concatenate_audio_files function with a list of audio file paths
        # The 2 files below are in the root project folder
        # Between the two chunks the speaker says the numbers 1 through 10
        audio_files = ['testaudio_01.webm', 'testaudio_02.webm']
        concatenated_file_path = concatenate_audio_files(audio_files)
        self.assertTrue(os.path.exists(concatenated_file_path))
        os.remove(concatenated_file_path)  # Clean up the temporary file

    def test_format_transcript(self):
        # Test the format_transcript function with sample segment data
        segments = [
            {'speaker': 'Speaker 1', 'text': 'Hello'},
            {'speaker': 'Speaker 2', 'text': 'World'},
            {'speaker': 'Speaker 1', 'text': 'Goodbye'}
        ]
        formatted_transcript = format_transcript(segments)
        expected_transcript = "Speaker 1: Hello Speaker 2: World Speaker 1: Goodbye "
        self.assertEqual(formatted_transcript, expected_transcript)

    # Add more tests for other functions and components of your app

if __name__ == '__main__':
    unittest.main()
