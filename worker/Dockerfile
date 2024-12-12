FROM python:3.11-slim
WORKDIR /app
RUN pip install pika
RUN pip install torch
RUN pip install numpy
RUN pip install minio
ENV MINIO_HOST="minio"
COPY worker.py /app/worker.py
COPY utils.py /app/utils.py
CMD ["python", "worker.py"]