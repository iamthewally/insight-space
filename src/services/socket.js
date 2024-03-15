// socket.js
import io from 'socket.io-client';

const socket = io('https://2601.sysak.dev', {
  transports: ['polling'],
  upgrade: false,
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  randomizationFactor: 0.5,
  autoConnect: true,
  forceNew: true,
  timeout: 20000
});

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