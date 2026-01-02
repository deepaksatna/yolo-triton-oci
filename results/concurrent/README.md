# Concurrent Benchmark Results

Results from concurrent/load benchmarking (CONCURRENCY=8+).

## Purpose

Measures realistic production performance under concurrent load.
Shows true TensorRT advantage (20-30x speedup) and batching benefits.

## Configuration

```python
ITERATIONS = 200
CONCURRENCY = 8  # or 16, 32 for stress testing
```

## Add Your Results Here

Run benchmarks and copy files:
```bash
cd ../../benchmarking
# Edit benchmark_all_pods.py: CONCURRENCY = 8
python3 benchmark_all_pods.py

# Copy results
cp /mnt/coecommonfss/llmcore/benchmarking/*.json .
cp /mnt/coecommonfss/llmcore/benchmarking/benchmark_report_*.txt .
```

Files will be ignored by git until you commit them.

## Key Insights

- PyTorch degrades 2.5x under concurrent load (GIL limitation)
- TensorRT maintains low latency
- nim-batching excels (2-3x better than other NIMs)
- Throughput gap: 976 FPS vs 40 FPS (24x!)
