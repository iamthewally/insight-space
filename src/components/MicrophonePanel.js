// MicrophonePanel.js
import React, { useState, useEffect } from 'react';

const MicrophonePanel = ({ socket, emitTranscribeStream, chunkInterval }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [stopRecordingFunction, setStopRecordingFunction] = useState(null);
  const [time, setTime] = useState(0);

  useEffect(() => {
    let timer;
    if (isRecording) {
      timer = setInterval(() => {
        setTime((prevTime) => prevTime + 1);
      }, 1000);
    }
    return () => {
      clearInterval(timer);
    };
  }, [isRecording]);

  const startRecording = () => {
    if (isRecording) {
      console.log('Recording is already in progress.');
      return;
    }

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        setIsRecording(true);
        let recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        const stopRecordingSession = () => {
          if (recorder && recorder.state !== 'inactive') {
            recorder.stop();
          }
          stream.getTracks().forEach((track) => track.stop());
          setIsRecording(false);
        };

        setStopRecordingFunction(() => stopRecordingSession);

        recorder.start();

        const interval = chunkInterval * 1000;
        setInterval(() => {
          if (recorder.state !== 'inactive') {
            recorder.stop();
          }
        }, interval);

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            emitTranscribeStream(event.data);
          }
        };

        recorder.onstop = () => {
          console.log('Chunk recording stopped, ready to reinitialize');
          recorder.start();
        };
      })
      .catch((error) => {
        console.error('Error accessing audio stream:', error);
      });
  };

  return (
    <div className="microphone-panel">
      <h3>Audio Transcription (Mic Recording)</h3>
      <div onMouseDown={(e) => e.stopPropagation()}>
        <button
          onClick={startRecording}
          className="btn btn-primary mt-2"
          disabled={isRecording}
          onMouseDown={(e) => e.stopPropagation()}
        >
          {isRecording ? 'Recording...' : 'Start Recording'}
        </button>
        <button
          onClick={() => stopRecordingFunction && stopRecordingFunction()}
          className="btn btn-danger mt-2"
          disabled={!isRecording}
          onMouseDown={(e) => e.stopPropagation()}
        >
          Stop Recording
        </button>
        {isRecording && <div className="recording-animation"></div>}
        <div className="timer">{time} seconds</div>
      </div>
    </div>
  );
};

export default MicrophonePanel;