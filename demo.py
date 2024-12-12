"""
Please follow the instructions from the README

1. Run 'python3 demo.py' to get initial prediction
2. Put torchscript model into server e.g:
    - 'curl -X POST -H "Content-Type: application/json" -d '{<your data here>}' http://127.0.0.1:5000/train'
3. Download trained mode:
    - 'curl --output output/run3.pth http://127.0.0.1:5000/model/<put-hash-here>'
4. Run 'python3 demo.py' again to get final prediction from trained model

"""

import torch

print("Model Prediction:")
print("Correct:")