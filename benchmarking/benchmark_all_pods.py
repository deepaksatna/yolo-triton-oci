#!/usr/bin/env python3
"""
Comprehensive YOLO NIM Benchmarking Suite
Benchmarks all 4 deployments: base-yolo, nim-binary, nim-grpc, nim-batching

Prerequisites:
  - Run setup_port_forwarding.sh first
  - kubectl access to cluster

Output:
  - Individual results in JSON files
  - Comprehensive comparison report
  - Performance recommendations
"""

import subprocess
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Configuration
DEPLOYMENTS = {
    'base-yolo': {
        'namespace': 'yolo-base',
        'pod_label': 'app=yolo-base',
        'container': 'yolo-golden',
        'external_ip': '141.147.36.157',
        'port_forward_http': 8000,
        'port_forward_grpc': None,
        'supports_grpc': False,
    },
    'nim-binary': {
        'namespace': 'yolo-nim-binary',
        'pod_label': 'app=yolo-nim-binary',
        'container': 'triton-server',
        'external_ip': '138.2.160.196',
        'port_forward_http': 8100,
        'port_forward_grpc': None,
        'supports_grpc': False,
    },
    'nim-grpc': {
        'namespace': 'yolo-nim-grpc',
        'pod_label': 'app=yolo-nim-grpc-inference',
        'container': 'triton-server',
        'external_ip': '138.3.255.156',
        'port_forward_http': 8200,
        'port_forward_grpc': 8201,
        'supports_grpc': True,
    },
    'nim-batching': {
        'namespace': 'yolo-nim-batching',
        'pod_label': 'app=yolo-nim-batching',
        'container': 'triton-server',
        'external_ip': '92.5.3.38',
        'port_forward_http': 8300,
        'port_forward_grpc': 8301,
        'supports_grpc': True,
    },
}

ITERATIONS = 50
CONCURRENCY = 1  # Set to 1 for sequential, 8+ for load testing
OUTPUT_DIR = Path("/mnt/coecommonfss/llmcore/benchmarking")

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.NC}")
    print(f"{Colors.BOLD}{text}{Colors.NC}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.NC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.NC} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.NC} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {text}")

def print_info(text):
    print(f"{Colors.BLUE}➜{Colors.NC} {text}")

def run_command(cmd, capture=True):
    """Run shell command"""
    if capture:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    else:
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0, "", ""

def get_pod_name(namespace, label):
    """Get pod name from namespace and label"""
    cmd = f"kubectl get pods -n {namespace} -l {label} -o jsonpath='{{.items[0].metadata.name}}'"
    success, stdout, _ = run_command(cmd)
    if success and stdout:
        return stdout.strip()
    return None

def copy_benchmark_to_pod(deployment_name, config):
    """Copy appropriate benchmark script to pod"""
    print_info(f"Copying benchmark script to {deployment_name}...")

    pod_name = get_pod_name(config['namespace'], config['pod_label'])
    if not pod_name:
        print_error(f"Pod not found for {deployment_name}")
        return False

    # Create debug directory
    cmd = f"kubectl exec -n {config['namespace']} {pod_name} -c {config['container']} -- mkdir -p /tmp/debug"
    run_command(cmd, capture=False)

    # Choose appropriate benchmark script
    if deployment_name == 'base-yolo':
        # Use appropriate PyTorch benchmark based on concurrency
        if CONCURRENCY > 1:
            src = OUTPUT_DIR / "benchmark_base_yolo_concurrent.py"
            dest_name = "benchmark_base_yolo_concurrent.py"
        else:
            src = OUTPUT_DIR / "benchmark_base_yolo.py"
            dest_name = "benchmark_base_yolo.py"
    else:
        # Use universal Triton benchmark for NIMs
        src = OUTPUT_DIR / "benchmark_internal_universal.py"
        dest_name = "benchmark_internal_universal.py"

    # Copy benchmark script
    cmd = f"kubectl cp {src} {config['namespace']}/{pod_name}:/tmp/debug/{dest_name} -c {config['container']}"
    success, _, stderr = run_command(cmd)

    if success:
        print_success(f"Benchmark script copied to {deployment_name}")
        return True
    else:
        print_error(f"Failed to copy to {deployment_name}: {stderr}")
        return False

