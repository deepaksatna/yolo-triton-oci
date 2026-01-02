# nim-batching (TensorRT High Throughput)

NVIDIA Triton Inference Server with TensorRT optimization and dynamic batching for maximum throughput.

## Purpose

Highest throughput TensorRT deployment for production workloads with concurrent users.

## Features

- NVIDIA Triton Inference Server
- TensorRT engine (FP16 optimized)
- **Dynamic batching** (5ms queue delay)
- HTTP + gRPC protocols
- Dual instances for better concurrency

## Dynamic Batching

Automatically groups concurrent requests into batches for GPU efficiency:
- Max batch size: 8
- Preferred batch sizes: [4, 8]
- Max queue delay: 5000 microseconds (5ms)

## Expected Performance

- Sequential latency: ~8-12ms per request
- Throughput: ~120 FPS (sequential)
- Concurrent (8 workers): ~12ms latency, ~976 FPS
- Concurrent (16 workers): ~15ms latency, ~1066 FPS
- **Speedup vs PyTorch: 24x (concurrent load)**

## Best For

- High concurrent request volume (100+ req/sec)
- Batch video processing
- Production workloads with multiple users
- Can tolerate 5ms batching delay for better throughput

## Deployment

See `kubernetes/nim-batching/deployment.yaml`

Uses init container to convert ONNX → TensorRT on first deployment.
