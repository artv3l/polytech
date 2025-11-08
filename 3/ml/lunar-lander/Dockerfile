FROM python:3.14-slim

WORKDIR /app

COPY ppo_2.zip .
COPY common.py .
COPY service.py .

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch
RUN pip install --no-cache-dir flask stable_baselines3

EXPOSE 8080

CMD ["python", "service.py"]
