import os
import pika
import json
import torch
import hashlib
import tempfile
import torch.nn as nn

cluster_name = "localhost"
queue_name = "bob"

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

def send_training_task(batch_data, batch_labels, model_hash, lr=0.001):
    connection = pika.BlockingConnection(pika.ConnectionParameters(cluster_name))  
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    # serialized_model_hash = my_hash(model)

    task = {
        "hash_id": model_hash,
        "data": batch_data.tolist(),
        "learning_rate": lr,
        "labels": batch_labels.tolist(),
    }

    channel.basic_publish(exchange="",routing_key=queue_name,body=json.dumps(task),properties=pika.BasicProperties(delivery_mode=2))

    print("Task added to mq")
    # connection.close() # NOTE: how to close this connection without closing post request connection?