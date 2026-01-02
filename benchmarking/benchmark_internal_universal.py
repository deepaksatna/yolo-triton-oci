#!/usr/bin/env python3
"""
Universal Internal Benchmark - Works for HTTP and gRPC
Runs INSIDE the pod to measure true inference latency
Supports both sequential and concurrent (load) benchmarking

Usage:
  python3 benchmark_internal_universal.py [iterations] [protocol] [concurrency]

  iterations: number of requests (default: 50)
  protocol: 'http' or 'grpc' (default: auto-detect)
  concurrency: number of concurrent workers (default: 1 for sequential, 8+ for load testing)
"""

import sys
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try imports
try:
    import numpy as np
except ImportError:
    print("ERROR: numpy not available")
    sys.exit(1)

# Configuration
TRITON_HTTP_URL = "127.0.0.1:8000"
TRITON_GRPC_URL = "127.0.0.1:8001"
MODEL_NAME = "yolov8s"
MODEL_VERSION = "1"

def benchmark_http(iterations=50):
    """Benchmark using HTTP protocol"""
    try:
        from urllib.request import Request, urlopen
        import json as json_module
    except ImportError:
        return None

    print(f"\n{'='*70}")
    print(f"Internal HTTP Benchmark (Inside Pod)")
    print(f"{'='*70}\n")

    print(f"Configuration:")
    print(f"  URL: {TRITON_HTTP_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Iterations: {iterations}\n")

    # Check health
    try:
        health_url = f"http://{TRITON_HTTP_URL}/v2/health/ready"
        req = Request(health_url)
        with urlopen(req, timeout=5) as response:
            _ = response.read()
        print(f"✓ Server ready\n")
    except Exception as e:
        print(f"✗ Server not ready: {e}")
        return None

    # Prepare input
    input_data = np.random.rand(1, 3, 640, 640).astype(np.float32)
    request_data = {
        "inputs": [{
            "name": "images",
            "shape": [1, 3, 640, 640],
            "datatype": "FP32",
            "data": input_data.flatten().tolist()
        }]
    }

    url = f"http://{TRITON_HTTP_URL}/v2/models/{MODEL_NAME}/infer"

    # Warmup
    print("Warming up (10 iterations)...")
    for _ in range(10):
        try:
            req = Request(url)
            req.add_header('Content-Type', 'application/json')
            data = json_module.dumps(request_data).encode('utf-8')
            with urlopen(req, data=data, timeout=30) as response:
                _ = response.read()
        except Exception as e:
            print(f"Warmup failed: {e}")
            return None
    print()

    # Benchmark
    print(f"Running benchmark ({iterations} iterations)...\n")
    latencies = []
    errors = 0

    for i in range(iterations):
        try:
            req = Request(url)
            req.add_header('Content-Type', 'application/json')
            data = json_module.dumps(request_data).encode('utf-8')

            start = time.perf_counter()
            with urlopen(req, data=data, timeout=30) as response:
                _ = response.read()
            end = time.perf_counter()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

            if (i + 1) % 10 == 0:
                avg = sum(latencies) / len(latencies)
                print(f"  Progress: {i+1}/{iterations} - Avg: {avg:.2f} ms")
        except Exception as e:
            errors += 1
            if errors == 1:
                print(f"  Error: {e}")

    if not latencies:
        return None

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    results = {
        'protocol': 'http',
        'mode': 'sequential',
        'location': 'internal',
        'iterations': len(latencies),
        'errors': errors,
        'latency_ms': {
            'min': min(latencies),
            'max': max(latencies),
            'mean': sum(latencies) / len(latencies),
            'median': latencies_sorted[len(latencies) // 2],
            'p50': latencies_sorted[int(len(latencies) * 0.50)],
            'p90': latencies_sorted[int(len(latencies) * 0.90)],
            'p95': latencies_sorted[int(len(latencies) * 0.95)],
            'p99': latencies_sorted[int(len(latencies) * 0.99)],
        },
        'throughput_fps': 1000 / (sum(latencies) / len(latencies))
    }

    return results

def benchmark_grpc(iterations=50):
    """Benchmark using gRPC protocol (sequential)"""
    try:
        import tritonclient.grpc as grpcclient
    except ImportError:
        print("✗ tritonclient.grpc not available")
        return None

    print(f"\n{'='*70}")
    print(f"Internal gRPC Benchmark (Sequential, Inside Pod)")
    print(f"{'='*70}\n")

    print(f"Configuration:")
    print(f"  URL: {TRITON_GRPC_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Iterations: {iterations}\n")

    # Create client
    try:
        client = grpcclient.InferenceServerClient(url=TRITON_GRPC_URL, verbose=False)
        print(f"✓ Connected to Triton")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return None

    # Check health
    try:
        if client.is_server_ready() and client.is_model_ready(MODEL_NAME):
            print(f"✓ Server and model ready\n")
        else:
            print(f"✗ Server or model not ready")
            return None
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return None

    # Prepare input
    input_data = np.random.rand(1, 3, 640, 640).astype(np.float32)
    inputs = [grpcclient.InferInput("images", input_data.shape, "FP32")]
    inputs[0].set_data_from_numpy(input_data)
    outputs = [grpcclient.InferRequestedOutput("output0")]

    # Warmup
    print("Warming up (10 iterations)...")
    for _ in range(10):
        client.infer(MODEL_NAME, inputs, model_version=MODEL_VERSION, outputs=outputs)
    print()

    # Benchmark
    print(f"Running benchmark ({iterations} iterations)...\n")
    latencies = []

    for i in range(iterations):
        start = time.perf_counter()
        response = client.infer(MODEL_NAME, inputs, model_version=MODEL_VERSION, outputs=outputs)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

        if (i + 1) % 10 == 0:
            avg = sum(latencies) / len(latencies)
            print(f"  Progress: {i+1}/{iterations} - Avg: {avg:.2f} ms")

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    results = {
        'protocol': 'grpc',
        'mode': 'sequential',
        'location': 'internal',
        'iterations': len(latencies),
        'latency_ms': {
            'min': min(latencies),
            'max': max(latencies),
            'mean': sum(latencies) / len(latencies),
            'median': latencies_sorted[len(latencies) // 2],
            'p50': latencies_sorted[int(len(latencies) * 0.50)],
            'p90': latencies_sorted[int(len(latencies) * 0.90)],
            'p95': latencies_sorted[int(len(latencies) * 0.95)],
            'p99': latencies_sorted[int(len(latencies) * 0.99)],
        },
        'throughput_fps': 1000 / (sum(latencies) / len(latencies))
    }

    return results

def benchmark_grpc_concurrent(iterations=50, concurrency=8):
    """Benchmark using gRPC protocol with concurrency (load testing)"""
    try:
        import tritonclient.grpc as grpcclient
    except ImportError:
        print("✗ tritonclient.grpc not available")
        return None

    print(f"\n{'='*70}")
    print(f"Internal gRPC Benchmark (Concurrent, Inside Pod)")
    print(f"{'='*70}\n")

    print(f"Configuration:")
    print(f"  URL: {TRITON_GRPC_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Total Requests: {iterations}")
    print(f"  Concurrency: {concurrency} workers\n")

    # Create client for health check
    try:
        client = grpcclient.InferenceServerClient(url=TRITON_GRPC_URL, verbose=False)
        print(f"✓ Connected to Triton")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return None

    # Check health
    try:
        if client.is_server_ready() and client.is_model_ready(MODEL_NAME):
            print(f"✓ Server and model ready\n")
        else:
            print(f"✗ Server or model not ready")
            return None
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return None

    # Prepare input once (reused by all workers)
    input_data = np.random.rand(1, 3, 640, 640).astype(np.float32)

    # Warmup (single-thread warmup, reduced for high concurrency)
    warmup_iterations = min(10, max(5, iterations // 20))  # Scale warmup with test size
    print(f"Warming up ({warmup_iterations} iterations)...")
    inputs = [grpcclient.InferInput("images", input_data.shape, "FP32")]
    inputs[0].set_data_from_numpy(input_data)
    outputs = [grpcclient.InferRequestedOutput("output0")]

    warmup_success = 0
    for i in range(warmup_iterations):
        try:
            client.infer(MODEL_NAME, inputs, model_version=MODEL_VERSION, outputs=outputs)
            warmup_success += 1
        except Exception as e:
            if i == 0:  # Only print first error
                print(f"  Warning: Warmup request {i+1} failed: {e}")

    if warmup_success == 0:
        print(f"✗ All warmup requests failed")
        return None

    print(f"  Warmup complete ({warmup_success}/{warmup_iterations} successful)\n")

    # Worker function: each worker creates its own client + inputs (thread-safe)
    def one_request():
        try:
            c = grpcclient.InferenceServerClient(url=TRITON_GRPC_URL, verbose=False)
            inp = [grpcclient.InferInput("images", input_data.shape, "FP32")]
            inp[0].set_data_from_numpy(input_data)
            out = [grpcclient.InferRequestedOutput("output0")]

            start = time.perf_counter()
            c.infer(MODEL_NAME, inp, model_version=MODEL_VERSION, outputs=out)
            end = time.perf_counter()
            return (end - start) * 1000.0
        except Exception as e:
            # Re-raise to be caught by executor
            raise Exception(f"Inference failed: {str(e)[:100]}")

    latencies = []
    errors = 0

    print(f"Running concurrent benchmark ({iterations} requests, {concurrency} workers)...\n")

    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(one_request) for _ in range(iterations)]
        for i, f in enumerate(as_completed(futures), 1):
            try:
                latencies.append(f.result())
            except Exception as e:
                errors += 1
                if errors == 1:
                    print(f"  Error: {e}")

            if i % max(1, iterations // 10) == 0:
                avg = sum(latencies) / len(latencies) if latencies else 0
                print(f"  Progress: {i}/{iterations} - Avg: {avg:.2f} ms - Errors: {errors}")

    end_time = time.perf_counter()
    total_time = end_time - start_time

    if not latencies:
        return None

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    mean = sum(latencies) / len(latencies)

    results = {
        'protocol': 'grpc',
        'mode': 'concurrent',
        'location': 'internal',
        'iterations': len(latencies),
        'errors': errors,
        'concurrency': concurrency,
        'total_time_sec': total_time,
        'latency_ms': {
            'min': min(latencies),
            'max': max(latencies),
            'mean': mean,
            'median': latencies_sorted[len(latencies_sorted) // 2],
            'p50': latencies_sorted[int(len(latencies_sorted) * 0.50)],
            'p90': latencies_sorted[int(len(latencies_sorted) * 0.90)],
            'p95': latencies_sorted[int(len(latencies_sorted) * 0.95)],
            'p99': latencies_sorted[int(len(latencies_sorted) * 0.99)],
        },
        # Throughput = total requests / total time (actual throughput under load)
        'throughput_fps': len(latencies) / total_time,
        # Also include per-request average
        'avg_latency_fps': 1000.0 / mean
    }

    return results

def benchmark_http_concurrent(iterations=50, concurrency=8):
    """Benchmark using HTTP protocol with concurrency (load testing)"""
    try:
        from urllib.request import Request, urlopen
        import json as json_module
    except ImportError:
        return None

    print(f"\n{'='*70}")
    print(f"Internal HTTP Benchmark (Concurrent, Inside Pod)")
    print(f"{'='*70}\n")

    print(f"Configuration:")
    print(f"  URL: {TRITON_HTTP_URL}")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Total Requests: {iterations}")
    print(f"  Concurrency: {concurrency} workers\n")

    # Check health
    try:
        health_url = f"http://{TRITON_HTTP_URL}/v2/health/ready"
        req = Request(health_url)
        with urlopen(req, timeout=5) as response:
            _ = response.read()
        print(f"✓ Server ready\n")
    except Exception as e:
        print(f"✗ Server not ready: {e}")
        return None

    # Prepare input once (reused by all workers)
    input_data = np.random.rand(1, 3, 640, 640).astype(np.float32)
    request_data = {
        "inputs": [{
            "name": "images",
            "shape": [1, 3, 640, 640],
            "datatype": "FP32",
            "data": input_data.flatten().tolist()
        }]
    }

    url = f"http://{TRITON_HTTP_URL}/v2/models/{MODEL_NAME}/infer"

    # Warmup (reduced for high concurrency)
    warmup_iterations = min(10, max(5, iterations // 20))  # Scale warmup with test size
    print(f"Warming up ({warmup_iterations} iterations)...")

    warmup_success = 0
    for i in range(warmup_iterations):
        try:
            req = Request(url)
            req.add_header('Content-Type', 'application/json')
            data = json_module.dumps(request_data).encode('utf-8')
            with urlopen(req, data=data, timeout=30) as response:
                _ = response.read()
            warmup_success += 1
        except Exception as e:
            if i == 0:  # Only print first error
                print(f"  Warning: Warmup request {i+1} failed: {e}")

    if warmup_success == 0:
        print(f"✗ All warmup requests failed")
        return None

    print(f"  Warmup complete ({warmup_success}/{warmup_iterations} successful)\n")

    # Worker function
    def one_request():
        try:
            req = Request(url)
            req.add_header('Content-Type', 'application/json')
            data = json_module.dumps(request_data).encode('utf-8')

            start = time.perf_counter()
            with urlopen(req, data=data, timeout=60) as response:  # Increased timeout for high concurrency
                _ = response.read()
            end = time.perf_counter()
            return (end - start) * 1000.0
        except Exception as e:
            # Re-raise to be caught by executor
            raise Exception(f"HTTP request failed: {str(e)[:100]}")

    latencies = []
    errors = 0

    print(f"Running concurrent benchmark ({iterations} requests, {concurrency} workers)...\n")

    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(one_request) for _ in range(iterations)]
        for i, f in enumerate(as_completed(futures), 1):
            try:
                latencies.append(f.result())
            except Exception as e:
                errors += 1
                if errors == 1:
                    print(f"  Error: {e}")

            if i % max(1, iterations // 10) == 0:
                avg = sum(latencies) / len(latencies) if latencies else 0
                print(f"  Progress: {i}/{iterations} - Avg: {avg:.2f} ms - Errors: {errors}")

    end_time = time.perf_counter()
    total_time = end_time - start_time

    if not latencies:
        return None

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    mean = sum(latencies) / len(latencies)

    results = {
        'protocol': 'http',
        'mode': 'concurrent',
        'location': 'internal',
        'iterations': len(latencies),
        'errors': errors,
        'concurrency': concurrency,
        'total_time_sec': total_time,
        'latency_ms': {
            'min': min(latencies),
            'max': max(latencies),
            'mean': mean,
            'median': latencies_sorted[len(latencies_sorted) // 2],
            'p50': latencies_sorted[int(len(latencies_sorted) * 0.50)],
            'p90': latencies_sorted[int(len(latencies_sorted) * 0.90)],
            'p95': latencies_sorted[int(len(latencies_sorted) * 0.95)],
            'p99': latencies_sorted[int(len(latencies_sorted) * 0.99)],
        },
        # Throughput = total requests / total time (actual throughput under load)
        'throughput_fps': len(latencies) / total_time,
        # Also include per-request average
        'avg_latency_fps': 1000.0 / mean
    }

    return results

def print_results(results):
    """Print benchmark results"""
    if not results:
        print("No results to display")
        return

    print(f"\n{'='*70}")
    print(f"Results")
    print(f"{'='*70}\n")

    print(f"Protocol: {results['protocol'].upper()}")
    print(f"Mode: {results.get('mode', 'sequential').upper()}")
    print(f"Location: {results['location']}")
    print(f"Iterations: {results['iterations']}")
    if 'concurrency' in results:
        print(f"Concurrency: {results['concurrency']} workers")
    if 'errors' in results and results['errors'] > 0:
        print(f"Errors: {results['errors']}")
    if 'total_time_sec' in results:
        print(f"Total Time: {results['total_time_sec']:.2f} sec")
    print()

    print(f"Latency (ms):")
    print(f"  Min:     {results['latency_ms']['min']:7.2f} ms")
    print(f"  Max:     {results['latency_ms']['max']:7.2f} ms")
    print(f"  Mean:    {results['latency_ms']['mean']:7.2f} ms")
    print(f"  Median:  {results['latency_ms']['median']:7.2f} ms")
    print(f"  P50:     {results['latency_ms']['p50']:7.2f} ms")
    print(f"  P90:     {results['latency_ms']['p90']:7.2f} ms")
    print(f"  P95:     {results['latency_ms']['p95']:7.2f} ms")
    print(f"  P99:     {results['latency_ms']['p99']:7.2f} ms")
    print()

    print(f"Throughput:")
    print(f"  FPS:     {results['throughput_fps']:7.2f}")
    if 'avg_latency_fps' in results:
        print(f"  Avg FPS (from latency): {results['avg_latency_fps']:7.2f}")
    print()

def save_results(results):
    """Save results to JSON file"""
    try:
        results_dir = Path("/tmp/debug")
        results_dir.mkdir(parents=True, exist_ok=True)
        results_file = results_dir / "benchmark_results.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✓ Results saved to: {results_file}")
    except Exception as e:
        print(f"⚠ Could not save results: {e}")

def auto_detect_protocol():
    """Auto-detect available protocol"""
    # Check gRPC
    try:
        import tritonclient.grpc as grpcclient
        client = grpcclient.InferenceServerClient(url=TRITON_GRPC_URL, verbose=False)
        if client.is_server_ready():
            return 'grpc'
    except:
        pass

    # Check HTTP
    try:
        from urllib.request import Request, urlopen
        health_url = f"http://{TRITON_HTTP_URL}/v2/health/ready"
        req = Request(health_url)
        with urlopen(req, timeout=5) as response:
            _ = response.read()
        return 'http'
    except:
        pass

    return None

if __name__ == '__main__':
    # Get parameters
    iterations = 50
    protocol = 'auto'
    concurrency = 1  # Default: sequential (1 worker)

    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
        except ValueError:
            print(f"Invalid iterations: {sys.argv[1]}, using default: 50")

    if len(sys.argv) > 2:
        protocol = sys.argv[2].lower()

    if len(sys.argv) > 3:
        try:
            concurrency = int(sys.argv[3])
            if concurrency < 1:
                print(f"Invalid concurrency: {concurrency}, using default: 1")
                concurrency = 1
        except ValueError:
            print(f"Invalid concurrency: {sys.argv[3]}, using default: 1")

    # Auto-detect if needed
    if protocol == 'auto':
        protocol = auto_detect_protocol()
        if not protocol:
            print("ERROR: Could not detect any available protocol")
            sys.exit(1)
        print(f"Auto-detected protocol: {protocol.upper()}\n")

    # Determine mode
    mode = 'concurrent' if concurrency > 1 else 'sequential'
    print(f"Benchmark mode: {mode.upper()}")
    if concurrency > 1:
        print(f"Concurrency: {concurrency} workers")
        if concurrency > 50:
            print(f"⚠ WARNING: Very high concurrency ({concurrency} workers)")
            print(f"  This may cause timeouts or resource exhaustion")
            print(f"  Recommended: Start with 8-16 workers and increase gradually")
        print()
    else:
        print(f"Sequential mode (1 request at a time)\n")

    # Run benchmark
    if protocol == 'grpc':
        if concurrency > 1:
            results = benchmark_grpc_concurrent(iterations, concurrency)
        else:
            results = benchmark_grpc(iterations)
    elif protocol == 'http':
        if concurrency > 1:
            results = benchmark_http_concurrent(iterations, concurrency)
        else:
            results = benchmark_http(iterations)
    else:
        print(f"ERROR: Unknown protocol: {protocol}")
        print("Use 'http' or 'grpc'")
        sys.exit(1)

    # Print and save results
    if results:
        print_results(results)
        save_results(results)
        print(f"\n{'='*70}\n")
        sys.exit(0)
    else:
        print(f"\nBenchmark failed\n")
        sys.exit(1)
