import io
import os
import torch
import hashlib
import logging
import tempfile
import numpy as np
from minio import Minio
from flask import Flask, request, abort, send_file
from worker.utils import SimpleModel, send_training_task

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
logger.info("checking minio connection...")
if not client.bucket_exists(bucketname):
    client.make_bucket(bucketname)
    logger.info(f"Bucket '{bucketname}' created successfully!")
else:
    logger.info(f"Bucket '{bucketname}' already exists.")

app = Flask(__name__)

@app.route('/train', methods=['POST'])
def train():
    r = request.get_json()

    # REQUEST BODY
    data = np.array(r.get("data", np.random.randn(320, 784)))
    labels = np.array(r.get("labels", np.random.randint(0, 10, size=(320,))))
    batch_size = r.get("batch_size", 32)
    epochs = r.get("epochs", 1)
    steps = r.get("steps", 3) # steps per batch per worker
    lr = r.get("lr", 0.01)

    # ADD TO MINIO
    encoded_model = r.get("model") # user uploads torchscript model

    if not encoded_model:
        model = SimpleModel()
        scripted_model = torch.jit.script(model)
        buffer = io.BytesIO()
        torch.jit.save(scripted_model, buffer)

    # model_bytes = base64.b64decode(encoded_model)
    model_hash = hashlib.sha256(buffer.getvalue()).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(buffer.getvalue())
        temp_path = temp_file.name

    client.fput_object(bucketname, model_hash, temp_path)
    os.remove(temp_path)

    # TRAINING LOOP
    batches = (data.shape[0] + batch_size - 1) // batch_size
    print(f"STARTING TRAINING RUN: {epochs=}, {batches=}")

    for _ in range(epochs): # loops through all data
        for i in range(batches): # loop through all batches
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, data.shape[0])
            batch_data = data[start_idx:end_idx]
            batch_labels = labels[start_idx:end_idx]

            # SEND TO RABBITMQ
            send_training_task(batch_data, batch_labels, model_hash, lr=lr, steps=steps)
    
    return f"***POST /train --- Track progress with hash: {model_hash}"

@app.route('/model/<string:hash_id>', methods=['GET'])
def model(hash_id):
    logger.info("GET /model called")
    # object_name = f"{hash_id}_weights"
    object_name = hash_id

    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            client.fget_object(bucketname, object_name, temp_path)
        return send_file(temp_path, as_attachment=True)
    except Exception as e:
        return abort(404, description = f"Could not retrieve weights: {str(e)}")
    
@app.route('/status/<string:hash_id>', methods=['GET'])
def status(hash_id):
    logger.info("GET /weights called")
    # object_name = f"{hash_id}_weights"
    object_name = hash_id

    return "***GET /status: training run {object_name} loss: "

app.run(host="0.0.0.0", debug=True, port=5000)