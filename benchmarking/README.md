# YOLO NIM Comprehensive Benchmarking Suite

Complete benchmarking solution for all 4 YOLO deployments with performance analysis and recommendations.

---

## 📋 What Gets Benchmarked

| Deployment | GPU | External IP | Protocols | Features |
|------------|-----|-------------|-----------|----------|
| **base-yolo** | - | 141.147.36.157 | HTTP | PyTorch baseline |
| **nim-binary** | GPU 1 | 138.2.160.196 | HTTP | Single instance |
| **nim-grpc** | GPU 2 | 138.3.255.156 | HTTP + gRPC | Optimized latency |
| **nim-batching** | GPU 3 | 92.5.3.38 | HTTP + gRPC | Dynamic batching |

---

## 🚀 Quick Start (2 Steps)

### Step 1: Setup Port Forwarding

Open **Terminal 1** and run:

```bash
cd /Users/deepsoni/Oracle\ Content\ -\ Accounts/Oracle\ Content/Projects/CoE_initial/CoE_base/000-AICoE-Knowledgebase/001-customers/2025-lab/YOLO-NIM/simplest/benchmarking

chmod +x setup_port_forwarding.sh
./setup_port_forwarding.sh
```

**Keep this terminal open!** It will show:
```
Port Forwarding Active
Port Mapping:
  base-yolo:     localhost:8000 (HTTP)
  nim-binary:    localhost:8100 (HTTP)
  nim-grpc:      localhost:8200 (HTTP), localhost:8201 (gRPC)
  nim-batching:  localhost:8300 (HTTP), localhost:8301 (gRPC)
```

### Step 2: Run Benchmarks

Open **Terminal 2** and run:

```bash
cd /Users/deepsoni/Oracle\ Content\ -\ Accounts/Oracle\ Content/Projects/CoE_initial/CoE_base/000-AICoE-Knowledgebase/001-customers/2025-lab/YOLO-NIM/simplest/benchmarking

python3 benchmark_all_pods.py
```

**Done!** The script will:
- ✅ Copy benchmark scripts to all pods
- ✅ Run internal benchmarks (true GPU performance)
- ✅ Test port forwarding endpoints
- ✅ Test external LoadBalancer endpoints
- ✅ Generate comprehensive comparison report

### 🔥 Load Testing (Concurrent Benchmarking)

**NEW:** The suite now supports concurrent load testing!

To enable load testing, edit `benchmark_all_pods.py`:

```python
# Line 64-65
ITERATIONS = 50          # Total number of requests
CONCURRENCY = 1          # Set to 8+ for load testing
```

**Examples:**
```python
CONCURRENCY = 1          # Sequential (default) - measure pure latency
CONCURRENCY = 8          # Medium load - 8 concurrent users
CONCURRENCY = 16         # Heavy load - 16 concurrent users
CONCURRENCY = 32         # Stress test - 32 concurrent users
```

**Key Differences:**
- **Sequential (concurrency=1):** Measures pure inference latency
- **Concurrent (concurrency>1):** Measures real throughput under load

📖 **Full Guide:** See `LOAD_TESTING_GUIDE.txt` for detailed examples and recommendations

---

## 📊 What You'll Get

### 1. Console Output
Real-time progress and results for each deployment

### 2. Individual Result Files
```
base-yolo_internal.json
nim-binary_internal.json
nim-grpc_internal.json
nim-batching_internal.json
```

### 3. Comprehensive Report
```
benchmark_report_YYYYMMDD_HHMMSS.txt
```

Contains:
- Performance summary table
- Detailed statistics for each deployment
- Analysis and recommendations
- Best deployment for your use case

### 4. All Results JSON
```
all_results_YYYYMMDD_HHMMSS.json
```

---

## 📈 Expected Results

Based on A10 GPU performance:

| Deployment | Expected Latency | Expected Throughput | Best For |
|------------|------------------|---------------------|----------|
| **nim-grpc** | 8-12 ms | 80-120 FPS | Lowest latency |
| **nim-batching** | 15-20 ms | 200-400 FPS | Highest throughput |
| **nim-binary** | 15-25 ms | 40-70 FPS | HTTP-only simplicity |
| **base-yolo** | 50-100 ms | 10-20 FPS | PyTorch baseline |

---

## 🔧 Files in This Directory

