import requests

url = 'https://127.0.0.1:8085'
client_cert = ('client.crt', 'client.key')  # Клиентский сертификат и ключ
ca_cert = 'root_ca.crt'  # Корневой сертификат CA

response = requests.get(url, cert=client_cert, verify=ca_cert)

print(response.text)
