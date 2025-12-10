import threading
import datetime
import time
import io

from flask import Flask, request, jsonify, Response
from pymongo import MongoClient
import gridfs
import librosa
from bson import ObjectId
from prometheus_client import make_wsgi_app, Histogram, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import numpy as np

import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt

import params
import common

request_latency = Histogram('flask_request_latency_seconds', 'Request latency', ['endpoint'])
analyzes_count = Gauge('analyzes_count', 'Number of started analyzes')
analyzer_status = Gauge('analyzer_status', 'Status of analyzer (0 - running, other - time)')

audio_analysis_duration = Histogram(
    "audio_analysis_duration_seconds",
    "Time spent analyzing audio file",
)

app = Flask(__name__)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

mongo_client = MongoClient("mongodb://root:root@mongo:27017/")
file_db = gridfs.GridFS(mongo_client["cw"])
coll_analyzes = mongo_client["cw"][params.names.coll_analyzes]
coll_results = mongo_client["cw"][params.names.coll_results]

@app.route('/upload', methods=['POST'])
@request_latency.labels(endpoint='/upload').time()
def upload():
    c_file_key = "file"
    c_filename_field_name = "filename"

    if c_file_key not in request.files:
        return jsonify({"message": "No file"}), 400
    
    file = request.files[c_file_key]
    file_id = file_db.put(file.stream, **{c_filename_field_name: file.filename})

    result = coll_analyzes.insert_one({
        "file_id": file_id,
        "title": file.filename,
        "status": "waiting",
        "created_at": datetime.datetime.now(),
        "result_id": None,
    })

    return jsonify({
        "message": f"File \"{file.filename}\" uploaded. Analyze is started.",
        "file_id": str(file_id),
        "analyze_id": str(result.inserted_id),
    })

@app.route('/analyzes', methods=['GET'])
@request_latency.labels(endpoint='/analyzes').time()
def get_analyzes():
    found = coll_analyzes.find(sort=[("created_at", -1)])
    return jsonify([common.Analyze(**doc).model_dump() for doc in found])

@app.route('/result/<id>', methods=['GET'])
@request_latency.labels(endpoint='/result').time()
def get_result(id: str):
    res = coll_results.find_one({"_id": ObjectId(id)})
    return common.Result(**res).model_dump()

@app.route('/file/<id>', methods=['GET'])
@request_latency.labels(endpoint='/file').time()
def get_file(id: str):
    file = file_db.get(ObjectId(id))
    return Response(file.read(), mimetype="image/png")

def analyze(task):
    start_time = time.time()
    with file_db.get(ObjectId(task["file_id"])) as f:
        y, sample_rate = librosa.load(f, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sample_rate)
    
    n_fft = 1024  # Window size: 2048 samples (adjust based on frequency resolution)  
    stft_result = librosa.stft(y, n_fft=n_fft, hop_length=512)
    magnitude_spectrogram = np.abs(stft_result) # Compute magnitude spectrogram (absolute value of STFT result)
    db_spectrogram = librosa.amplitude_to_db(magnitude_spectrogram, ref=np.max) # Convert to dB scale (logarithmic)

    fig, ax = plt.subplots(figsize=(4, 4), dpi=72)
    img = librosa.display.specshow(
        db_spectrogram,
        ax=ax,
        sr=sample_rate,
        x_axis="time",  # Label x-axis as time  
        y_axis="hz",    # Label y-axis as frequency (Hz)  
        cmap="viridis"  # Colormap (try "magma" or "plasma" for different looks)
    )
    fig.colorbar(img, ax=ax, format="%+2.0f dB") # Show amplitude in dB
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Spectrogram (dB Scale)")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    audio_analysis_duration.observe(time.time() - start_time)

    spectrogram_id = file_db.put(buf)
    result = coll_results.insert_one({
        "bpm": tempo[0],
        "sample_rate": sample_rate,
        "duration": librosa.get_duration(y=y, sr=sample_rate),
        "spectrogram_id": spectrogram_id
    })
    coll_analyzes.update_one(
        {"_id": task["_id"]},
        {"$set": {"status": "ready", "result_id": str(result.inserted_id)}}
    )

def analyzer():
    while True:
        try:
            task = coll_analyzes.find_one_and_update(
                {"status": "waiting"},
                {"$set": {"status": "running"}},
                sort=[("created_at", 1)]
            )
        except BaseException:
            pass
        else:
            if task:
                analyzer_status.set(0)
                analyzes_count.inc()
                analyze(task)
        
        time.sleep(1)
        analyzer_status.set(int(time.time()))

if __name__ == "__main__":
    threading.Thread(target=analyzer, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
