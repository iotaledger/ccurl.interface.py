#!/bin/bash

# Updating ccurl submodule
git submodule update --init --recursive
rm -f src/libccurl.so
rm -f src/helpers.dll
WD=$(pwd)

# Bulding using cmake
echo "Building ccurl library with cmake..."
cd ccurl && mkdir -p build && cd build && cmake .. && cmake --build .
cd ../..
LIB=$(find . -name "*.so")

echo "The built library is at:"
echo $LIB

echo "Copying shared library file to the src directory..."
cp $LIB pow/

echo "Done."

# Bulding using bazel
echo "Building entangled/common/helpers library with bazel..."
cd entangled
bazel build //common/helpers:helpers.dll

LIB="bazel-bin/common/helpers/helpers.dll"
echo "Copying shared library file to the src directory..."
cp $LIB $WD/pow

echo "Done."
