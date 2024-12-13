"""
Please follow the instructions from the README

1. Run 'python3 demo.py' to get initial prediction
2. Put torchscript model into server e.g:
    - 'curl -X POST -H "Content-Type: application/json" -d '{<your data here>}' http://127.0.0.1:5000/train'
3. Download trained mode:
    - 'curl --output output/run3.pth http://127.0.0.1:5000/model/<put-hash-here>'
4. Run 'python3 demo.py' again to get final prediction from trained model
"""

import os
import torch
import requests
import numpy as np
from time import sleep
from worker.utils import SimpleModel
from torchvision.datasets import MNIST
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from torchvision.transforms import ToTensor

# load MNIST
print("Loading MNIST...")
mnist_train = MNIST(root="./data", train=True, transform=ToTensor(), download=True)
data = np.array([mnist_train[i][0].numpy().flatten() for i in range(len(mnist_train))])
labels = np.array([mnist_train[i][1] for i in range(len(mnist_train))])

task = {
    "data": data.tolist(),
    "labels": labels.tolist(),
    "batch_size": 64,
    "epochs": 5,
    "lr": 0.01
}

# train model
print("Uploading model...")
response = requests.post("http://localhost:5000/train", json=task)
model_hash = response.text

print(f"Training model {model_hash}...")
prev = None
while True:
    response = requests.get(f"http://localhost:5000/status/{model_hash}")
    loss = response.text
    print(f"Loss: {loss}")
    if loss == prev: break
    prev = loss
    sleep(5)

# download model
output_path = "models/trained_model.pth"
print(f"Downloading model {model_hash}...")
# exit(0)
os.system(f"curl --output {output_path} http://127.0.0.1:5000/model/{model_hash}")

# load model
simple_model = SimpleModel()
model = torch.jit.load(output_path)
model.eval()
simple_model.eval()

# load MNIST
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])
test_dataset = MNIST(root="./data", train=False, transform=transform, download=True)
test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)

# output prediction
correct, simple_correct = 0, 0
num_times = 0
with torch.no_grad():
    for i, (images, labels) in enumerate(test_loader):
        output = model(images)
        _, pred = torch.max(output, 1)
        if labels.item() == pred.item():
            correct +=1
        num_times += 1

    for i, (images, labels) in enumerate(test_loader):
        output = simple_model(images)
        _, pred = torch.max(output, 1)
        if labels.item() == pred.item():
            simple_correct +=1
        num_times += 1

print(f"Base model accuracy: {(simple_correct/num_times)*100}%")
print(f"Trained model accuracy: {(correct/num_times)*100}%")