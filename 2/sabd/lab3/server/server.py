from flask import Flask, request
import ssl

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Mutual TLS Client!'

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile='server.crt', keyfile='server.key')  # Сертификат сервера
    context.load_verify_locations('root_ca.crt')  # Корневой сертификат
    context.verify_mode = ssl.CERT_REQUIRED  # Требуем сертификат от клиента

    app.run(host='127.0.0.1', port=8085, ssl_context=context)
