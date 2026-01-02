# base-yolo (PyTorch Baseline)

PyTorch-based YOLO inference server using Ultralytics YOLO.

## Purpose

Provides baseline performance for comparison with TensorRT-optimized NIMs.

## Features

- Flask HTTP server
- PyTorch + Ultralytics YOLO
- GPU support
- Three endpoints:
  - `/health` - Health check
  - `/infer` - Single inference
  - `/benchmark` - Internal benchmarking

## Build

```bash
docker build -t fra.ocir.io/<namespace>/yolo-base-pytorch:latest .
docker push fra.ocir.io/<namespace>/yolo-base-pytorch:latest
```

## Run Locally

```bash
docker run -p 8080:8080 --gpus all yolo-base-pytorch:latest
```

## Test

```bash
# Health check
curl http://localhost:8080/health

# Inference (random image)
curl -X POST http://localhost:8080/infer \
  -H "Content-Type: application/json" \
  -d '{}'

# Benchmark
curl -X POST "http://localhost:8080/benchmark?iterations=50"
```

## Expected Performance

- Sequential latency: ~80-100ms per request
- Throughput: ~12 FPS (sequential)
- Concurrent (8 workers): ~200ms latency, ~40 FPS

## Deployment

See `kubernetes/base-yolo/deployment.yaml`
