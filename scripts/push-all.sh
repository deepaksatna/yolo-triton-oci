#!/bin/bash
#
# Push all Docker images to OCIR
#
set -e

# Configuration
OCIR_REGION="fra.ocir.io"
OCIR_NAMESPACE="<your-namespace>"  # Update this!
TAG="${1:-latest}"

echo "========================================="
echo "Pushing all images to OCIR"
echo "========================================="
echo "OCIR Region: $OCIR_REGION"
echo "Namespace: $OCIR_NAMESPACE"
echo "Tag: $TAG"
echo ""

# Check docker login
echo "Checking OCIR authentication..."
if ! docker login ${OCIR_REGION} 2>/dev/null; then
    echo "⚠ Not logged in to OCIR"
    echo "Please login first:"
    echo "  docker login ${OCIR_REGION}"
    echo "  Username: <tenancy-namespace>/<username>"
    echo "  Password: <auth-token>"
    exit 1
fi
echo "✓ Authenticated"
echo ""

# Push base-yolo
echo "Pushing base-yolo..."
docker push ${OCIR_REGION}/${OCIR_NAMESPACE}/yolo-base-pytorch:${TAG}
echo "✓ base-yolo pushed"
echo ""

echo "========================================="
echo "Push complete!"
echo "========================================="
echo ""
echo "Images pushed:"
echo "  - ${OCIR_REGION}/${OCIR_NAMESPACE}/yolo-base-pytorch:${TAG}"
echo ""
echo "Next step: ./deploy-all.sh"