| File | Purpose |
|------|---------|
| `setup_port_forwarding.sh` | Setup port forwards for all pods |
| `benchmark_internal_universal.py` | Universal internal benchmark (HTTP + gRPC, with concurrency support) |
| `benchmark_base_yolo.py` | Custom PyTorch baseline benchmark |
| `benchmark_all_pods.py` | Main orchestrator script (supports load testing) |
| `README.md` | This file |
| `LOAD_TESTING_GUIDE.txt` | Complete guide for concurrent/load testing |
| `COMPLETE_BENCHMARKING_GUIDE.txt` | Comprehensive benchmarking guide |
| `QUICK_START.txt` | Quick reference guide |

---

## 📝 Detailed Usage

### Port Forwarding Script

**What it does:**
- Kills existing port forwards
- Sets up port forwarding for all 4 deployments
- Maps to unique localhost ports
- Keeps running until Ctrl+C

**Port Mapping:**
```
base-yolo:     8000 → 8000 (HTTP)
nim-binary:    8100 → 8000 (HTTP)
nim-grpc:      8200 → 8000 (HTTP), 8201 → 8001 (gRPC)
nim-batching:  8300 → 8000 (HTTP), 8301 → 8001 (gRPC)
```

**Manual test:**
```bash
# Test base-yolo
curl http://localhost:8000/v2/health/ready

# Test nim-grpc HTTP
curl http://localhost:8200/v2/health/ready

# Test nim-grpc gRPC (using curl for health)
curl http://localhost:8201/v2/health/ready
```

---

### Main Benchmark Script

**What it does:**

1. **Copy Scripts to Pods**
   - Copies `benchmark_internal_universal.py` to `/tmp/debug/` in each pod
   - Creates necessary directories

2. **Run Internal Benchmarks**
   - Executes benchmark inside each pod
   - Measures true GPU inference latency (no network)
   - Auto-detects HTTP or gRPC support
   - 50 iterations per deployment

3. **Test Port Forwarding**
   - Verifies localhost endpoints are accessible
   - Tests both HTTP and gRPC (where supported)

4. **Test External Endpoints**
   - Verifies LoadBalancer IPs are accessible
   - Confirms production readiness

5. **Generate Report**
   - Comprehensive performance analysis
   - Comparison table
   - Recommendations for your use case

**Customization:**

Edit `benchmark_all_pods.py` to change:
```python
ITERATIONS = 50  # Number of requests per test (default: 50)
```

For longer tests:
```python
ITERATIONS = 100  # More iterations = more accurate
```

---

### Universal Internal Benchmark

**What it does:**
- Auto-detects HTTP or gRPC support
- Runs warmup phase (10 iterations)
- Benchmarks with configurable iterations
- Saves results to `/tmp/debug/benchmark_results.json`

**Manual usage inside pod:**
```bash
# Auto-detect protocol, 50 iterations
python3 /tmp/debug/benchmark_internal_universal.py 50

# Force HTTP protocol
python3 /tmp/debug/benchmark_internal_universal.py 50 http

# Force gRPC protocol
python3 /tmp/debug/benchmark_internal_universal.py 50 grpc
```

---

## 🎯 Interpreting Results

### Latency Metrics

- **Mean**: Average latency (most important for typical workloads)
- **P95**: 95th percentile (important for SLA guarantees)
- **P99**: 99th percentile (worst-case latency)
- **Min/Max**: Best and worst observed latency

### Throughput (FPS)

- **Single request**: FPS = 1000 / mean_latency_ms
- **Batched**: Actual FPS depends on batch sizes achieved

### What "Good" Looks Like

**Excellent:**
- nim-grpc: < 15 ms mean latency
- nim-batching: > 200 FPS throughput

**Good:**
- nim-grpc: < 20 ms mean latency
- nim-batching: > 150 FPS throughput

**Acceptable:**
- nim-grpc: < 30 ms mean latency
- nim-batching: > 100 FPS throughput

---

## 🔍 Troubleshooting

### Issue 1: "Pod not found"

**Cause:** Deployment not running or wrong namespace

**Solution:**
```bash
kubectl get pods -A | grep yolo
```

Update `DEPLOYMENTS` in `benchmark_all_pods.py` with correct names.

---

### Issue 2: Port forwarding not accessible

**Symptoms:**
```
⚠ nim-grpc: Port forward may not be ready
```

**Solutions:**

1. **Check if port forwarding script is running:**
   ```bash
   ps aux | grep port-forward
   ```

2. **Kill old port forwards and restart:**
   ```bash
   pkill -f port-forward
   ./setup_port_forwarding.sh
   ```

3. **Test manually:**
   ```bash
   curl http://localhost:8200/v2/health/ready
   ```

---

### Issue 3: Internal benchmark fails

**Symptoms:**
```
✗ Internal benchmark failed for nim-grpc
```

**Possible causes:**

