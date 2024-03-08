// TranscriptDisplay.js
import React from 'react';

const TranscriptDisplay = ({ transcript }) => {
  return (
    <div className="transcript-display">
      {transcript && (
        <div>
          <h2>Transcript:</h2>
          <div className="border rounded p-3" style={{ whiteSpace: 'pre-wrap' }}>
            {transcript}
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptDisplay;