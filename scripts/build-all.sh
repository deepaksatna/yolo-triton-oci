#!/bin/bash
#
# Build all Docker images
#
set -e

# Configuration
OCIR_REGION="fra.ocir.io"
OCIR_NAMESPACE="<your-namespace>"  # Update this!
TAG="${1:-latest}"

echo "========================================="
echo "Building all YOLO-NIM Docker images"
echo "========================================="
echo "OCIR Region: $OCIR_REGION"
echo "Namespace: $OCIR_NAMESPACE"
echo "Tag: $TAG"
echo ""

# Build base-yolo (PyTorch baseline)
echo "1/4 Building base-yolo (PyTorch)..."
cd ../docker/base-yolo
docker build -t ${OCIR_REGION}/${OCIR_NAMESPACE}/yolo-base-pytorch:${TAG} .
echo "✓ base-yolo built"
echo ""

# Note: NIMs use official NVIDIA images + init containers
# No custom Dockerfile needed - configured in deployment.yaml
echo "2/4 NIM images use official NVIDIA Triton base"
echo "   Image: nvcr.io/nvidia/tritonserver:23.10-py3"
echo "   TensorRT conversion happens in init container"
echo "✓ NIM configuration ready"
echo ""

echo "========================================="
echo "Build complete!"
echo "========================================="
echo ""
echo "Images built:"
echo "  - ${OCIR_REGION}/${OCIR_NAMESPACE}/yolo-base-pytorch:${TAG}"
echo ""
echo "Next step: ./push-all.sh"
