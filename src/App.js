import './App.css';
import DevConsole from './DevConsole';
import 'bootstrap/dist/css/bootstrap.min.css';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css'; // Import the CSS for React-Grid-Layout
import io from 'socket.io-client';
import React, { useState, useEffect } from 'react';

const socket = io('https://192.168.1.25:2601');

function App() {
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [summary, setSummary] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [stopRecordingFunction, setStopRecordingFunction] = useState(null);
  const [recordingEnabled, setRecordingEnabled] = useState(false);
  const [chunkInterval, setChunkInterval] = useState(5); // Default chunk interval in seconds
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);
  const [time, setTime] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(prevTime => prevTime + 1);
    }, 1000);

    return () => {
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    socket.on('transcription', (data) => {
      setTranscript(prevTranscript => prevTranscript + "\n" + data.transcript);
    });

    socket.on('summary', (data) => {
      setSummary(data.summary_text);
    });

    // Set up the stylesheet for dark mode
    const stylesheet = document.createElement('style');
    stylesheet.innerHTML = `
      :root {
        --background-color: ${darkModeEnabled ? '#212529' : '#ffffff'};
        --text-color: ${darkModeEnabled ? '#ffffff' : '#000000'};
      }
    `;
    document.head.appendChild(stylesheet);

    return () => {
      socket.off('transcription');
      socket.off('summary');
      document.head.removeChild(stylesheet); // Remove the stylesheet when the component is unmounted
    };
  }, [darkModeEnabled]);
  const handleChunkIntervalChange = (event) => {
    const value = parseInt(event.target.value);
    if (value > 0) {
      setChunkInterval(value);
    }
  };

  const handleDarkModeToggle = () => {
    setDarkModeEnabled(!darkModeEnabled);
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    console.log('File upload button clicked');
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        const audioData = new Uint8Array(e.target.result);
        socket.emit('transcribe', { audio: audioData.buffer });
      };
      reader.readAsArrayBuffer(file);
    }
  };

  const startRecording = () => {
    console.log("startRecording() -> Start");
    setRecordingEnabled(true); // Enable recording when the start button is clicked

    let stream;
    let recorder;

    const stopRecordingSession = () => {
      if (recorder && recorder.state !== "inactive") {
        recorder.stop(); // Stop the current recording session
      }
      if (stream) {
        // Stop each track on the stream to ensure it's fully stopped
        stream.getTracks().forEach(track => track.stop());
      }
    };

    const initializeRecording = () => {
      if (!recordingEnabled) {
        return; // Exit if recording is not enabled
      }
      stopRecordingSession(); // Stop any previous recording session

      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(newStream => {
          stream = newStream;
          recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
          recorder.start(); // Start recording without slicing

          // Start slicing the recording into chunks
          const interval = chunkInterval * 1000; // Convert to milliseconds
          setInterval(() => {
            if (recorder.state !== "inactive") {
              recorder.stop(); // Stop the current chunk
            }
          }, interval);

          setIsRecording(true);

          recorder.ondataavailable = event => {
            if (event.data.size > 0) {
              const reader = new FileReader();
              reader.onload = function (e) {
                const audioData = new Uint8Array(e.target.result);
                socket.emit('transcribe', { audio: audioData.buffer });
              };
              reader.readAsArrayBuffer(event.data);
            }
          };

          recorder.onstop = () => {
            console.log("Chunk recording stopped, ready to reinitialize");
            initializeRecording(); // Restart the recording process for the next segment
          };
        })
        .catch(error => {
          console.error('Error accessing audio stream:', error);
        });
    };

    const stopRecording = () => {
      setRecordingEnabled(false); // Disable recording when the stop button is clicked
      stopRecordingSession();
      console.log("startRecording() -> Stop");
      setIsRecording(false);
    };

    setStopRecordingFunction(() => stopRecording);
    initializeRecording(); // Start the initial recording process
  };





  // TODO: give the grid boxes a windows style bar?
  return (
    <div>
      <GridLayout className="layout" cols={12} rowHeight={30} width={1200}>
        <div key="fileUploadForm" data-grid={{ x: 0, y: 0, w: 6, h: 4 }} className="grid-item">
          <h3>Audio Transcription (File Upload)</h3>
          <form onSubmit={handleSubmit}>
            <input type="file" onChange={handleFileChange} accept="audio/*" className="form-control" />
            <button type="submit" className="btn btn-primary mt-2">Transcribe</button>
          </form>
        </div>
        <div key="microphone-panel" data-grid={{ x: 6, y: 0, w: 6, h: 3 }} className="grid-item">
          <h3>Audio Transcription (Mic Recording)</h3>
          <div onMouseDown={e => e.stopPropagation()}>
            <button onClick={startRecording} className="btn btn-primary mt-2" disabled={isRecording}>
              {isRecording ? 'Recording...' : 'Start Recording'}
            </button>
            <button onClick={() => stopRecordingFunction && stopRecordingFunction()} className="btn btn-danger mt-2" disabled={!isRecording}>
              Stop Recording
            </button>          

          {isRecording && (
            <div className="recording-animation"></div>
          )}

            <div className="timer">
            {time} seconds
          </div>
          </div>
        </div>


        <div key="transcriptDisplay" data-grid={{ x: 0, y: 4, w: 6, h: 10 }} className="grid-item">
          {transcript && (
            <div>
              <h2>Transcript:</h2>
              <div className="border rounded p-3" style={{ whiteSpace: 'pre-wrap' }}>
                {transcript}
              </div>
            </div>
          )}
        </div>
        <div key="summaryDisplay" data-grid={{ x: 6, y: 4, w: 6, h: 8 }} className="grid-item">
          {summary && (
            <div>
              <h2>Refined Transcript:</h2>
              <div className="border rounded p-3" style={{ whiteSpace: 'pre-wrap' }}>
                {summary}
              </div>
            </div>
          )}
        </div>
        <div key="settingsPanel" data-grid={{ x: 9, y: 0, w: 3, h: 5 }} className="grid-item settings-panel">
          <h3>Settings</h3>
          <div className="chunk-interval-field">
            <label htmlFor="chunkInterval">Chunk Interval (seconds):</label>
            <input type="number" id="chunkInterval" value={chunkInterval} onChange={handleChunkIntervalChange} />
          </div>
          <div className="dark-mode-toggle">
            <label htmlFor="darkModeToggle">Dark Mode:</label>
            <input type="checkbox" id="darkModeToggle" checked={darkModeEnabled} onChange={handleDarkModeToggle} />
          </div>
        </div>
        <div key="devConsole" data-grid={{ x: 0, y: 14, w: 6, h: 4 }} className="grid-item">
          <DevConsole />
        </div>
      </GridLayout>
    </div>
  );
}

export default App;
