import threading
import datetime
import time

from flask import Flask, request, jsonify
from pymongo import MongoClient
import gridfs
import librosa
from bson import ObjectId
from prometheus_client import make_wsgi_app, Histogram, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware

import params
import common

request_latency = Histogram('flask_request_latency_seconds', 'Request latency', ['endpoint'])

audio_analysis_duration = Gauge(
    "audio_analysis_duration_seconds",
    "Time spent analyzing audio file",
    ["file_id", "filename"],
)

app = Flask(__name__)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

mongo_client = MongoClient("mongodb://root:root@localhost:27017/")
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
    print(id)
    res = coll_results.find_one({"_id": ObjectId(id)})
    return common.Result(**res).model_dump()

def analyze(task):
    file = file_db.get(ObjectId(task["file_id"]))

    start_time = time.time()
    y, sample_rate = librosa.load(file, sr=None)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sample_rate)
    
    audio_analysis_duration.labels(file_id=task["file_id"], filename=file.filename).set(time.time() - start_time)

    result = coll_results.insert_one({
        "bpm": tempo[0],
        "sample_rate": sample_rate,
        "duration": librosa.get_duration(y=y, sr=sample_rate),
    })
    coll_analyzes.update_one(
        {"_id": task["_id"]},
        {"$set": {"status": "ready", "result_id": str(result.inserted_id)}}
    )

def analyzer():
    while True:
        task = coll_analyzes.find_one_and_update(
            {"status": "waiting"},
            {"$set": {"status": "running"}},
            sort=[("created_at", 1)]
        )
        if task:
            analyze(task)
        else:
            time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=analyzer, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
