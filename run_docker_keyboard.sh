#!/bin/bash

# Docker run script for LeRobot keyboard control with proper input forwarding

echo "🐳 Starting Docker container with keyboard input support..."
echo "=================================================="

# Check if Docker container exists
if ! docker images | grep -q "lerobot-yahboom-jetson"; then
    echo "❌ Docker image 'lerobot-yahboom-jetson' not found!"
    echo "Please build the Docker image first."
    exit 1
fi

# Check if robot device exists
if [ ! -e "/dev/myserial" ]; then
    echo "⚠️  Warning: /dev/myserial not found. Robot connection may fail."
    echo "    Available USB devices:"
    ls -la /dev/ttyUSB* 2>/dev/null || echo "    No /dev/ttyUSB* devices found"
fi

echo "🔌 Forwarding display and input devices..."
echo "📦 Mounting workspace..."
echo "🚀 Starting container..."
echo

# Run Docker with full privileged access and device permissions
docker run \
    --rm \
    -it \
    --privileged \
    --device=/dev/myserial:/dev/myserial:rwm \
    --device=/dev/ttyUSB2:/dev/ttyUSB2:rwm \
    --device-cgroup-rule='c 188:* rwm' \
    --env DISPLAY=$DISPLAY \
    --volume /tmp/.X11-unix:/tmp/.X11-unix:rw \
    --volume /dev/input:/dev/input:ro \
    --volume /dev:/dev \
    --volume $(pwd):/workspace \
    --workdir /workspace \
    --network host \
    --cap-add=ALL \
    lerobot-yahboom-jetson \
    python direct_keyboard_control.py

echo
echo "👋 Docker session ended!"
