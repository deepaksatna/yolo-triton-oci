# nim-binary (TensorRT HTTP Binary)

NVIDIA Triton Inference Server with TensorRT-optimized YOLO model using HTTP binary protocol.

## Purpose

Simple HTTP-only TensorRT deployment for straightforward integrations.

## Features

- NVIDIA Triton Inference Server
- TensorRT engine (FP16 optimized)
- HTTP binary protocol only
- Single GPU instance

## Build

This uses the official NVIDIA NIM image with TensorRT conversion:

```bash
# Use NVIDIA base image
FROM nvcr.io/nvidia/tritonserver:23.10-py3

# Add model repository and conversion scripts
# See deployment.yaml for init container that converts ONNX to TensorRT
```

## Expected Performance

- Sequential latency: ~7-10ms per request
- Throughput: ~130 FPS (sequential)
- Concurrent (8 workers): ~15ms latency, ~640 FPS
- **Speedup vs PyTorch: 10x**

## Deployment

See `kubernetes/nim-binary/deployment.yaml`

Uses init container to convert ONNX → TensorRT on first deployment.