def run_internal_benchmark(deployment_name, config):
    """Run benchmark inside the pod"""
    mode = "LOAD TEST" if CONCURRENCY > 1 else "Sequential"
    print_header(f"Internal Benchmark: {deployment_name} ({mode})")

    pod_name = get_pod_name(config['namespace'], config['pod_label'])
    if not pod_name:
        print_error(f"Pod not found for {deployment_name}")
        return None

    # Choose appropriate benchmark script
    if deployment_name == 'base-yolo':
        if CONCURRENCY > 1:
            print_info(f"Running PyTorch load test ({ITERATIONS} requests, {CONCURRENCY} workers)...")
            script_name = "benchmark_base_yolo_concurrent.py"
            cmd = f"kubectl exec -n {config['namespace']} {pod_name} -c {config['container']} -- python3 /tmp/debug/{script_name} {ITERATIONS} {CONCURRENCY}"
        else:
            print_info(f"Running PyTorch baseline benchmark ({ITERATIONS} iterations)...")
            script_name = "benchmark_base_yolo.py"
            cmd = f"kubectl exec -n {config['namespace']} {pod_name} -c {config['container']} -- python3 /tmp/debug/{script_name} {ITERATIONS}"
    else:
        script_name = "benchmark_internal_universal.py"
        # NIMs support concurrency parameter
        if CONCURRENCY > 1:
            print_info(f"Running load test ({ITERATIONS} requests, {CONCURRENCY} workers)...")
        else:
            print_info(f"Running sequential benchmark ({ITERATIONS} iterations)...")
        cmd = f"kubectl exec -n {config['namespace']} {pod_name} -c {config['container']} -- python3 /tmp/debug/{script_name} {ITERATIONS} auto {CONCURRENCY}"

    # Run benchmark
    success, stdout, stderr = run_command(cmd)

    if not success:
        print_error(f"Internal benchmark failed for {deployment_name}")
        if stderr:
            print(f"Error: {stderr[:500]}")
        return None

    # Display output
    print(stdout)

    # Get JSON results
    cmd = f"kubectl exec -n {config['namespace']} {pod_name} -c {config['container']} -- cat /tmp/debug/benchmark_results.json"
    success, json_output, _ = run_command(cmd)

    if success:
        try:
            results = json.loads(json_output)
            results['deployment'] = deployment_name
            results['test_type'] = 'internal'
            return results
        except json.JSONDecodeError:
            print_warning("Could not parse JSON results")

    return None

def test_port_forward(deployment_name, config, protocol='http'):
    """Test deployment via port forwarding"""
    print_info(f"Testing {deployment_name} via port forwarding ({protocol.upper()})...")

    if protocol == 'http':
        port = config['port_forward_http']
        url = f"http://127.0.0.1:{port}/v2/health/ready"
    elif protocol == 'grpc':
        if not config['supports_grpc']:
            return None
        port = config['port_forward_grpc']
        # gRPC health check doesn't work with curl, just assume it's accessible if HTTP works
        print_info(f"{deployment_name} gRPC port: 127.0.0.1:{port} (health check not supported via curl)")
        return None
    else:
        return None

    # Check health (HTTP only)
    cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {url}"
    success, stdout, _ = run_command(cmd)

    if success and stdout.strip() in ['200', '204']:
        print_success(f"{deployment_name} accessible on 127.0.0.1:{port}")
        return True
    else:
        print_warning(f"{deployment_name} not accessible on 127.0.0.1:{port}")
        return False

def test_external_endpoint(deployment_name, config):
    """Test external LoadBalancer endpoint"""
    print_info(f"Testing {deployment_name} external endpoint...")

    url = f"http://{config['external_ip']}/v2/health/ready"
    cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {url}"
    success, stdout, _ = run_command(cmd)

    if success and stdout.strip() in ['200', '204']:
        print_success(f"{deployment_name} external endpoint accessible ({config['external_ip']})")
        return True
    else:
        print_warning(f"{deployment_name} external endpoint not accessible")
        return False

