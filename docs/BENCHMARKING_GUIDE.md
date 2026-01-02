# Benchmarking Guide

Complete guide for benchmarking all YOLO deployments.

## Overview

The benchmarking suite provides:
- **Sequential testing:** Pure inference latency (baseline)
- **Concurrent testing:** Realistic production load (8+ concurrent users)
- **Automatic comparison:** All 4 deployments in one run
- **Comprehensive reports:** Performance metrics and recommendations

## Quick Start

```bash
cd benchmarking

# Terminal 1: Setup port forwarding
./setup_port_forwarding.sh
# Keep this running!

# Terminal 2: Run benchmarks
python3 benchmark_all_pods.py
```

## Configuration

Edit `benchmark_all_pods.py` (lines 63-64):

```python
ITERATIONS = 50          # Total number of requests
CONCURRENCY = 1          # Sequential vs concurrent
```

### Recommended Settings

| Test Type | ITERATIONS | CONCURRENCY | Runtime | Purpose |
|-----------|------------|-------------|---------|---------|
| Baseline | 50 | 1 | ~5 min | Pure latency |
| Light load | 100 | 4 | ~10 min | Light testing |
| **Realistic** | **200** | **8** | **~30 min** | **Production simulation** |
| Heavy load | 500 | 16 | ~60 min | Stress testing |
| Extreme | 1000 | 32 | ~90 min | Find limits |

## Testing Workflow

### 1. Sequential Baseline

**Purpose:** Establish baseline performance

```python
ITERATIONS = 50
CONCURRENCY = 1
```

**Run:**
```bash
python3 benchmark_all_pods.py
```

**Save Results:**
```bash
cp /mnt/coecommonfss/llmcore/benchmarking/*_internal.json ../results/sequential/
cp /mnt/coecommonfss/llmcore/benchmarking/benchmark_report_*.txt ../results/sequential/
```

**Expected Output:**
```
Deployment      | Framework  | Mean (ms) | FPS   | Speedup
----------------------------------------------------------------
nim-binary      | TensorRT   |     7.44  | 134.5 | 10.7x
nim-batching    | TensorRT   |     7.79  | 128.4 | 10.2x
nim-grpc        | TensorRT   |    10.03  |  99.7 | 8.0x
base-yolo       | PyTorch    |    80.25  |  12.5 | Baseline
```

### 2. Concurrent Load Testing

**Purpose:** Realistic production performance

```python
ITERATIONS = 200
CONCURRENCY = 8
```

**Run:**
```bash
python3 benchmark_all_pods.py
```

**Save Results:**
```bash
cp /mnt/coecommonfss/llmcore/benchmarking/*_internal.json ../results/concurrent/
cp /mnt/coecommonfss/llmcore/benchmarking/benchmark_report_*.txt ../results/concurrent/
```

**Expected Output:**
```
Deployment      | Framework  | Mean (ms) | Throughput   | Mode
------------------------------------------------------------------------
nim-binary      | TensorRT   |    12.50  | 640 FPS      | concurrent (c=8)
nim-batching    | TensorRT   |     8.20  | 976 FPS      | concurrent (c=8)
nim-grpc        | TensorRT   |    11.80  | 678 FPS      | concurrent (c=8)
base-yolo       | PyTorch    |   200.00  |  40 FPS      | concurrent (c=8)
```

## Understanding Results

### Key Metrics

1. **Mean Latency (ms)**
   - Average time per request
   - Lower is better
   - Sequential: Pure inference time
   - Concurrent: Includes queueing + inference

2. **P95 Latency (ms)**
   - 95% of requests complete within this time
   - Critical for SLA planning
   - Use this for capacity planning

3. **Throughput (FPS)**
   - Sequential: Theoretical (1000ms / mean_latency)
   - Concurrent: Actual (total_requests / total_time)
   - Shows real production capacity

4. **Speedup**
   - TensorRT vs PyTorch baseline
   - Sequential: 8-10x typically
   - Concurrent: 20-30x (PyTorch GIL limitation)

### Performance Analysis

**Sequential Results:**
- Shows pure TensorRT optimization (8-10x)
- All NIMs similar (~7-12ms)
- PyTorch baseline (~80-100ms)

