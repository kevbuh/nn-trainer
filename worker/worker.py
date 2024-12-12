import os
import io
import json
import pika
import torch
import logging
import tempfile
import numpy as np
import torch.nn as nn
from minio import Minio
import torch.optim as optim

# LOGGER
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MINIO
minioHost = os.getenv("MINIO_HOST") or "localhost"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"
logger.info(f"connecting to minio...MINIO_HOST:{minioHost}")
client = Minio(minioHost+":9000", secure=False, access_key=minioUser, secret_key=minioPasswd)
bucketname='runs'

logger.info("creating bucket...")
if not client.bucket_exists(bucketname):
    client.make_bucket(bucketname)
    logger.info(f"Bucket '{bucketname}' created successfully!")
else:
    logger.info(f"Bucket '{bucketname}' already exists.")

# RABBITMQ
cluster_name = os.getenv("RABBITMQ_HOST") or "localhost"
queue_name = os.getenv("RABBITMQ_QUEUE") or "bob"
logger.info("")
logger.info(f"connecting to rabbitmq...RABBITMQ_HOST:{cluster_name} and RABBITMQ_QUEUE:{queue_name}")
logger.info("")

# PROCESS FROM QUEUE
def process_training_task(ch, method, properties, body):
    task = json.loads(body)

    hash_id = task["hash_id"]
    if task["steps"] > task["max_steps"]:
        logging.info(f"model uploaded to minio: ./'{hash_id}'")
        logging.info(f"Max steps for task {task['hash_id']} reached, removing from queue")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    batch_data = np.array(task["data"])
    batch_labels = np.array(task["labels"])
    lr = task["learning_rate"]
    model = None

    temp_path = "scriptmodule.pt"
    # with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # temp_path = temp_file.name
    client.fget_object(bucketname, hash_id, temp_path)
    with open('scriptmodule.pt', 'rb') as f:
        buffer = io.BytesIO(f.read())
    model = torch.jit.load(buffer)
    
    # model = torch.jit.load(temp_path)
    os.remove(temp_path)

    inputs = torch.tensor(batch_data, dtype=torch.float32)
    labels = torch.tensor(batch_labels, dtype=torch.long)
    optimizer = optim.SGD(model.parameters(), lr=lr)

    outputs = model(inputs)

    criterion = nn.CrossEntropyLoss()
    loss = criterion(outputs, labels)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    logging.info(f"Processed batch. Loss: {loss.item()}")

    # PUT BACK IN QUEUE

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        buffer = io.BytesIO()
        torch.jit.save(model, buffer)
        temp_file.write(buffer.getvalue())
        temp_path = temp_file.name

    client.fput_object(bucketname, task["hash_id"], temp_path)
    os.remove(temp_path)

    updated_task = {
        "hash_id": task["hash_id"],
        "steps": task["steps"] + 1,
        "max_steps": task["max_steps"],
        "learning_rate": lr,
        "data": batch_data.tolist(),
        "labels": batch_labels.tolist(),
    }

    ch.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(updated_task), properties=pika.BasicProperties(delivery_mode=2))
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_tasks():
    connection = pika.BlockingConnection(pika.ConnectionParameters(cluster_name)) 
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    
    channel.basic_consume(queue=queue_name, on_message_callback=process_training_task)
    
    logger.info("Waiting for tasks...")
    print("Waiting for tasks...")
    channel.start_consuming()

consume_tasks()