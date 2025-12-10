FROM python:3.13-slim

WORKDIR /app

COPY backend.py .
COPY common.py .
COPY params.py .
COPY requirements_backend.txt .

RUN pip install --no-cache-dir -r requirements_backend.txt

CMD ["python", "backend.py"]
