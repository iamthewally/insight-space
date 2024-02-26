from fastapi import FastAPI, WebSocket
from diart.inference import StreamingInference
from diart import SpeakerDiarization
from diart.sources import WebSocketAudioSource
from diart.sinks import RTTMWriter

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Create a WebSocket audio source, this will need to match the client's sample rate and frame settings
    ws_source = WebSocketAudioSource(rate=16000, uri="ws://localhost:2600/ws")

    # Initialize the Diart pipeline with the default configuration
    pipeline = SpeakerDiarization()

    # Attach the RTTM writer to save the diarization output
    rttm_writer = RTTMWriter(f"/output/file.rttm")

    # Create the StreamingInference object and attach observers
    inference = StreamingInference(pipeline, ws_source, do_plot=True)
    inference.attach_observers(rttm_writer)

    # Here you would include the logic to handle the WebSocket communication
    # For example, you might read audio frames from the WebSocket and write them to the WebSocketAudioSource
    while True:
        # Receive audio frames from the client
        audio_frame = await websocket.receive_bytes()
        
        # Write audio frames to the WebSocket audio source
        ws_source.write(audio_frame)

        # Process the audio frame with the Diart pipeline
        diarization_result = inference()

        # Send diarization results back to the client
        await websocket.send_text(str(diarization_result))

    # Don't forget to close the WebSocket connection when done
    await websocket.close()
