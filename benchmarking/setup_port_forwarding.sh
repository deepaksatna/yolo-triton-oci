#!/bin/bash
# Setup Port Forwarding for All YOLO NIM Pods
# Run this BEFORE running the benchmark script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}Port Forwarding Setup for All YOLO NIM Deployments${NC}"
echo -e "${BOLD}======================================================================${NC}\n"

# Kill existing port forwards
echo -e "${BLUE}Step 1: Cleaning up existing port forwards...${NC}"
pkill -f "port-forward.*8000" 2>/dev/null || true
pkill -f "port-forward.*8001" 2>/dev/null || true
pkill -f "port-forward.*8100" 2>/dev/null || true
pkill -f "port-forward.*8101" 2>/dev/null || true
pkill -f "port-forward.*8200" 2>/dev/null || true
pkill -f "port-forward.*8201" 2>/dev/null || true
pkill -f "port-forward.*8300" 2>/dev/null || true
pkill -f "port-forward.*8301" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Cleaned up${NC}\n"

# Port mapping:
# base-yolo:     8000 (HTTP)
# nim-binary:    8100 (HTTP)
# nim-grpc:      8200 (HTTP), 8201 (gRPC)
# nim-batching:  8300 (HTTP), 8301 (gRPC)
# Using 127.0.0.1 instead of localhost

echo -e "${BLUE}Step 2: Setting up port forwards...${NC}\n"

# 1. base-yolo
echo -e "${YELLOW}Setting up base-yolo (127.0.0.1:8000)...${NC}"
POD_NAME=$(kubectl get pods -n yolo-base -l app=yolo-base -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ ! -z "$POD_NAME" ]; then
    kubectl port-forward -n yolo-base "$POD_NAME" 8000:8000 &>/dev/null &
    sleep 1
    if curl -s http://127.0.0.1:8000/v2/health/ready &>/dev/null; then
        echo -e "${GREEN}✓ base-yolo: HTTP on 127.0.0.1:8000 (PID: $!)${NC}"
    else
        echo -e "${YELLOW}⚠ base-yolo: Port forward may not be ready${NC}"
    fi
else
    echo -e "${RED}✗ base-yolo pod not found${NC}"
fi

# 2. nim-binary
echo -e "${YELLOW}Setting up nim-binary (127.0.0.1:8100)...${NC}"
POD_NAME=$(kubectl get pods -n yolo-nim-binary -l app=yolo-nim-binary -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ ! -z "$POD_NAME" ]; then
    kubectl port-forward -n yolo-nim-binary "$POD_NAME" 8100:8000 &>/dev/null &
    sleep 1
    if curl -s http://127.0.0.1:8100/v2/health/ready &>/dev/null; then
        echo -e "${GREEN}✓ nim-binary: HTTP on 127.0.0.1:8100 (PID: $!)${NC}"
    else
        echo -e "${YELLOW}⚠ nim-binary: Port forward may not be ready${NC}"
    fi
else
    echo -e "${RED}✗ nim-binary pod not found${NC}"
fi

# 3. nim-grpc (HTTP + gRPC)
echo -e "${YELLOW}Setting up nim-grpc (127.0.0.1:8200, 8201)...${NC}"
POD_NAME=$(kubectl get pods -n yolo-nim-grpc -l app=yolo-nim-grpc-inference -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ ! -z "$POD_NAME" ]; then
    kubectl port-forward -n yolo-nim-grpc "$POD_NAME" 8200:8000 8201:8001 &>/dev/null &
    sleep 1
    HTTP_OK=false
    if curl -s http://127.0.0.1:8200/v2/health/ready &>/dev/null; then
        HTTP_OK=true
    fi
    # gRPC health check doesn't work with curl, just check HTTP
    if [ "$HTTP_OK" = true ]; then
        echo -e "${GREEN}✓ nim-grpc: HTTP on 127.0.0.1:8200, gRPC on 127.0.0.1:8201 (PID: $!)${NC}"
    else
        echo -e "${YELLOW}⚠ nim-grpc: Port forward may not be ready${NC}"
    fi
else
    echo -e "${RED}✗ nim-grpc pod not found${NC}"
fi

# 4. nim-batching (HTTP + gRPC)
echo -e "${YELLOW}Setting up nim-batching (127.0.0.1:8300, 8301)...${NC}"
POD_NAME=$(kubectl get pods -n yolo-nim-batching -l app=yolo-nim-batching -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ ! -z "$POD_NAME" ]; then
    kubectl port-forward -n yolo-nim-batching "$POD_NAME" 8300:8000 8301:8001 &>/dev/null &
    sleep 1
    HTTP_OK=false
    if curl -s http://127.0.0.1:8300/v2/health/ready &>/dev/null; then
        HTTP_OK=true
    fi
    # gRPC health check doesn't work with curl, just check HTTP
    if [ "$HTTP_OK" = true ]; then
        echo -e "${GREEN}✓ nim-batching: HTTP on 127.0.0.1:8300, gRPC on 127.0.0.1:8301 (PID: $!)${NC}"
    else
        echo -e "${YELLOW}⚠ nim-batching: Port forward may not be ready${NC}"
    fi
else
    echo -e "${RED}✗ nim-batching pod not found${NC}"
fi

echo ""
echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}Port Forwarding Active${NC}"
echo -e "${BOLD}======================================================================${NC}\n"

echo -e "${GREEN}Port Mapping:${NC}"
echo "  base-yolo:     127.0.0.1:8000 (HTTP)"
echo "  nim-binary:    127.0.0.1:8100 (HTTP)"
echo "  nim-grpc:      127.0.0.1:8200 (HTTP), 127.0.0.1:8201 (gRPC)"
echo "  nim-batching:  127.0.0.1:8300 (HTTP), 127.0.0.1:8301 (gRPC)"
echo ""

echo -e "${YELLOW}Keep this terminal open!${NC}"
echo "Run the benchmark script in a new terminal:"
echo "  python3 benchmark_all_pods.py"
echo ""
echo "To stop port forwarding, press Ctrl+C or run:"
echo "  pkill -f port-forward"
echo ""

# Wait for Ctrl+C
trap "echo -e '\n${YELLOW}Stopping port forwards...${NC}'; pkill -f port-forward; exit 0" SIGINT SIGTERM

echo -e "${BOLD}======================================================================${NC}\n"

# Keep script running
wait
