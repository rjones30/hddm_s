#!/bin/bash
#
# local_test_build.sh - Dry-run script for Alma9 / RHEL9 environments
#
# author: richard.t.jones at uconn.edu
# version: 2-28-2026

set -e

# --- Configuration ---
BUILD_DIR="test_workspace"
VENV_DIR="test_venv"
PYTHON_EXE=$(which python3)
export CIBW_BUILD_ID=local-test

echo "=== Starting Local Dry-Run of gluex.hddm_s ==="
echo "Target Platform: $(uname -a)"

# 1. Clean up previous attempts
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning old workspace..."
    rm -rf "$BUILD_DIR"
fi

# 2. Setup isolated environment
echo "Setting up virtual environment..."
$PYTHON_EXE -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

# 3. Pre-flight check: dummy file creation
#echo "Checking if setup.py creates the dummy stub..."
#$PYTHON_EXE -c "import os; dummy='gluex/hddm_s/pyxrootd.so'; print(f'Exists: {os.path.exists(dummy)}')"

# 4. Run the build
# We use --verbose so we can see the 'spawn' commands and the 'Harvest' logs
echo "Launching build (this may take a while)..."
python setup.py bdist_wheel --verbose

# 5. Post-Build Analysis
echo "=== Analyzing Build Results ==="

# Check if the wheel was actually created
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)
if [ -z "$WHEEL_FILE" ]; then
    echo "ERROR: Wheel was not created!"
    exit 1
fi
echo "Found Wheel: $WHEEL_FILE"

# Check for the xrootd client module directory and its compiled content instead
ls -d gluex/hddm_s/pyxrootd/
ls -l gluex/hddm_s/pyxrootd/client*.so

# 6. Check Linkage
# We expect to see XrdCl and XrdUtils in the 'needed' list
echo "Checking clinet*.so internal linkage..."
readelf -d gluex/hddm_s/pyxrootd/client*.so | grep NEEDED

echo "Checking main hddm_s internal linkage..."
# Find the compiled .so inside the build directory
MAIN_SO=$(find build/lib* -name "hddm_s*.so" | grep -v pyxrootd)
readelf -d "$MAIN_SO" | grep NEEDED

echo "=== Dry Run Complete ==="
echo "If the 'NEEDED' lists above show libXrdCl, you are ready for GitHub Actions."
