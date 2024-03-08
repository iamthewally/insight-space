// App.js
import React, { useState, useEffect } from 'react';
import FileUploadForm from './components/FileUploadForm';
import MicrophonePanel from './components/MicrophonePanel';
import TranscriptDisplay from './components/TranscriptDisplay';
import SummaryDisplay from './components/SummaryDisplay';
import SettingsPanel from './components/SettingsPanel';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import './App.css'
import 'bootstrap/dist/css/bootstrap.min.css';
import { socket, setupSocketListeners, emitTranscribeStream } from './services/socket';

function App() {
  const [transcript, setTranscript] = useState('');
  const [summary, setSummary] = useState('');
  const [chunkInterval, setChunkInterval] = useState(5);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);

  useEffect(() => {
    setupSocketListeners(
      (transcriptData) => {
        setTranscript((prevTranscript) => prevTranscript + (prevTranscript ? '\n' : '') + transcriptData);
      },
      (summaryText) => {
        setSummary(summaryText + '\n----------------------------------\n');
      }
    );

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
      document.head.removeChild(stylesheet); // Remove the stylesheet when the component is unmounted
    };
  }, [darkModeEnabled]);

  const handleChunkIntervalChange = (newInterval) => {
    setChunkInterval(newInterval);
  };

  const handleDarkModeToggle = (newDarkModeEnabled) => {
    setDarkModeEnabled(newDarkModeEnabled);
  };

  return (
    <div>
      <GridLayout className="layout" cols={12} rowHeight={30} width={1200}>
        <div key="fileUploadForm" data-grid={{ x: 0, y: 0, w: 6, h: 4 }} className="grid-item">
          <FileUploadForm socket={socket} emitTranscribeStream={emitTranscribeStream} />
        </div>
        <div key="microphonePanel" data-grid={{ x: 6, y: 0, w: 6, h: 4 }} className="grid-item">
          <MicrophonePanel socket={socket} emitTranscribeStream={emitTranscribeStream} chunkInterval={chunkInterval} />
        </div>
        <div key="transcriptDisplay" data-grid={{ x: 0, y: 4, w: 6, h: 10 }} className="grid-item">
          <TranscriptDisplay transcript={transcript} />
        </div>
        <div key="summaryDisplay" data-grid={{ x: 6, y: 4, w: 6, h: 6 }} className="grid-item">
          <SummaryDisplay summary={summary} />
        </div>
        <div key="settingsPanel" data-grid={{ x: 9, y: 0, w: 3, h: 5 }} className="grid-item">
          <SettingsPanel
            onChunkIntervalChange={handleChunkIntervalChange}
            onDarkModeToggle={handleDarkModeToggle}
          />
        </div>
      </GridLayout>
    </div>
  );
}

export default App;