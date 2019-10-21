#!/usr/bin/env bash

# ccurl submodule can't be at root level, because then naming collides with
# pyota-ccurl's naming in iota.py repo.
# In iota.crypto.__init__, `from ccurl import ...` tries to import
# from this `ccurl` rather then from `pyota-ccurl`, that results in ImportError.

# Updating ccurl submodule
git submodule update --init --recursive
# Delete binaries if present
rm -f pow/libccurl.so

# Get current working directory
WD=$(pwd)

# Bulding using cmake
echo "Building ccurl library with cmake..."
cd ccurl_repo/ccurl && mkdir -p build && cd build && cmake .. && cmake --build .
cd ../../..
LIB=$(find ./ccurl_repo -name "*.so")

echo "The built library is at:"
echo $LIB

echo "Copying shared library file to the src directory..."
cp $LIB $WD/pow

echo "Done building CCurl binaries..."