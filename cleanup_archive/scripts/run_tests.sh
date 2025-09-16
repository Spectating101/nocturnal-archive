#!/bin/bash

# Exit on error
set -e

echo "Running Nocturnal Archive tests..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run Rust tests first
echo "Running Rust tests..."
cargo test -- --nocapture

# Run Python tests
echo "Running Python tests..."
pytest tests/ -v --cov=src --cov-report=term-missing

# Run integration tests
echo "Running integration tests..."
pytest tests/integration -v

# Check code formatting
echo "Checking Python code formatting..."
black --check src/
echo "Checking Rust code formatting..."
cargo fmt -- --check

# Run linters
echo "Running Python linter..."
flake8 src/
echo "Running Rust linter..."
cargo clippy -- -D warnings

echo "All tests completed!"