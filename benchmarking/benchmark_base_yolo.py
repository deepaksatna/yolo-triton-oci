#!/usr/bin/env python3
"""
Base YOLO PyTorch Benchmark Script
Runs inside base-yolo pod to measure baseline PyTorch performance

Usage:
  python3 benchmark_base_yolo.py [iterations]
"""

import sys
import json
import time

def benchmark_base_yolo(iterations=50):
    """Benchmark base-yolo using its built-in /benchmark endpoint"""
    try:
        from urllib.request import Request, urlopen
    except ImportError:
        print("ERROR: urllib not available")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"Base YOLO PyTorch Benchmark (Inside Pod)")
    print(f"{'='*70}\n")

    print(f"Configuration:")
    print(f"  URL: http://127.0.0.1:8080/benchmark")
    print(f"  Iterations: {iterations}")
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

    # Run benchmark using built-in endpoint
    try:
        url = f"http://127.0.0.1:8080/benchmark?iterations={iterations}"
        req = Request(url, method='POST')
        req.add_header('Content-Type', 'application/json')

        print(f"Running PyTorch benchmark...")
        print(f"(includes 10 warmup iterations)\n")

        start = time.time()
        with urlopen(req, timeout=300) as response:  # 5 min timeout for large iterations
            result = json.loads(response.read())
        end = time.time()

        print(f"Benchmark completed in {end - start:.2f} seconds\n")

        # Print results
        print(f"{'='*70}")
        print(f"Results")
        print(f"{'='*70}\n")

        print(f"Protocol: HTTP")
        print(f"Location: internal")
        print(f"Framework: PyTorch (Ultralytics)")
        print(f"Iterations: {result['iterations']}\n")

        lat = result['latency_ms']
        print(f"Latency (ms):")
        print(f"  Min:     {lat['min']:7.2f} ms")
        print(f"  Max:     {lat['max']:7.2f} ms")
        print(f"  Mean:    {lat['mean']:7.2f} ms")
        print(f"  P95:     {lat['p95']:7.2f} ms")
        print()

        print(f"Throughput:")
        print(f"  FPS:     {result['fps']:7.2f}")
        print()

        # Format for compatibility with universal benchmark
        formatted_result = {
            'protocol': 'http',
            'location': 'internal',
            'framework': 'pytorch',
            'deployment': 'base-pytorch',
            'iterations': result['iterations'],
            'latency_ms': {
                'min': lat['min'],
                'max': lat['max'],
                'mean': lat['mean'],
                'median': lat['mean'],  # Not provided by base-yolo, use mean
                'p50': lat['mean'],
                'p90': lat['p95'],  # Not provided, use p95
                'p95': lat['p95'],
                'p99': lat['p95'],  # Not provided, use p95
            },
            'throughput_fps': result['fps']
        }

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

    except Exception as e:
        print(f"✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    iterations = 50
    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
        except ValueError:
            print(f"Invalid iterations: {sys.argv[1]}, using default: 50")

    result = benchmark_base_yolo(iterations)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)
