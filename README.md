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
- batch_data: numpy batch data to train on
- batch_labels: numpy batch labels
- model: upload a base64 encoded torchscript buffer
- lr: learning rate
- steps: maximum number of steps to train for

Example:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"lr": 0.1}' http://127.0.0.1:5000/train
```

GET /weights/<string:hash_id>

Example:
```bash
curl --output weights/run3.pt http://127.0.0.1:5000/weights/c1c8a53df5be3a2f7e73f6e3b7efe44553ae26ca448818d39404b75a7a9b3875
```

### Components
Kubernentes/Prometheus
PyTorch/TorchScript
MinIO
Flask
RabbitMQ

### Interactions
Flask <-> RabbitMQ <-> Kubernetes worker <-> minio blob storage
