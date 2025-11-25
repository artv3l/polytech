FROM python:3.13-slim

WORKDIR /app

COPY frontend.py .
COPY common.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "frontend.py", "--server.port=8501"]