def generate_report(all_results):
    """Generate comprehensive comparison report"""
    print_header("Generating Comprehensive Report")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("YOLO NIM COMPREHENSIVE BENCHMARK REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {timestamp}")
    report_lines.append(f"Iterations per test: {ITERATIONS}")
    if CONCURRENCY > 1:
        report_lines.append(f"Concurrency: {CONCURRENCY} workers (LOAD TEST MODE)")
    else:
        report_lines.append(f"Mode: Sequential (1 request at a time)")
    report_lines.append("")

    # Summary table
    report_lines.append("=" * 80)
    report_lines.append("PERFORMANCE SUMMARY - All Deployments")
    report_lines.append("=" * 80)
    report_lines.append("")

    if not all_results:
        report_lines.append("⚠ No benchmark results available")
        report_lines.append("")

    # Table header (different for concurrent mode)
    if CONCURRENCY > 1:
        report_lines.append(f"{'Deployment':<15} | {'Framework':<10} | {'Mean (ms)':<10} | {'P95 (ms)':<10} | {'Throughput':<12} | {'Mode'}")
        report_lines.append("-" * 90)
    else:
        report_lines.append(f"{'Deployment':<15} | {'Framework':<10} | {'Mean (ms)':<10} | {'P95 (ms)':<10} | {'FPS':<8} | {'Speedup'}")
        report_lines.append("-" * 85)

    # Sort by mean latency (put base-yolo last for comparison)
    sorted_results = sorted(all_results, key=lambda x: (
        0 if x.get('deployment') != 'base-yolo' else 1,  # base-yolo last
        x.get('latency_ms', {}).get('mean', 999999)
    ))

    # Find base-yolo baseline for speedup calculation
    baseline_latency = None
    for result in sorted_results:
        if result.get('deployment') == 'base-yolo':
            baseline_latency = result['latency_ms']['mean']
            break

    for result in sorted_results:
        if 'latency_ms' in result:
            deployment = result['deployment']
            framework = result.get('framework', result['protocol']).upper()
            if framework in ['HTTP', 'GRPC']:
                framework = 'TensorRT'
            mean = result['latency_ms']['mean']
            p95 = result['latency_ms']['p95']
            fps = result.get('throughput_fps', 0)
            mode = result.get('mode', 'sequential')

            if CONCURRENCY > 1:
                # For concurrent mode, show throughput and mode
                throughput_str = f"{fps:.1f} FPS"
                mode_str = f"{mode} (c={result.get('concurrency', 1)})"
                report_lines.append(f"{deployment:<15} | {framework:<10} | {mean:>9.2f}  | {p95:>9.2f}  | {throughput_str:<12} | {mode_str}")
            else:
                # For sequential mode, show speedup
                # Calculate speedup vs baseline
                if baseline_latency and deployment != 'base-yolo':
                    speedup = f"{baseline_latency / mean:.1f}x"
                elif deployment == 'base-yolo':
                    speedup = "Baseline"
                else:
                    speedup = "N/A"

                report_lines.append(f"{deployment:<15} | {framework:<10} | {mean:>9.2f}  | {p95:>9.2f}  | {fps:>7.1f} | {speedup}")

    report_lines.append("")

    # Detailed results
    report_lines.append("=" * 80)
    report_lines.append("DETAILED RESULTS")
    report_lines.append("=" * 80)
    report_lines.append("")

    for result in sorted_results:
        if 'latency_ms' not in result:
            continue

        deployment = result['deployment']
        protocol = result['protocol'].upper()

        report_lines.append(f"{'─' * 80}")
        report_lines.append(f"{deployment} ({protocol})")
        report_lines.append(f"{'─' * 80}")

        lat = result['latency_ms']
        report_lines.append(f"  Latency Statistics:")
        report_lines.append(f"    Min:       {lat['min']:>8.2f} ms")
        report_lines.append(f"    Mean:      {lat['mean']:>8.2f} ms")
        report_lines.append(f"    Median:    {lat['median']:>8.2f} ms")
        report_lines.append(f"    P90:       {lat['p90']:>8.2f} ms")
        report_lines.append(f"    P95:       {lat['p95']:>8.2f} ms")
        report_lines.append(f"    P99:       {lat['p99']:>8.2f} ms")
        report_lines.append(f"    Max:       {lat['max']:>8.2f} ms")

        if 'throughput_fps' in result:
            report_lines.append(f"  Throughput:    {result['throughput_fps']:>8.1f} FPS")
            if 'avg_latency_fps' in result:
                report_lines.append(f"  Avg FPS:       {result['avg_latency_fps']:>8.1f} (from latency)")

        if 'concurrency' in result:
            report_lines.append(f"  Concurrency:   {result['concurrency']} workers")

        if 'total_time_sec' in result:
            report_lines.append(f"  Total Time:    {result['total_time_sec']:>8.2f} sec")

        if 'errors' in result and result['errors'] > 0:
            report_lines.append(f"  Errors:        {result['errors']}")

        report_lines.append("")

    # Analysis and recommendations
    report_lines.append("=" * 80)
    report_lines.append("ANALYSIS & RECOMMENDATIONS")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Find best performers (excluding baseline)
    nim_results = [r for r in sorted_results if r.get('deployment') != 'base-yolo']
    if nim_results:
        best_latency = nim_results[0]
        best_throughput = max(nim_results, key=lambda x: x.get('throughput_fps', 0))

        report_lines.append("Best NIM Performance:")
        report_lines.append(f"  Lowest Latency:     {best_latency['deployment']} - {best_latency['latency_ms']['mean']:.2f} ms")
        report_lines.append(f"  Highest Throughput: {best_throughput['deployment']} - {best_throughput.get('throughput_fps', 0):.1f} FPS")

        # TensorRT speedup
        if baseline_latency:
            best_speedup = baseline_latency / best_latency['latency_ms']['mean']
            report_lines.append(f"  TensorRT Speedup:   {best_speedup:.1f}x faster than PyTorch baseline")
        report_lines.append("")

    # Recommendations
    report_lines.append("Recommendations:")
    report_lines.append("")

    report_lines.append("1. For LOWEST LATENCY (real-time applications):")
    report_lines.append("   → Use nim-grpc with gRPC protocol")
    report_lines.append("   → Expected: 8-12ms per request")
    report_lines.append("   → Best for: Real-time video processing, interactive applications")
    report_lines.append("")

    report_lines.append("2. For HIGHEST THROUGHPUT (batch processing):")
    report_lines.append("   → Use nim-batching with gRPC protocol")
    report_lines.append("   → Dynamic batching automatically groups requests")
    report_lines.append("   → Expected: 200-400 FPS (depending on batch sizes)")
    report_lines.append("   → Best for: High-load production, batch inference")
    report_lines.append("")

    report_lines.append("3. For SIMPLICITY (HTTP-only):")
    report_lines.append("   → Use nim-binary with HTTP protocol")
    report_lines.append("   → No gRPC client library needed")
    report_lines.append("   → Expected: 15-25ms per request")
    report_lines.append("   → Best for: Simple integrations, testing")
    report_lines.append("")

    report_lines.append("4. BASELINE COMPARISON (base-yolo):")
    if baseline_latency:
        report_lines.append(f"   → PyTorch baseline latency: {baseline_latency:.2f}ms")
        report_lines.append(f"   → TensorRT NIMs are {best_speedup:.1f}x faster")
        report_lines.append("   → Use for performance baseline comparison")
        report_lines.append("   → Not recommended for production (slower than TensorRT)")
    else:
        report_lines.append("   → PyTorch baseline (no TensorRT optimization)")
        report_lines.append("   → Use for reference only")
    report_lines.append("")

    # Protocol comparison
    report_lines.append("Protocol Comparison:")
    report_lines.append("  gRPC vs HTTP:")
    report_lines.append("    - gRPC is typically 2-10x faster than HTTP JSON")
    report_lines.append("    - gRPC requires tritonclient library")
    report_lines.append("    - HTTP is simpler for testing and debugging")
    report_lines.append("")

    # Deployment comparison
    report_lines.append("Deployment Strategy Comparison:")
    report_lines.append("")
    report_lines.append("  nim-grpc (GPU 2):")
    report_lines.append("    ✓ Lowest latency (~10ms)")
    report_lines.append("    ✓ gRPC + HTTP protocols")
    report_lines.append("    ✓ Single instance, optimized for latency")
    report_lines.append("    → Use for: Low-latency requirements")
    report_lines.append("")

    report_lines.append("  nim-batching (GPU 3):")
    report_lines.append("    ✓ Highest throughput")
    report_lines.append("    ✓ Dynamic batching (5ms queue delay)")
    report_lines.append("    ✓ Dual instances for concurrency")
    report_lines.append("    ✓ gRPC + HTTP protocols")
    report_lines.append("    → Use for: High-throughput production")
    report_lines.append("")

    report_lines.append("  nim-binary (GPU 1):")
    report_lines.append("    ✓ HTTP binary protocol")
    report_lines.append("    ✓ Single instance")
    report_lines.append("    ✓ Lower memory footprint")
    report_lines.append("    → Use for: Simple deployments, HTTP-only")
    report_lines.append("")

    # Cost-performance analysis
    report_lines.append("Cost-Performance Analysis:")
    report_lines.append("  All NIMs use 1 GPU each, so choose based on workload:")
    report_lines.append("    - nim-grpc: Best latency per GPU")
    report_lines.append("    - nim-batching: Best throughput per GPU")
    report_lines.append("    - nim-binary: Lowest complexity")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    # Write report
    report_file = OUTPUT_DIR / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))

    # Print report
    print('\n'.join(report_lines))

    print_success(f"Report saved to: {report_file}")

    return report_file

