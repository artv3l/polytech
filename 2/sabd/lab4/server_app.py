from flask import Flask, request

app = Flask(__name__)

@app.route('/data')
def data():
    print(request.headers)
    return 'Server: /data'

if __name__ == '__main__':
    app.run(host='localhost', port=5001)
