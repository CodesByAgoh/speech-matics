from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import speechmatics
from httpx import HTTPStatusError
from flask_socketio import SocketIO
import os

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])

API_KEY = os.environ.get('API_KEY')
PATH_TO_FILE = "temp.wav"
LANGUAGE = "en"
CONNECTION_URL = f"wss://eu2.rt.speechmatics.com/v2"

@app.route('/audio', methods=['POST'])
def audio():
    transcription = []
    audio_file = request.files.get('audio_data')

    if audio_file:
        audio_file.save(PATH_TO_FILE)
    else:
        return jsonify({ "message": "No audio received" })

    # Create a transcription client
    ws = speechmatics.client.WebsocketClient(
        speechmatics.models.ConnectionSettings(
            url=CONNECTION_URL,
            auth_token=API_KEY,
        )
    )

    # Define an event handler to print the partial transcript
    def print_partial_transcript(msg):
        print(f"[partial] {msg['metadata']['transcript']}")

    # Define an event handler to print the full transcript
    def print_transcript(msg):
        transcription.append(msg['metadata']['transcript'])
        print(f"[   FULL] {msg['metadata']['transcript']}")

    # Register the event handler for partial transcript
    ws.add_event_handler(
        event_name=speechmatics.models.ServerMessageType.AddPartialTranscript,
        event_handler=print_partial_transcript,
    )

    # Register the event handler for full transcript
    ws.add_event_handler(
        event_name=speechmatics.models.ServerMessageType.AddTranscript,
        event_handler=print_transcript,
    )

    settings = speechmatics.models.AudioSettings()

    # Define transcription parameters
    # Full list of parameters described here: https://speechmatics.github.io/speechmatics-python/models
    conf = speechmatics.models.TranscriptionConfig(
        language=LANGUAGE,
        enable_partials=True,
        max_delay=5,
    )

    print("Starting transcription (type Ctrl-C to stop):")
    with open(PATH_TO_FILE, 'rb') as fd:
        try:
            ws.run_synchronously(fd, conf, settings)
        except KeyboardInterrupt:
            print("\nTranscription stopped.")
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                print('Invalid API key - Check your API_KEY at the top of the code!')
            else:
                raise e
        
    return { 'response': transcription }

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.secret_key = 'secretkeyforspeechmaticsapiapi'
    app.run()