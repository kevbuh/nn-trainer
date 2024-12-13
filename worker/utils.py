import os
import pika
import json
import torch
import hashlib
import tempfile
import numpy as np
import torch.nn as nn

cluster_name = "localhost"
queue_name = "model_queue"

def my_hash(val):
    return hashlib.sha256(val.encode()).hexdigest()

def serialize_model(model):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
        # torch.save(model, temp_path)
        scripted_model = torch.jit.script(model)
        scripted_model.save(temp_path)
        with open(temp_path, "rb") as f:
            model_bytes = f.read()
        os.remove(temp_path)
    return model_bytes
    # buffer = io.BytesIO()
    # torch.save(model.state_dict(), buffer)
    # buffer.seek(0)
    # return base64.b64encode(buffer.read())#.decode('utf-8')

class SimpleModel(nn.Module): # for MNIST
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.fc(x)

def send_training_task(model_hash, r):
    connection = pika.BlockingConnection(pika.ConnectionParameters(cluster_name))  
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    # REQUEST BODY
    data = np.array(r.get("data"))
    labels = np.array(r.get("labels"))
    batch_size = r.get("batch_size")
    epochs = r.get("epochs")
    lr = r.get("lr")

    # TRAINING LOOP
    batches = (data.shape[0] + batch_size - 1) // batch_size
    print(f"STARTING TRAINING RUN: {epochs=}, {batches=}")

    for _ in range(epochs): # loops through all data
        for b in range(batches): # loop through all batches
            start_idx = b * batch_size
            end_idx = min(start_idx + batch_size, data.shape[0])
            batch_data, batch_labels= data[start_idx:end_idx], labels[start_idx:end_idx]

            task = {
                "hash_id": model_hash,
                "data": batch_data.tolist(),
                "labels": batch_labels.tolist(),
                "learning_rate": lr,
            }

            channel.basic_publish(exchange="",routing_key=queue_name,body=json.dumps(task),properties=pika.BasicProperties(delivery_mode=2))

    print("Training run queued to RabbitMQ")
    connection.close() # NOTE: how to close this connection without closing post request connection?