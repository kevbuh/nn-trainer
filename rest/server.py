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

    # R DATA
    batch_data = r.get("batch_data", np.random.randn(32, 784))
    batch_labels = r.get("batch_labels", np.random.randint(0, 10, size=(32,)))
    lr = r.get("lr", 0.01)
    steps = r.get("steps", 10)

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

    # SEND TO RABBITMQ
    send_training_task(batch_data, batch_labels, model_hash, lr=lr, steps=int(steps))
    
    return f"***POST /train --- Track progress with hash: {model_hash}"

@app.route('/weights/<string:hash_id>', methods=['GET'])
def weights(hash_id):
    logger.info("GET /weights called")
    # object_name = f"{hash_id}_weights"
    object_name = hash_id

    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            client.fget_object(bucketname, object_name, temp_path)
        return send_file(temp_path, as_attachment=True)
    except Exception as e:
        return abort(404, description = f"Could not retrieve weights: {str(e)}")

# @app.route('/inference', methods=['GET'])
# def inference():
#     # get model weights
#     # get picture
#     # output inference
#     r = request.get_json()
    
#     return "***GET /inference"

app.run(host="0.0.0.0", debug=True, port=5000)