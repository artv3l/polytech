`openssl genrsa -out root_ca.key 2048`
- root_ca.key - Приватный ключ CA. Хранится в секрете от всех

`openssl req -x509 -new -key root_ca.key -days 365 -out root_ca.crt`
- root_ca.crt - Сертификат, подписанный ключом CA. На 365 дней. Копируем его на все компьютеры, между которыми нужно организовать TLS соединение
- CN=MyCN
- `openssl x509 -text -in root_ca.crt` - Просмотр информации о сертификате

---

`openssl genrsa -out server.key 2048`
- server.key - Приватный ключ HTTPS сервера. Хранится только на компе, где запущен сервер

`openssl req -new -key server.key -out server.csr`
- server.csr - Запрос от сервера на сертификат CSR
- CN=127.0.0.1
- `openssl req -text -in server.csr`

`openssl x509 -req -in server.csr -CA root_ca.crt -CAkey root_ca.key -CAcreateserial -out server.crt -days 365`
- server.crt - Сертификат сервера, подписанный ключом CA. На 365 дней.

---

`openssl genrsa -out client.key 2048`
- client.key - Приватный ключ клиента

`openssl req -new -key client.key -out client.csr`
- CN=127.0.0.1

`openssl x509 -req -in client.csr -CA root_ca.crt -CAkey root_ca.key -CAcreateserial -out client.crt -days 365`

`openssl pkcs12 -inkey client.key -in client.crt -export -out client.p12`

---

`curl --cert client.crt --key client.key --cacert root_ca.crt https://127.0.0.1:8085`
