#!/bin/bash
# Run notebooks in CI with timeout and error checking

set -e

echo "📓 Running notebooks in CI..."

# Configuration
NOTEBOOK_DIR="examples"
TIMEOUT_MINUTES=10
MAX_RUNTIME_MINUTES=5

# Check if jupyter is available
if ! command -v jupyter >/dev/null 2>&1; then
    echo "❌ Jupyter not found. Installing..."
    pip install jupyter nbconvert
fi

# Check if notebooks exist
if [ ! -d "$NOTEBOOK_DIR" ]; then
    echo "❌ Notebook directory $NOTEBOOK_DIR not found"
    exit 1
fi

FAILED_NOTEBOOKS=()
RUNTIME_VIOLATIONS=()

# Find all .ipynb files
NOTEBOOKS=$(find "$NOTEBOOK_DIR" -name "*.ipynb" -type f)

if [ -z "$NOTEBOOKS" ]; then
    echo "⚠️  No notebooks found in $NOTEBOOK_DIR"
    exit 0
fi

echo "Found notebooks:"
echo "$NOTEBOOKS"
echo ""

for notebook in $NOTEBOOKS; do
    echo "🔄 Running $notebook..."
    
    # Run notebook with timeout
    start_time=$(date +%s)
    
    if timeout "${TIMEOUT_MINUTES}m" jupyter nbconvert --to notebook --execute --inplace "$notebook" 2>&1; then
        end_time=$(date +%s)
        runtime=$((end_time - start_time))
        runtime_minutes=$((runtime / 60))
        
        echo "✅ $notebook completed in ${runtime}s"
        
        # Check runtime limit
        if [ $runtime_minutes -gt $MAX_RUNTIME_MINUTES ]; then
            echo "⚠️  $notebook exceeded runtime limit (${runtime_minutes}m > ${MAX_RUNTIME_MINUTES}m)"
            RUNTIME_VIOLATIONS+=("$notebook: ${runtime_minutes}m")
        fi
        
        # Check for errors in output
        if grep -q "Error\|Exception\|Traceback" "$notebook"; then
            echo "❌ $notebook contains errors in output"
            FAILED_NOTEBOOKS+=("$notebook: errors_in_output")
        fi
        
    else
        echo "❌ $notebook failed to execute"
        FAILED_NOTEBOOKS+=("$notebook: execution_failed")
    fi
    
    echo ""
done

# Report results
echo "📊 Notebook CI Results:"
echo "========================"

if [ ${#FAILED_NOTEBOOKS[@]} -eq 0 ] && [ ${#RUNTIME_VIOLATIONS[@]} -eq 0 ]; then
    echo "✅ All notebooks passed CI checks"
    exit 0
fi

if [ ${#FAILED_NOTEBOOKS[@]} -gt 0 ]; then
    echo "❌ Failed notebooks:"
    for failure in "${FAILED_NOTEBOOKS[@]}"; do
        echo "  - $failure"
    done
fi

if [ ${#RUNTIME_VIOLATIONS[@]} -gt 0 ]; then
    echo "⚠️  Runtime violations:"
    for violation in "${RUNTIME_VIOLATIONS[@]}"; do
        echo "  - $violation"
    done
fi

echo ""
echo "💡 Tips:"
echo "  - Check notebook outputs for errors"
echo "  - Optimize slow cells or increase MAX_RUNTIME_MINUTES"
echo "  - Use %%time magic to profile cell execution"

exit 1

