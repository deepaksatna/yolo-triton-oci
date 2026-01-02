# Sequential Benchmark Results

Results from sequential benchmarking (CONCURRENCY=1).

## Purpose

Measures pure inference latency without concurrency overhead.
Shows baseline TensorRT optimization (8-10x speedup).

## Configuration

```python
ITERATIONS = 50
CONCURRENCY = 1
```

## Add Your Results Here

Run benchmarks and copy files:
```bash
cd ../../benchmarking
# Edit benchmark_all_pods.py: CONCURRENCY = 1
python3 benchmark_all_pods.py

# Copy results
cp /mnt/coecommonfss/llmcore/benchmarking/*.json .
cp /mnt/coecommonfss/llmcore/benchmarking/benchmark_report_*.txt .
```

Files will be ignored by git until you commit them.