1. **tritonclient not installed in pod (for gRPC)**
   - nim-grpc and nim-batching should have it
   - Falls back to HTTP automatically

2. **Script not copied correctly**
   ```bash
   kubectl exec -n yolo-nim-grpc POD_NAME -c triton-server -- ls -la /tmp/debug/
   ```

3. **Pod not ready**
   ```bash
   kubectl get pods -n yolo-nim-grpc
   ```

---

### Issue 4: No results generated

**Cause:** All internal benchmarks failed

**Debug steps:**

1. **Check pod logs:**
   ```bash
   kubectl logs -n yolo-nim-grpc POD_NAME -c triton-server | tail -50
   ```

2. **Test manually:**
   ```bash
   kubectl exec -n yolo-nim-grpc POD_NAME -c triton-server -- \
     python3 /tmp/debug/benchmark_internal_universal.py 10
   ```

3. **Check Triton health:**
   ```bash
   kubectl exec -n yolo-nim-grpc POD_NAME -c triton-server -- \
     curl -s http://localhost:8000/v2/health/ready
   ```

---

## 📊 Sample Report Output

```
================================================================================
PERFORMANCE SUMMARY
================================================================================

Deployment      | Protocol | Mean (ms)  | P95 (ms)   | FPS      | Status
--------------------------------------------------------------------------------
nim-grpc        | GRPC     |      10.03 |      11.57 |    99.7  | ✓ Pass
nim-batching    | GRPC     |      11.25 |      12.80 |    88.9  | ✓ Pass
nim-binary      | HTTP     |      23.45 |      28.90 |    42.6  | ✓ Pass
base-yolo       | HTTP     |      78.32 |      95.40 |    12.8  | ✓ Pass

================================================================================
ANALYSIS & RECOMMENDATIONS
================================================================================

Best Performance:
  Lowest Latency:     nim-grpc (GRPC) - 10.03 ms
  Highest Throughput: nim-batching (GRPC) - 88.9 FPS

Recommendations:

1. For LOWEST LATENCY (real-time applications):
   → Use nim-grpc with gRPC protocol
   → Expected: 8-12ms per request
   → Best for: Real-time video processing, interactive applications

2. For HIGHEST THROUGHPUT (batch processing):
   → Use nim-batching with gRPC protocol
   → Dynamic batching automatically groups requests
   → Expected: 200-400 FPS (depending on batch sizes)
   → Best for: High-load production, batch inference

3. For SIMPLICITY (HTTP-only):
   → Use nim-binary with HTTP protocol
   → No gRPC client library needed
   → Expected: 15-25ms per request
   → Best for: Simple integrations, testing
```

---

## 🎓 Understanding the Deployments

### nim-grpc (Lowest Latency)
- **Purpose:** Minimize inference latency
- **Config:** Single instance, CUDA graphs, gRPC optimized
- **Use when:** Latency < 15ms required
- **Example:** Real-time video analysis, interactive apps

### nim-batching (Highest Throughput)
- **Purpose:** Maximize throughput for multiple requests
- **Config:** 2 instances, dynamic batching (5ms delay), CUDA graphs
- **Use when:** Handling 100+ concurrent requests
- **Example:** Batch video processing, high-load APIs

### nim-binary (Simplest)
- **Purpose:** Simple HTTP-only deployment
- **Config:** Single instance, HTTP binary protocol
- **Use when:** Simple integration, no gRPC library
- **Example:** Testing, development, simple services

### base-yolo (Baseline)
- **Purpose:** PyTorch reference implementation
- **Config:** Standard PyTorch inference
- **Use when:** Comparing against TensorRT speedup
- **Example:** Development, debugging

---

## 📞 Support

**Files location:**
```
/Users/deepsoni/Oracle Content - Accounts/Oracle Content/Projects/CoE_initial/CoE_base/000-AICoE-Knowledgebase/001-customers/2025-lab/YOLO-NIM/simplest/benchmarking/
```

**Related documentation:**
- Deployment review: `/simplest/codes/DEPLOYMENT_REVIEW.txt`
- gRPC benchmarking: `/simplest/gRPC/BENCHMARK_README.md`

---

## ✅ Checklist Before Running

- [ ] All 4 pods are Running (check: `kubectl get pods -A | grep yolo`)
- [ ] Port forwarding script is executable (`chmod +x setup_port_forwarding.sh`)
- [ ] Port forwarding is running in separate terminal
- [ ] kubectl access to cluster
- [ ] Python 3 available (`python3 --version`)

---

**Created:** 2026-01-01
**Purpose:** Comprehensive benchmarking suite for YOLO NIM deployments
**Author:** Benchmarking Expert Analysis
