#!/bin/bash
# Build the sandbox Docker image for code execution
# Usage: ./build_sandbox_image.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

IMAGE_NAME="cesi-ptc"
IMAGE_TAG="latest"

echo "🔨 Building $IMAGE_NAME:$IMAGE_TAG Docker image..."

# Check if Dockerfile exists
if [ ! -f "$PROJECT_ROOT/Dockerfile" ]; then
    echo "❌ Error: Dockerfile not found at $PROJECT_ROOT/Dockerfile"
    exit 1
fi

# Build the image
docker build \
    -t "$IMAGE_NAME:$IMAGE_TAG" \
    -f "$PROJECT_ROOT/Dockerfile" \
    "$PROJECT_ROOT"

echo "✅ Successfully built $IMAGE_NAME:$IMAGE_TAG"

# Verify the image
echo ""
echo "📋 Image details:"
docker images "$IMAGE_NAME:$IMAGE_TAG"

# Test the image
echo ""
echo "🧪 Testing sandbox execution..."
docker run --rm "$IMAGE_NAME:$IMAGE_TAG" python -c "print('✅ Sandbox test passed!')"

echo ""
echo "🎉 Sandbox image ready to use!"
echo "   Run: docker run --rm $IMAGE_NAME:$IMAGE_TAG python your_script.py"
