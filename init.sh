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

# By default, ccurl lib compiles with debug symbols, that we don't necessarly
# want to see when using the interface. Remove them before building.

# Definition of a DEBUG symbol
pattern='#ifndef DEBUG'

# Find files that define DEBUG symbols in ccurl repo
result=$(grep -rnw 'ccurl_repo/' -e "$pattern" -l)

# Result is not empty
if [ -n "$result" ]; then
    # Transform cmd output to array
    readarray -t files <<<$result

    # Go thorugh the files and delete line with pattern + 2 follwing lines
    # A definition in c looks like this:
    #   #ifndef DEBUG
    #   define DEBUG
    #   endif
    for i in "${files[@]}"; do
        echo "Removing DEBUG symbols from $i"
        sed -i -e "/$pattern/,+2d" $i
    done
fi

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