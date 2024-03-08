// SettingsPanel.js
import React, { useState } from 'react';

const SettingsPanel = ({ onChunkIntervalChange, onDarkModeToggle }) => {
  const [chunkInterval, setChunkInterval] = useState(5);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);

  const handleChunkIntervalChange = (event) => {
    const value = parseInt(event.target.value);
    if (value > 0) {
      setChunkInterval(value);
      onChunkIntervalChange(value);
    }
  };

  const handleDarkModeToggle = () => {
    const newDarkModeEnabled = !darkModeEnabled;
    setDarkModeEnabled(newDarkModeEnabled);
    onDarkModeToggle(newDarkModeEnabled);
  };

  return (
    <div className="settings-panel">
      <h3>Settings</h3>
      <div className="chunk-interval-field">
        <label htmlFor="chunkInterval">Chunk Interval (seconds):</label>
        <input
          type="number"
          id="chunkInterval"
          value={chunkInterval}
          onChange={handleChunkIntervalChange}
        />
      </div>
      <div className="dark-mode-toggle">
        <label htmlFor="darkModeToggle">Dark Mode:</label>
        <input
          type="checkbox"
          id="darkModeToggle"
          checked={darkModeEnabled}
          onChange={handleDarkModeToggle}
        />
      </div>
    </div>
  );
};

export default SettingsPanel;