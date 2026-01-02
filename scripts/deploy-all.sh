#!/bin/bash
#
# Deploy all YOLO configurations to Kubernetes
#
set -e

echo "========================================="
echo "Deploying all YOLO-NIM configurations"
echo "========================================="
echo ""

# Check kubectl
if ! kubectl version --client > /dev/null 2>&1; then
    echo "✗ kubectl not found or not configured"
    exit 1
fi
echo "✓ kubectl configured"
echo ""

# Deploy base-yolo
echo "1/4 Deploying base-yolo (PyTorch baseline)..."
kubectl apply -f ../kubernetes/base-yolo/deployment.yaml
echo "✓ base-yolo deployed"
echo ""

# Deploy nim-binary
echo "2/4 Deploying nim-binary (TensorRT HTTP)..."
kubectl apply -f ../kubernetes/nim-binary/deployment.yaml
echo "✓ nim-binary deployed"
echo ""

# Deploy nim-grpc
echo "3/4 Deploying nim-grpc (TensorRT gRPC)..."
kubectl apply -f ../kubernetes/nim-grpc/deployment.yaml
echo "✓ nim-grpc deployed"
echo ""

# Deploy nim-batching
echo "4/4 Deploying nim-batching (TensorRT batching)..."
kubectl apply -f ../kubernetes/nim-batching/deployment.yaml
echo "✓ nim-batching deployed"
echo ""

echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "Check status:"
echo "  kubectl get pods -A | grep yolo"
echo ""
echo "Wait for pods to be ready (NIMs take 5-10 min for TensorRT conversion):"
echo "  kubectl wait --for=condition=ready pod -l app=yolo-base -n yolo-base --timeout=300s"
echo "  kubectl wait --for=condition=ready pod -l app=yolo-nim-binary -n yolo-nim-binary --timeout=600s"
echo "  kubectl wait --for=condition=ready pod -l app=yolo-nim-grpc-inference -n yolo-nim-grpc --timeout=600s"
echo "  kubectl wait --for=condition=ready pod -l app=yolo-nim-batching -n yolo-nim-batching --timeout=600s"
echo ""
echo "Next step: Run benchmarks"
echo "  cd ../benchmarking"
echo "  ./setup_port_forwarding.sh  # Terminal 1"
echo "  python3 benchmark_all_pods.py  # Terminal 2"
