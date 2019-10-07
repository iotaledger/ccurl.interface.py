#!/bin/bash

# Updating ccurl submodule
git submodule update --init --recursive
# Delete binaries if present
rm -f pow/libccurl.so
#rm -f pow/helpers.dll
# Get current working directory
WD=$(pwd)

# Bulding using cmake
echo "Building ccurl library with cmake..."
cd ccurl && mkdir -p build && cd build && cmake .. && cmake --build .
cd ../..
LIB=$(find . -name "*.so")

echo "The built library is at:"
echo $LIB

echo "Copying shared library file to the src directory..."
cp $LIB $WD/pow

echo "Done building CCurl binaries..."