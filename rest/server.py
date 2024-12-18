import io
import os
import redis
import torch
import hashlib
import logging
import tempfile
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
bucketname='demobucket2'
logger.info("checking minio connection...")
if not client.bucket_exists(bucketname):
    client.make_bucket(bucketname)
    logger.info(f"Bucket '{bucketname}' created successfully!")
else:
    logger.info(f"Bucket '{bucketname}' already exists.")

# REDIS
redis_host = os.getenv("REDIS_HOST") or "localhost"
redisClient = redis.StrictRedis(host=redis_host, port=6379, db=0)
try:
    if redisClient.ping():
        logger.info("Connected to Redis successfully!")
except redis.ConnectionError:
    logger.info("Failed to connect to Redis.")
    exit(1)

app = Flask(__name__)

@app.route('/train', methods=['POST'])
def train():
    r = request.get_json()

    # ADD MODEL TO MINIO
    encoded_model = r.get("model") # user should upload torchscript model
    if not encoded_model:
        model = SimpleModel()
        scripted_model = torch.jit.script(model)
        buffer = io.BytesIO()
        torch.jit.save(scripted_model, buffer)

    model_hash = hashlib.sha256(buffer.getvalue()).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(buffer.getvalue())
        temp_path = temp_file.name

    # upload to minio
    client.fput_object(bucketname, model_hash, temp_path)
    os.remove(temp_path)

    # send to rabbitmq
    send_training_task(model_hash, r)
    
    return model_hash, 200

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
    loss = redisClient.get(hash_id)
    if not loss:
        return abort(404, description = f"Could not retrieve loss for hash: {hash_id}")
    # return f"***GET /status: training run {object_name} loss: {loss}"
    return loss.decode('utf-8'), 200

app.run(host="0.0.0.0", debug=True, port=5000)