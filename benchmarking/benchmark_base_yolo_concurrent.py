#!/usr/bin/env python3
"""
Base YOLO PyTorch Concurrent Benchmark Script
Tests PyTorch performance under concurrent load using /infer endpoint

Usage:
  python3 benchmark_base_yolo_concurrent.py [iterations] [concurrency]

  iterations: total number of requests (default: 50)
  concurrency: number of concurrent workers (default: 1 for sequential, 8+ for load testing)
"""

import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def benchmark_base_yolo_concurrent(iterations=50, concurrency=1):
    """Benchmark base-yolo using concurrent calls to /infer endpoint"""
    try:
        from urllib.request import Request, urlopen
    except ImportError:
        print("ERROR: urllib not available")
        sys.exit(1)

    mode = "Sequential" if concurrency == 1 else "Concurrent"
    print(f"\n{'='*70}")
    print(f"Base YOLO PyTorch Benchmark ({mode}, Inside Pod)")
    print(f"{'='*70}\n")

    print(f"Configuration:")
    print(f"  URL: http://127.0.0.1:8080/infer")
    print(f"  Total Requests: {iterations}")
    print(f"  Concurrency: {concurrency} worker{'s' if concurrency > 1 else ''}")
    print(f"  Framework: PyTorch + Ultralytics YOLO\n")

    # Check health first
    try:
        health_url = "http://127.0.0.1:8080/health"
        req = Request(health_url)
        with urlopen(req, timeout=5) as response:
            health = json.loads(response.read())
        print(f"✓ Server ready: {health.get('status')}")
        print(f"  Deployment: {health.get('deployment')}\n")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return None

    # Prepare request payload (use random image - server will generate if empty)
    request_data = json.dumps({}).encode('utf-8')

    # Worker function for concurrent execution
    def one_request():
        url = "http://127.0.0.1:8080/infer"
        req = Request(url, method='POST')
        req.add_header('Content-Type', 'application/json')

        start = time.perf_counter()
        with urlopen(req, data=request_data, timeout=30) as response:
            result = json.loads(response.read())
        end = time.perf_counter()

        return (end - start) * 1000.0  # Return latency in ms

    # Warmup
    print(f"Warming up (20 iterations)...")
    for _ in range(20):
        try:
            one_request()
        except Exception as e:
            print(f"Warmup failed: {e}")
            return None
    print()

    latencies = []
    errors = 0

    if concurrency == 1:
        # Sequential mode
        print(f"Running sequential benchmark ({iterations} iterations)...\n")
        for i in range(iterations):
            try:
                latencies.append(one_request())

                if (i + 1) % 10 == 0:
                    avg = sum(latencies) / len(latencies)
                    print(f"  Progress: {i+1}/{iterations} - Avg: {avg:.2f} ms")
            except Exception as e:
                errors += 1
                if errors == 1:
                    print(f"  Error: {e}")

        total_time = sum(latencies) / 1000.0  # Approximate

    else:
        # Concurrent mode
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
        print(f"✗ All requests failed")
        return None

    print(f"\nBenchmark completed in {total_time:.2f} seconds\n")

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    mean = sum(latencies) / len(latencies)

    print(f"{'='*70}")
    print(f"Results")
    print(f"{'='*70}\n")

    print(f"Protocol: HTTP")
    print(f"Mode: {'sequential' if concurrency == 1 else 'concurrent'}")
    print(f"Location: internal")
    print(f"Framework: PyTorch (Ultralytics)")
    print(f"Iterations: {len(latencies)}")
    if concurrency > 1:
        print(f"Concurrency: {concurrency} workers")
    if errors > 0:
        print(f"Errors: {errors}")
    if concurrency > 1:
        print(f"Total Time: {total_time:.2f} sec")
    print()

    lat_stats = {
        'min': min(latencies),
        'max': max(latencies),
        'mean': mean,
        'median': latencies_sorted[len(latencies_sorted) // 2],
        'p50': latencies_sorted[int(len(latencies_sorted) * 0.50)],
        'p90': latencies_sorted[int(len(latencies_sorted) * 0.90)],
        'p95': latencies_sorted[int(len(latencies_sorted) * 0.95)],
        'p99': latencies_sorted[int(len(latencies_sorted) * 0.99)],
    }

    print(f"Latency (ms):")
    print(f"  Min:     {lat_stats['min']:7.2f} ms")
    print(f"  Max:     {lat_stats['max']:7.2f} ms")
    print(f"  Mean:    {lat_stats['mean']:7.2f} ms")
    print(f"  Median:  {lat_stats['median']:7.2f} ms")
    print(f"  P50:     {lat_stats['p50']:7.2f} ms")
    print(f"  P90:     {lat_stats['p90']:7.2f} ms")
    print(f"  P95:     {lat_stats['p95']:7.2f} ms")
    print(f"  P99:     {lat_stats['p99']:7.2f} ms")
    print()

    print(f"Throughput:")
    if concurrency > 1:
        actual_fps = len(latencies) / total_time
        theoretical_fps = 1000.0 / mean
        print(f"  FPS:     {actual_fps:7.2f} (actual throughput)")
        print(f"  Avg FPS (from latency): {theoretical_fps:7.2f}")
    else:
        fps = 1000.0 / mean
        print(f"  FPS:     {fps:7.2f}")
    print()

    # Format for compatibility with universal benchmark
    formatted_result = {
        'protocol': 'http',
        'mode': 'sequential' if concurrency == 1 else 'concurrent',
        'location': 'internal',
        'framework': 'pytorch',
        'deployment': 'base-pytorch',
        'iterations': len(latencies),
        'latency_ms': lat_stats,
        'throughput_fps': len(latencies) / total_time if concurrency > 1 else 1000.0 / mean
    }

    # Add concurrent-specific fields
    if concurrency > 1:
        formatted_result['concurrency'] = concurrency
        formatted_result['errors'] = errors
        formatted_result['total_time_sec'] = total_time
        formatted_result['avg_latency_fps'] = 1000.0 / mean

    # Save results
    try:
        import os
        os.makedirs('/tmp/debug', exist_ok=True)
        with open('/tmp/debug/benchmark_results.json', 'w') as f:
            json.dump(formatted_result, f, indent=2)
        print(f"✓ Results saved to: /tmp/debug/benchmark_results.json")
    except Exception as e:
        print(f"⚠ Could not save results: {e}")

    print(f"\n{'='*70}\n")

    return formatted_result

if __name__ == '__main__':
    iterations = 50
    concurrency = 1

    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
        except ValueError:
            print(f"Invalid iterations: {sys.argv[1]}, using default: 50")

    if len(sys.argv) > 2:
        try:
            concurrency = int(sys.argv[2])
            if concurrency < 1:
                print(f"Invalid concurrency: {concurrency}, using default: 1")
                concurrency = 1
        except ValueError:
            print(f"Invalid concurrency: {sys.argv[2]}, using default: 1")

    result = benchmark_base_yolo_concurrent(iterations, concurrency)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)
