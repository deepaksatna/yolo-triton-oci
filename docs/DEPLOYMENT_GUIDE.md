# YOLO-NIM Deployment Guide

Complete guide for deploying all 4 YOLO configurations to OKE.

## Prerequisites

### 1. OCI CLI
```bash
# Install
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configure
oci setup config
```

### 2. Docker
```bash
# Verify
docker --version

# Login to OCIR
docker login fra.ocir.io
# Username: <tenancy-namespace>/<username>
# Password: <auth-token>
```

### 3. kubectl
```bash
# Verify
kubectl version --client

# Get kubeconfig
oci ce cluster create-kubeconfig --cluster-id <cluster-id>
kubectl get nodes
```

## Step-by-Step Deployment

### Step 1: Update Configuration

Edit OCIR namespace in all deployment manifests:
```bash
# Update image references
find kubernetes/ -name "*.yaml" -exec sed -i '' 's/<your-namespace>/YOUR_NAMESPACE/g' {} +

# Update scripts
sed -i '' 's/<your-namespace>/YOUR_NAMESPACE/g' scripts/*.sh
```

### Step 2: Build Images

```bash
cd scripts
./build-all.sh latest
```

This builds:
- `base-yolo`: PyTorch baseline image

NIMs use official NVIDIA Triton image + init container for TensorRT conversion.

### Step 3: Push to OCIR

```bash
./push-all.sh latest
```

Verifies OCIR authentication and pushes images.

### Step 4: Create Namespaces

```bash
kubectl create namespace yolo-base
kubectl create namespace yolo-nim-binary
kubectl create namespace yolo-nim-grpc
kubectl create namespace yolo-nim-batching
```

### Step 5: Create Image Pull Secret (if needed)

```bash
kubectl create secret docker-registry ocir-secret \
  --docker-server=fra.ocir.io \
  --docker-username='<tenancy-namespace>/<username>' \
  --docker-password='<auth-token>' \
  -n yolo-base

# Repeat for other namespaces
```

### Step 6: Deploy All Configurations

```bash
./deploy-all.sh
```

Or deploy individually:
```bash
kubectl apply -f ../kubernetes/base-yolo/deployment.yaml
kubectl apply -f ../kubernetes/nim-binary/deployment.yaml
kubectl apply -f ../kubernetes/nim-grpc/deployment.yaml
kubectl apply -f ../kubernetes/nim-batching/deployment.yaml
```

### Step 7: Wait for Pods Ready

```bash
# Check status
kubectl get pods -A | grep yolo

# Wait for base-yolo (1-2 min)
kubectl wait --for=condition=ready pod -l app=yolo-base -n yolo-base --timeout=300s

# Wait for NIMs (5-10 min for TensorRT conversion)
kubectl wait --for=condition=ready pod -l app=yolo-nim-binary -n yolo-nim-binary --timeout=600s
kubectl wait --for=condition=ready pod -l app=yolo-nim-grpc-inference -n yolo-nim-grpc --timeout=600s
kubectl wait --for=condition=ready pod -l app=yolo-nim-batching -n yolo-nim-batching --timeout=600s
```

## Deployment Details

### base-yolo
- **Namespace:** yolo-base
- **Image:** Custom PyTorch + Flask
- **GPU:** 1 (any available)
- **Startup time:** 1-2 minutes
- **Service:** LoadBalancer on port 80

### nim-binary
- **Namespace:** yolo-nim-binary
- **Image:** NVIDIA Triton + init container
- **GPU:** 1 (node affinity can be set)
- **Startup time:** 5-10 minutes (TensorRT conversion)
- **Service:** LoadBalancer on port 80

### nim-grpc
- **Namespace:** yolo-nim-grpc
- **Image:** NVIDIA Triton + init container
- **GPU:** 1
- **Startup time:** 5-10 minutes
- **Service:** LoadBalancer on port 80 (HTTP), 8001 (gRPC)
- **Protocols:** HTTP + gRPC

### nim-batching
- **Namespace:** yolo-nim-batching
- **Image:** NVIDIA Triton + init container
- **GPU:** 1
- **Startup time:** 5-10 minutes
- **Service:** LoadBalancer on port 80 (HTTP), 8001 (gRPC)
- **Features:** Dynamic batching (max batch: 8, delay: 5ms)
- **Instances:** 2 (for better concurrency)

## Verification

### Check All Deployments
```bash
kubectl get deploy,svc,pods -A | grep yolo
```

### Test Health Endpoints
```bash
# Get external IPs
kubectl get svc -A | grep yolo

# Test each deployment
curl http://<base-yolo-ip>/health
curl http://<nim-binary-ip>/v2/health/ready
curl http://<nim-grpc-ip>/v2/health/ready
curl http://<nim-batching-ip>/v2/health/ready
```

### Check Logs
```bash
# base-yolo
kubectl logs -n yolo-base -l app=yolo-base

# nim-binary (init container)
kubectl logs -n yolo-nim-binary -l app=yolo-nim-binary -c tensorrt-converter

# nim-binary (triton server)
kubectl logs -n yolo-nim-binary -l app=yolo-nim-binary -c triton-server
```

## Troubleshooting

### Pod Stuck in Init
**Symptom:** Pod shows `Init:0/1` for >10 minutes

**Solution:**
```bash
# Check init container logs
kubectl logs -n <namespace> <pod-name> -c tensorrt-converter

# Common issues:
# - Model download failure: Check internet connectivity
# - TensorRT conversion error: Check GPU availability
# - OOM: Increase init container memory limits
```

### ImagePullBackOff
**Symptom:** Pod shows `ImagePullBackOff`

**Solution:**
```bash
# Verify image exists in OCIR
oci artifacts container image list --compartment-id <compartment-id>

# Check image pull secret
kubectl get secret ocir-secret -n <namespace>

# Recreate if needed
kubectl delete secret ocir-secret -n <namespace>
kubectl create secret docker-registry ocir-secret ...
```

### GPU Not Available
**Symptom:** Pod pending with "Insufficient nvidia.com/gpu"

**Solution:**
```bash
# Check GPU nodes
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPUs:.status.capacity.nvidia\\.com/gpu

# Check GPU allocation
kubectl describe nodes | grep -A 5 "Allocated resources"

# Reduce GPU requests or add GPU nodes
```

## Cleanup

### Delete Specific Deployment
```bash
kubectl delete -f kubernetes/base-yolo/deployment.yaml
kubectl delete namespace yolo-base
```

### Delete All
```bash
kubectl delete namespace yolo-base yolo-nim-binary yolo-nim-grpc yolo-nim-batching
```

## Next Steps

After successful deployment:
1. Run benchmarks (see `BENCHMARKING_GUIDE.md`)
2. Add results to `results/` directory
3. Choose deployment strategy based on performance

---

**Last Updated:** 2026-01-01
