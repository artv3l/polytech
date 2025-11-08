from flask import Flask, request, jsonify
import common

c_algorithm = "PPO"
c_modelPath = "ppo_2.zip"

app = Flask(__name__)
model = common.load_model(c_modelPath, c_algorithm)

@app.route("/test", methods=["GET"])
def test():
    return "test"

@app.route("/predict", methods=["POST"])
def predict():
    obs = request.json["obs"]
    action, _ = model.predict(obs, deterministic=True)
    return jsonify({"action": int(action)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
