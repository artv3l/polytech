from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def ui_page():
    return render_template_string("""
    <html>
        <head>
            <title>UI Page</title>
        </head>
        <body>
            <h1>Welcome to UI</h1>
            <p><a href="/api/data" id="getDataLink">Get Data From Server</a></p>
        </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(host='localhost', port=5002)
