#!/bin/bash

# FFmpeg Installation Script
# This script attempts to install FFmpeg on various platforms

echo "FFmpeg Installation Script"
echo "=========================="
echo ""

# Check if FFmpeg is already installed
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg is already installed!"
    ffmpeg -version | head -3
    exit 0
fi

echo "FFmpeg not found. Attempting to install..."
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"

    # Try apt (Ubuntu/Debian)
    if command -v apt-get &> /dev/null; then
        echo "Using apt-get..."
        sudo apt-get update
        sudo apt-get install -y ffmpeg

    # Try yum (CentOS/RHEL)
    elif command -v yum &> /dev/null; then
        echo "Using yum..."
        sudo yum install -y ffmpeg

    # Try dnf (Fedora)
    elif command -v dnf &> /dev/null; then
        echo "Using dnf..."
        sudo dnf install -y ffmpeg

    # Try static binary as fallback
    else
        echo "Package manager not found. Downloading static binary..."
        wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -O /tmp/ffmpeg.tar.xz
        tar -xf /tmp/ffmpeg.tar.xz -C /tmp
        sudo cp /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/
        sudo cp /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/
        sudo chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"

    # Try Homebrew
    if command -v brew &> /dev/null; then
        echo "Using Homebrew..."
        brew install ffmpeg
    else
        echo "ERROR: Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

else
    echo "ERROR: Unsupported operating system: $OSTYPE"
    echo "Please install FFmpeg manually from: https://ffmpeg.org/download.html"
    exit 1
fi

# Verify installation
echo ""
echo "Verifying installation..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg successfully installed!"
    echo ""
    ffmpeg -version | head -3
else
    echo "✗ FFmpeg installation failed"
    echo ""
    echo "Please install FFmpeg manually:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi
