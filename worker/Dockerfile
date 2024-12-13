FROM python:3.11-slim
WORKDIR /app
RUN pip install pika torch numpy minio redis
ENV MINIO_HOST="minio"
ENV REDIS_HOST="redis"
COPY worker.py /app/worker.py
COPY utils.py /app/utils.py
CMD ["python", "worker.py"]