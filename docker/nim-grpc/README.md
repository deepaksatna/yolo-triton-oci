# nim-grpc (TensorRT Low Latency)

NVIDIA Triton Inference Server with TensorRT optimization, supporting both HTTP and gRPC protocols.

## Purpose

Lowest latency TensorRT deployment, ideal for real-time applications.

## Features

- NVIDIA Triton Inference Server
- TensorRT engine (FP16 optimized)
- HTTP + gRPC protocols
- Optimized for low latency

## Expected Performance

- Sequential latency: ~8-12ms per request
- Throughput: ~100 FPS (sequential)
- Concurrent (8 workers): ~14ms latency, ~678 FPS
- **Speedup vs PyTorch: 8-10x**

## Protocols

- **HTTP:** Port 8000
- **gRPC:** Port 8001 (recommended for lowest latency)

## Deployment

See `kubernetes/nim-grpc/deployment.yaml`

Uses init container to convert ONNX → TensorRT on first deployment.
