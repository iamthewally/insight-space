// socket.js
import io from 'socket.io-client';

const socket = io('https://2601.sysak.dev');

const setupSocketListeners = (onTranscription, onSummary) => {
  socket.on('transcription', (data) => {
    onTranscription(data.transcript);
  });

  socket.on('summary', (data) => {
    onSummary(data.summary_text);
  });
};

const emitTranscribeStream = (audioData) => {
  socket.emit('transcribe_stream', { audio: audioData });
};

export { socket, setupSocketListeners, emitTranscribeStream };