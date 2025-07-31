#!/bin/bash

# Build script for PLaMo Translation App
set -e

PROJECT_DIR="/Users/ibushimaru/Desktop/claude-workspace/PLaMoTranslationApp"
SOURCE_DIR="$PROJECT_DIR/PLaMoTranslationApp"
BUILD_DIR="$PROJECT_DIR/build"
APP_NAME="PLaMoTranslationApp"

echo "Building PLaMo Translation App..."

# Create build directory
mkdir -p "$BUILD_DIR"

# Compile Swift sources
cd "$SOURCE_DIR"

echo "Compiling Swift sources..."
swiftc -import-objc-header PLaMoTranslationApp-Bridging-Header.h \
    -framework Cocoa \
    -framework Carbon \
    -framework ApplicationServices \
    -framework ServiceManagement \
    -o "$BUILD_DIR/$APP_NAME" \
    *.swift

if [ $? -eq 0 ]; then
    echo "Build successful! Executable created at: $BUILD_DIR/$APP_NAME"
    echo "To run the app, execute: $BUILD_DIR/$APP_NAME"
else
    echo "Build failed!"
    exit 1
fi