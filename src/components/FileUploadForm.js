// FileUploadForm.js
import React, { useState } from 'react';

const FileUploadForm = ({ socket }) => {
  const [file, setFile] = useState(null);

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
        console.log('Buffer to send:', audioData.buffer);
        //emitTranscription(audioData.buffer); // Emit the audio data to the server
      };
      reader.readAsArrayBuffer(file);
    }
  };

  const handleMouseDown = (event) => {
    event.stopPropagation();
  };

  return (
    <div className="file-upload-form">
      <h3>Audio Transcription (File Upload)</h3>
      <form onSubmit={handleSubmit} onMouseDown={handleMouseDown}>
        <input
          type="file"
          onChange={handleFileChange}
          accept="audio/*"
          className="form-control"
        />
        <button
          type="submit"
          className="btn btn-primary mt-2"
          onMouseDown={handleMouseDown}
        >
          Transcribe
        </button>
      </form>
    </div>
  );
};

export default FileUploadForm;