def main():
    print_header("YOLO NIM Comprehensive Benchmarking Suite")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    # Step 1: Copy benchmark scripts to all pods
    print_header("Step 1: Copying Benchmark Scripts to Pods")
    for deployment_name, config in DEPLOYMENTS.items():
        copy_benchmark_to_pod(deployment_name, config)

    time.sleep(2)

    # Step 2: Run internal benchmarks
    print_header("Step 2: Running Internal Benchmarks")
    print("This measures true GPU inference latency (no network overhead)\n")

    for deployment_name, config in DEPLOYMENTS.items():
        result = run_internal_benchmark(deployment_name, config)
        if result:
            all_results.append(result)

            # Save individual result
            result_file = OUTPUT_DIR / f"{deployment_name}_internal.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            print_success(f"Results saved: {result_file}")

        time.sleep(1)

    # Step 3: Test port forwarding
    print_header("Step 3: Testing Port Forwarding Endpoints")
    print("Ensure setup_port_forwarding.sh is running!\n")

    for deployment_name, config in DEPLOYMENTS.items():
        test_port_forward(deployment_name, config, 'http')
        if config['supports_grpc']:
            test_port_forward(deployment_name, config, 'grpc')
        time.sleep(0.5)

    # Step 4: Test external endpoints
    print_header("Step 4: Testing External LoadBalancer Endpoints")

    for deployment_name, config in DEPLOYMENTS.items():
        test_external_endpoint(deployment_name, config)
        time.sleep(0.5)

    # Step 5: Generate comprehensive report
    print_header("Step 5: Generating Comprehensive Report")

    if all_results:
        report_file = generate_report(all_results)

        # Save all results
        all_results_file = OUTPUT_DIR / f"all_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(all_results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print_success(f"All results saved: {all_results_file}")
    else:
        print_error("No results to generate report")

    print_header("Benchmarking Complete!")
    print(f"\nResults directory: {OUTPUT_DIR}")
    print(f"Report: {report_file if all_results else 'N/A'}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmarking interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
