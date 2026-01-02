#!/usr/bin/env python3
"""
Base PyTorch YOLO Inference Server
Provides baseline performance metrics for comparison with TensorRT NIMs
"""
from flask import Flask, request, jsonify
import torch
from ultralytics import YOLO
import numpy as np
import time
import cv2
from io import BytesIO
import base64
import os

app = Flask(__name__)

# Load model
print("Loading YOLOv8s model...")
model_path = os.getenv("MODEL_PATH", "yolov8s.pt")
print(f"Model path: {model_path}")

model = YOLO(model_path)
model.to('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Model loaded on {'GPU' if torch.cuda.is_available() else 'CPU'}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'deployment': 'base-pytorch',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    })

@app.route('/infer', methods=['POST'])
def infer():
    """Single inference endpoint"""
    try:
        data = request.json or {}
        image_data = data.get('image')

        # Decode image or use random test image
        if image_data:
            img_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            # Random test image
            img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # Inference
        start = time.time()
        results = model(img)
        latency = (time.time() - start) * 1000

        # Extract detections
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                detections.append({
                    'bbox': box.xyxy[0].cpu().numpy().tolist(),
                    'confidence': float(box.conf[0]),
                    'class': int(box.cls[0])
                })

        return jsonify({
            'detections': detections,
            'latency_ms': latency,
            'deployment': 'base-pytorch',
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/benchmark', methods=['POST'])
def benchmark():
    """Internal benchmarking endpoint"""
    iterations = request.args.get('iterations', 100, type=int)

    latencies = []
    img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # Warmup
    for _ in range(10):
        model(img)

    # Benchmark
    start_time = time.time()
    for _ in range(iterations):
        start = time.time()
        model(img)
        latencies.append((time.time() - start) * 1000)

    total_time = time.time() - start_time

    return jsonify({
        'iterations': iterations,
        'total_time_sec': total_time,
        'fps': iterations / total_time,
        'latency_ms': {
            'min': min(latencies),
            'max': max(latencies),
            'mean': sum(latencies) / len(latencies),
            'p95': sorted(latencies)[int(len(latencies) * 0.95)]
        },
        'deployment': 'base-pytorch',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
