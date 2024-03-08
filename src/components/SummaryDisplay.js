// SummaryDisplay.js
import React from 'react';

const SummaryDisplay = ({ summary }) => {
  return (
    <div className="summary-display">
      {summary && (
        <div>
          <h2>Refined Transcript:</h2>
          <div className="border rounded p-3" style={{ whiteSpace: 'pre-wrap' }}>
            {summary}
          </div>
        </div>
      )}
    </div>
  );
};

export default SummaryDisplay;