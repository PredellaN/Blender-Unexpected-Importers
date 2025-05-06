#!/usr/bin/env bash
set -euo pipefail

# Clean existing wheels directory
rm -rf ./wheels
mkdir -p ./wheels

# Specify the Python version and ABI
PYTHON_VERSION=${PYTHON_VERSION:-311}
ABI=cp${PYTHON_VERSION}
IMPLEMENTATION=cp

# Map friendly platform names to pip tags
declare -A PLATFORMS=(
  [windows]=win_amd64
  [macos]=macosx_11_0_arm64
  [linux]=manylinux2014_x86_64
)

for PLATFORM in "${!PLATFORMS[@]}"; do
  TAG=${PLATFORMS[$PLATFORM]}
  echo "Downloading pye57 wheel for $PLATFORM (platform tag: $TAG, Python $PYTHON_VERSION)..."
  pip download pye57 \
    --only-binary=:all: \
    --platform $TAG \
    --python-version ${PYTHON_VERSION} \
    --implementation ${IMPLEMENTATION} \
    --abi ${ABI} \
    --dest ./wheels
done

echo "All wheels have been downloaded to ./wheels/"