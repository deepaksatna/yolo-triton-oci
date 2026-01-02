# Benchmark Results

This directory contains performance benchmark results for all YOLO deployments.

## Structure

```
results/
├── sequential/         # Sequential benchmarking results (CONCURRENCY=1)
│   ├── base-yolo_internal.json
│   ├── nim-binary_internal.json
│   ├── nim-grpc_internal.json
│   ├── nim-batching_internal.json
│   ├── benchmark_report_YYYYMMDD_HHMMSS.txt
│   └── all_results_YYYYMMDD_HHMMSS.json
│
└── concurrent/         # Concurrent benchmarking results (CONCURRENCY=8+)
    ├── base-yolo_internal.json
    ├── nim-binary_internal.json
    ├── nim-grpc_internal.json
    ├── nim-batching_internal.json
    ├── benchmark_report_YYYYMMDD_HHMMSS.txt
    └── all_results_YYYYMMDD_HHMMSS.json
```

## How to Add Results

1. Run benchmarks with desired concurrency level:
   ```bash
   cd ../benchmarking

   # For sequential
   # Edit benchmark_all_pods.py: CONCURRENCY = 1
   python3 benchmark_all_pods.py

   # For concurrent
   # Edit benchmark_all_pods.py: CONCURRENCY = 8
   python3 benchmark_all_pods.py
   ```

2. Copy results to appropriate directory:
   ```bash
   # Sequential results
   cp /mnt/coecommonfss/llmcore/benchmarking/*_internal.json ../results/sequential/
   cp /mnt/coecommonfss/llmcore/benchmarking/benchmark_report_*.txt ../results/sequential/
   cp /mnt/coecommonfss/llmcore/benchmarking/all_results_*.json ../results/sequential/

   # Concurrent results
   cp /mnt/coecommonfss/llmcore/benchmarking/*_internal.json ../results/concurrent/
   cp /mnt/coecommonfss/llmcore/benchmarking/benchmark_report_*.txt ../results/concurrent/
   cp /mnt/coecommonfss/llmcore/benchmarking/all_results_*.json ../results/concurrent/
   ```

3. Commit results to git:
   ```bash
   git add results/
   git commit -m "Add benchmark results: sequential/concurrent YYYYMMDD"
   git push
   ```

## Result Files

### Individual Results (`*_internal.json`)
JSON files containing detailed metrics for each deployment:
- Latency statistics (min, max, mean, p50, p90, p95, p99)
- Throughput (FPS)
- Protocol and framework information
- Concurrency level (if applicable)

### Comprehensive Report (`benchmark_report_*.txt`)
Human-readable report including:
- Performance summary table
- Detailed statistics for each deployment
- Analysis and recommendations
- TensorRT speedup calculations

### All Results (`all_results_*.json`)
Combined JSON with all deployment results for programmatic analysis.

## Expected Results

### Sequential (CONCURRENCY=1)
| Deployment | Mean Latency | Throughput | Speedup |
|------------|--------------|------------|---------|
| nim-binary | 7-10 ms | 130 FPS | 10x |
| nim-grpc | 8-12 ms | 100 FPS | 8x |
| nim-batching | 8-12 ms | 120 FPS | 9x |
| base-yolo | 80-100 ms | 12 FPS | Baseline |

### Concurrent (CONCURRENCY=8)
| Deployment | Mean Latency | Throughput | Speedup |
|------------|--------------|------------|---------|
| nim-binary | 15 ms | 640 FPS | 16x |
| nim-grpc | 14 ms | 678 FPS | 17x |
| nim-batching | 12 ms | 976 FPS | **24x** |
| base-yolo | 200 ms | 40 FPS | Baseline |

## Notes

- Results vary based on GPU model (expected: NVIDIA A10)
- Concurrent results show TensorRT's true advantage (20-30x vs PyTorch)
- nim-batching excels at high concurrency due to dynamic batching
- Add your actual results here for documentation
