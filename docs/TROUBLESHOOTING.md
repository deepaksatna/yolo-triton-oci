# Troubleshooting Guide

Common issues and solutions for YOLO-NIM deployments.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Image Issues](#image-issues)
3. [GPU Issues](#gpu-issues)
4. [Networking Issues](#networking-issues)
5. [Benchmarking Issues](#benchmarking-issues)
6. [Performance Issues](#performance-issues)

## Deployment Issues

### Pod Stuck in Pending

**Symptom:**
```bash
NAME                               READY   STATUS    RESTARTS   AGE
yolo-nim-batching-xxxxx            0/1     Pending   0          5m
```

**Diagnosis:**
```bash
kubectl describe pod -n <namespace> <pod-name> | grep Events -A 10
```

**Common Causes:**

1. **Insufficient GPU:**
```
Events:
  Warning  FailedScheduling  0/4 nodes: Insufficient nvidia.com/gpu
```
**Solution:** Add GPU nodes or reduce GPU requests

2. **Node Affinity Mismatch:**
```
Events:
  Warning  FailedScheduling  0/4 nodes didn't match node affinity
```
**Solution:** Remove/adjust node affinity in deployment.yaml

3. **Resource Limits Too High:**
```
Events:
  Warning  FailedScheduling  Insufficient memory/cpu
```
**Solution:** Reduce resource requests in deployment.yaml

### Pod Stuck in Init

**Symptom:**
```bash
yolo-nim-binary-xxxxx   0/1     Init:0/1   0          10m
```

**Diagnosis:**
```bash
kubectl logs -n <namespace> <pod-name> -c tensorrt-converter
```

**Common Causes:**

1. **Model Download Failure:**
```
Error: Failed to download model from...
```
**Solution:** Check internet connectivity, verify model URL

2. **TensorRT Conversion Error:**
```
Error: CUDA out of memory during conversion
```
**Solution:** Increase init container memory limits

3. **Still Converting (Normal):**
```
[TRT] Tactic: 0x0000... Time: 0.003...
```
**Solution:** Wait 5-10 minutes for conversion to complete

### CrashLoopBackOff

**Symptom:**
```bash
yolo-base-xxxxx   0/1     CrashLoopBackOff   3          5m
```

**Diagnosis:**
```bash
kubectl logs -n <namespace> <pod-name> --previous
```

**Common Causes:**

1. **Missing Dependencies:**
```
ModuleNotFoundError: No module named 'torch'
```
**Solution:** Rebuild Docker image with correct dependencies

2. **GPU Not Available:**
```
RuntimeError: CUDA not available
```
**Solution:** Verify GPU node selector and resources

3. **Port Already in Use:**
```
OSError: [Errno 98] Address already in use
```
**Solution:** Check for conflicting services

## Image Issues

### ImagePullBackOff

**Symptom:**
```bash
yolo-base-xxxxx   0/1     ImagePullBackOff   0          2m
```

**Diagnosis:**
```bash
kubectl describe pod -n <namespace> <pod-name> | grep -A 5 "Events:"
```

**Common Causes:**

1. **Invalid Credentials:**
```
Error: Failed to pull image: unauthorized
```
**Solution:**
```bash
# Recreate image pull secret
kubectl create secret docker-registry ocir-secret \
  --docker-server=fra.ocir.io \
  --docker-username='<tenancy>/<username>' \
  --docker-password='<auth-token>' \
  -n <namespace>

# Add to deployment
imagePullSecrets:
  - name: ocir-secret
```

2. **Image Doesn't Exist:**
```
Error: manifest not found
```
**Solution:**
```bash
# Verify image in OCIR
oci artifacts container image list --compartment-id <id>

# Push if missing
docker push fra.ocir.io/<namespace>/<image>:latest
```

3. **Wrong Image Name:**
```
Error: repository not found
```
**Solution:** Check image name in deployment.yaml matches OCIR

## GPU Issues

### CUDA Out of Memory

**Symptom:**
```
RuntimeError: CUDA out of memory
```

**Solution:**
```bash
# Reduce batch size in model config
# Or restart pod to clear GPU memory
kubectl delete pod -n <namespace> <pod-name>
```

### Illegal Memory Access

**Symptom:**
```
CUDA error: an illegal memory access was encountered
```

**Solution:**
```bash
# GPU memory corruption - restart pod
kubectl delete pod -n <namespace> <pod-name>

# If persists, restart node
kubectl drain <node-name>
kubectl uncordon <node-name>
```

### No GPU Allocated

**Symptom:**
```
No CUDA-capable device is detected
```

**Diagnosis:**
```bash
# Check GPU on node
kubectl exec -n <namespace> <pod-name> -- nvidia-smi

# Check GPU allocation
kubectl describe node <node-name> | grep -A 5 "Allocated resources"
```

**Solution:**
```yaml
# Ensure GPU requested in deployment.yaml
resources:
  limits:
    nvidia.com/gpu: 1
  requests:
    nvidia.com/gpu: 1
```

## Networking Issues

### LoadBalancer Pending

**Symptom:**
```bash
yolo-base-service   LoadBalancer   10.96.xxx.xxx   <pending>   80:30080/TCP
```

**Solution:**
```bash
# Check OCI LB provisioning (can take 5-10 min)
# If stuck >10 min, check OCI console for errors

# Alternative: Use NodePort
# Edit service.yaml:
type: NodePort
```

### Can't Access External IP

**Symptom:**
```bash
curl: (7) Failed to connect to xxx.xxx.xxx.xxx port 80
```

**Diagnosis:**
```bash
# Check service
kubectl get svc -n <namespace>

# Check endpoints
kubectl get endpoints -n <namespace>

# Check security lists in OCI console
```

**Solution:**
1. Verify pod is Running: `kubectl get pods -n <namespace>`
2. Check security lists allow ingress on port 80
3. Test from within cluster:
```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://<service-name>.<namespace>.svc.cluster.local
```

## Benchmarking Issues

### Port Forwarding Fails

**Symptom:**
```
Error: unable to forward port... connection refused
```

**Solution:**
```bash
# Kill existing forwards
pkill -f "kubectl port-forward"

# Verify pod is running
kubectl get pods -A | grep yolo

# Restart port forwarding
./setup_port_forwarding.sh
```

### High Error Rate (>20%)

**Symptom:**
```
Progress: 100/1000 - Errors: 250
```

**Solution:**
```python
# Reduce concurrency in benchmark_all_pods.py
CONCURRENCY = 8  # instead of 32
ITERATIONS = 200  # instead of 1000
```

### Warmup Failures

**Symptom:**
```
Warmup complete (0/10 successful)
Benchmark failed
```

**Solution:**
```bash
# Check pod health
kubectl logs -n <namespace> <pod-name>

# Test endpoint manually
curl http://127.0.0.1:8000/health

# Restart pod if CUDA errors
kubectl delete pod -n <namespace> <pod-name>
```

## Performance Issues

### Lower Than Expected Performance

**Expected:** 7-10ms latency (TensorRT)
**Actual:** 50ms+ latency

**Diagnosis:**
```bash
# Check GPU utilization
kubectl exec -n <namespace> <pod-name> -- nvidia-smi

# Check if using GPU
kubectl logs -n <namespace> <pod-name> | grep -i gpu

# Check TensorRT engine loaded
kubectl logs -n <namespace> <pod-name> | grep -i tensorrt
```

**Common Causes:**

1. **Using CPU instead of GPU:**
```
# Check CUDA_VISIBLE_DEVICES
kubectl describe pod -n <namespace> <pod-name> | grep CUDA
```

2. **Still using ONNX instead of TensorRT:**
```
# Check model repository
kubectl exec -n <namespace> <pod-name> -- \
  ls -la /model-repository/yolov8s/1/

# Should see: model.plan (TensorRT)
# Not: model.onnx
```

3. **Wrong precision:**
```
# TensorRT should use FP16 for A10
# Check config.pbtxt
kubectl exec -n <namespace> <pod-name> -- \
  cat /model-repository/yolov8s/config.pbtxt | grep optimization
```

### PyTorch Slower Than Expected

**Expected:** 80-100ms
**Actual:** 200ms+

**Common Causes:**

1. **Using CPU:**
```bash
# Check logs
kubectl logs -n yolo-base <pod-name> | grep "loaded on"
# Should say: "Model loaded on GPU"
```

2. **No GPU allocated:**
```yaml
# Add to deployment:
resources:
  limits:
    nvidia.com/gpu: 1
```

### nim-batching Not Batching

**Symptom:** Performance same as nim-binary

**Diagnosis:**
```bash
# Check dynamic batching config
kubectl exec -n yolo-nim-batching <pod-name> -- \
  cat /model-repository/yolov8s/config.pbtxt | grep -A 5 "dynamic_batching"
```

**Solution:**
```
# Should have:
dynamic_batching {
  preferred_batch_size: [ 4, 8 ]
  max_queue_delay_microseconds: 5000
}
```

## Getting Help

### Collect Diagnostic Info

```bash
#!/bin/bash
# Save diagnostic information

NAMESPACE="yolo-nim-batching"  # Update as needed

echo "=== Pod Status ===" > diagnostics.txt
kubectl get pods -n $NAMESPACE >> diagnostics.txt

echo "=== Pod Description ===" >> diagnostics.txt
kubectl describe pod -n $NAMESPACE >> diagnostics.txt

echo "=== Init Container Logs ===" >> diagnostics.txt
kubectl logs -n $NAMESPACE <pod-name> -c tensorrt-converter >> diagnostics.txt

echo "=== Main Container Logs ===" >> diagnostics.txt
kubectl logs -n $NAMESPACE <pod-name> -c triton-server >> diagnostics.txt

echo "=== Service Info ===" >> diagnostics.txt
kubectl get svc -n $NAMESPACE >> diagnostics.txt

echo "=== Events ===" >> diagnostics.txt
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' >> diagnostics.txt
```

### Contact Support

When reporting issues, include:
1. Output of diagnostic script above
2. Kubernetes deployment manifests
3. Expected vs actual behavior
4. Steps to reproduce
5. Environment details (GPU type, K8s version)

---

**Last Updated:** 2026-01-01
