# Automatic Neural Network Training

<div align="center" >
  <img src="./public/PROJECT DIAGRAM.svg" alt="PROJECT_DIAGRAM">
  <br/>
    CSCI 4253 Final Project: Automatic Neural Network Training
  <br/>
  Kevin Buhler
  <br/>
</div>

A service that fully automates deep-learning training jobs. It works for any model and on any data, as I found a way to upload and download general PyTorch models using TorchScript. 

You can upload a TorchScript model and NumPy dataset. You then make a POST request to /train that will create a new training job for you. The compute side of things will automatically be taken care of (no worrying about what GPU). You retrieve a hash ID which you can use to query /status/<hash_id> to retrieve the real-time status of your model’s loss. Once satisfied with the loss, or if the training job is done, you can send another GET request to /model/<hash_id> to download the model.

### How to run (locally)

Ensure that Docker and Kubernetes are installed on your machine and then run:

```bash
pip install requirements.txt
chmod +x run.sh
./run.sh
```

This will run the Flask server at http://127.0.0.1:5000. The amount of workers is handled by Kubernete's horizontal pod autoscaling. You can configure the max amount of worker in `worker/autoscale.yaml`.

### Demo

Once you have started the system up using the above commands, you can run the demo:

```bash
python3 demo.py
```

This will upload a simple MLP to the cloud and train it on MNIST for 2 epochs. It will then download the model and then run inference and collect accuracy. Overall this should take about 3 minutes.

### Prometheus

If you want to set up the basic Prometheus server:

```bash
chmod +x prometheus.sh
./prometheus.sh
```

You can then go to http://localhost:9090/query to see the metrics dashboard.

### API Routes

```bash
POST /train: 
- Create a training run
- Returns a SHA-256 hash to track training run

Body parameters
- model: upload a base64 encoded torchscript buffer
- data: numpy data to train on
- labels: numpy labels
- lr: learning rate
- epochs: number of times to iterate through entire data
- batch_size: number of samples per batch
```

```bash
GET /status/<string:hash_id>
- Returns latest batch loss from your training run
```

```bash
GET /model/<string:hash_id>
- Downloads trained model to your machine
```

### Software

- Kubernentes/Prometheus
- PyTorch/TorchScript
- MinIO
- Flask
- RabbitMQ
- Redis

### Links

Video: https://youtu.be/28F5CsZQOkM

Google Presentation: https://docs.google.com/presentation/d/1k9oQsrNGXxIDuBNtueDJWNB6viMZAbZzK02bsGo-EB4/edit?usp=sharing