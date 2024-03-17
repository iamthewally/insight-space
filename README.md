# Insight Space: A Real-Time Audio Transcription and Summarization Tool 🎙️

Insight Space is a web application that provides real-time audio transcription and summarization capabilities. It allows users to upload audio files or record audio directly from their microphone, and receive both a detailed transcript and a concise summary of the content. This tool is particularly useful for capturing and analyzing conversations, meetings, lectures, and other audio-based information.

## Features 🚀

- **Real-time transcription**: Transcribe audio in real-time, allowing you to follow along with the conversation or presentation as it happens.
- **Speaker diarization**: Identify and label different speakers in the audio, making it easier to track who said what.
- **Concise summarization**: Generate a brief summary of the transcribed text, highlighting the key points and takeaways.
- **File upload and microphone recording**: Choose between uploading existing audio files or recording directly from your microphone.
- **Customizable chunk interval**: Adjust the interval at which audio chunks are sent for transcription, allowing you to balance latency and accuracy.
- **Dark mode**: Switch to dark mode for a more comfortable viewing experience in low-light environments. 🌙

## Technologies Used 🛠️

Insight Space is built using a combination of technologies, including:
- **Frontend**: React, Bootstrap, React Grid Layout
- **Backend**: Flask, Flask-SocketIO, WhisperX, Ollama

## Installation 💻

1. Clone the repository:
   '''
   git clone https://github.com/iamthewally/insight-space.git
   cd insight-space
   '''

3. Generate a local key/cert to connect over SSL (Chrome requires a secured connection to enable the microphone):
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt

4. Set up the Node.js frontend:
   npm install

5. Install the backend requirements:
   pip install -r requirements.txt

## Usage 🖥️

1. Run the backend server:
   cd insight-space && python app.py

2. In a separate terminal, run the frontend server:
   cd insight-space && npm start

3. Access the application in your browser at https://localhost:2600.

## License 📄

This project is currently not licensed. Please contact the author for more information regarding licensing and usage rights.
