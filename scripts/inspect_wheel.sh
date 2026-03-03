# --- Wheel Inspection Logic ---
echo ">>> Checking build artifacts..."
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | tail -n 1)

if [ -z "$WHEEL_FILE" ]; then
    echo "ERROR: No wheel found in dist/!"
    exit 1
fi

echo ">>> Inspecting Wheel: $WHEEL_FILE"

# Create a temporary directory for a "clean room" inspection
INSPECT_DIR="inspect_wheel"
if [ -d "$INSPECT_DIR" ]; then rm -rf "$INSPECT_DIR"; fi
mkdir "$INSPECT_DIR"

# Unpack the wheel (it's just a zip file)
unzip -q "$WHEEL_FILE" -d "$INSPECT_DIR"

echo ">>> Contents of the packaged gluex directory:"
ls -lR "$INSPECT_DIR"

# Check for the specific elusive files
echo ">>> Verifying critical binaries..."
find "$INSPECT_DIR/gluex" -name "__init__*.so" -o -name "client*.so"

# Optional: Clean up
# rm -rf "$INSPECT_DIR"
