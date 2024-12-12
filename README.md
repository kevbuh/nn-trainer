# nn-trainer

CSCI 4253 Final Project: Distributed Neural Network Batch Training

Kevin Buhler

### How to run

Ensure that Docker and Kubernetes are installed on your machine. 

```bash
pip install requirements.txt
chmod +x run.sh
./run.sh
```

This will run the Flask server at http://127.0.0.1:5000. You can configure the amount of workers in ```worker/deployment.yaml```.

If you want to set up the basic Prometheus server:
```bash
chmod +x prometheus.sh
./prometheus.sh
```

### API Routes

POST /train:

Body parameters
- data: numpy batch data to train on
- labels: numpy batch labels
- model: upload a base64 encoded torchscript buffer
- lr: learning rate
- steps: training steps per batch
- epochs: number of times to iterate through entire data
- batch_size: number of samples per batch

Example:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"lr": 0.1}' http://127.0.0.1:5000/train
```

GET /model/<string:hash_id>

Example:
```bash
curl --output output/run3.pth http://127.0.0.1:5000/model/62000807262c72a0af4c983b057077d22a44c2cca64205a7b1bce9753e3ee802
```

### Components
- Kubernentes/Prometheus
- PyTorch/TorchScript
- MinIO
- Flask
- RabbitMQ

### Interactions
Flask <-> RabbitMQ <-> Kubernetes worker <-> minio blob storage