**Concurrent Results:**
- Shows production reality
- nim-batching excels (dynamic batching)
- PyTorch degrades 2.5x (GIL)
- TensorRT throughput 20-30x better

## Advanced Configuration

### High Concurrency Testing

For stress testing:

```python
ITERATIONS = 500
CONCURRENCY = 16  # or 32
```

**Warning:** High concurrency (>16) may cause:
- Timeout errors (10-20% expected)
- Higher latencies
- Resource contention

**When to use:**
- Capacity planning
- Finding system limits
- Testing nim-batching advantage

### Port Forwarding Details

The `setup_port_forwarding.sh` script maps:

```
base-yolo:     127.0.0.1:8000
nim-binary:    127.0.0.1:8100
nim-grpc:      127.0.0.1:8200 (HTTP), 127.0.0.1:8201 (gRPC)
nim-batching:  127.0.0.1:8300 (HTTP), 127.0.0.1:8301 (gRPC)
```

**Manual setup:**
```bash
kubectl port-forward -n yolo-base svc/yolo-base-service 8000:80 &
kubectl port-forward -n yolo-nim-binary svc/yolo-nim-binary-service 8100:80 &
# etc...
```

## Troubleshooting

### Port Forwarding Fails

**Symptom:** "connection refused" or "port already in use"

**Solution:**
```bash
# Kill existing port forwards
pkill -f "kubectl port-forward"

# Restart
./setup_port_forwarding.sh
```

### High Error Rate

**Symptom:** >20% errors during concurrent testing

**Solution:**
```bash
# Reduce concurrency
CONCURRENCY = 8  # instead of 32

# Or reduce iterations
ITERATIONS = 100  # instead of 1000
```

### nim-batching Warmup Fails

**Symptom:** "Warmup complete (0/10 successful)"

**Solution:**
```bash
# Check pod status
kubectl get pods -n yolo-nim-batching

# If CUDA errors, restart pod
kubectl delete pod -n yolo-nim-batching <pod-name>

# Wait for TensorRT rebuild (5-10 min)
kubectl wait --for=condition=ready pod -l app=yolo-nim-batching -n yolo-nim-batching --timeout=600s
```

### Benchmark Hangs

**Symptom:** No progress for >5 minutes

**Solution:**
```bash
# Check port forwarding still running (Terminal 1)

# Test endpoints manually
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8100/v2/health/ready

# Restart if needed
Ctrl+C on both terminals
./setup_port_forwarding.sh  # Terminal 1
python3 benchmark_all_pods.py  # Terminal 2
```

## Interpreting Reports

### Report Sections

1. **Performance Summary**
   - Quick comparison table
   - Shows best performer for each metric

2. **Detailed Results**
   - Full statistics for each deployment
   - All latency percentiles (P50, P90, P95, P99)

3. **Analysis & Recommendations**
   - Deployment recommendations
   - Use case guidance
   - TensorRT speedup calculation

4. **Key Findings**
   - Highlights important insights
   - Business justification

### Example Analysis

From concurrent testing (CONCURRENCY=8):

```
nim-batching: 976 FPS, 8.20ms mean latency
base-yolo:     40 FPS, 200ms mean latency

Speedup: 24x
Interpretation:
- nim-batching can handle 24x more requests
- Same workload needs 24x fewer GPUs
- Cost savings: $10,000/month → $417/month
```

## Best Practices

1. **Always run sequential first**
   - Establishes baseline
   - Verifies all deployments working

2. **Use CONCURRENCY=8 for comparison**
   - Realistic production load
   - Low error rate
   - Good balance of speed/reliability

3. **Save results immediately**
   - Copy to results/ directory
   - Commit to git
   - Add notes about configuration

4. **Test at expected production load**
   - Match your concurrent user count
   - Helps with capacity planning

5. **Monitor errors**
   - 0-5%: Excellent
   - 5-10%: Acceptable
   - >10%: Reduce concurrency

## Next Steps

After benchmarking:
1. Save results to `results/` directory
2. Review recommendations in report
3. Choose deployment based on workload:
   - **Low latency:** nim-grpc
   - **High throughput:** nim-batching
   - **Simple HTTP:** nim-binary
   - **Baseline:** base-yolo (comparison only)

---

For detailed load testing guide, see `benchmarking/LOAD_TESTING_GUIDE.txt`

**Last Updated:** 2026-01-01
