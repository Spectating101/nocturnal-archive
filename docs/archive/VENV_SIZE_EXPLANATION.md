# Virtual Environment Size Explanation

## Current Status
- **.venv size**: 7.4GB
- **Nocturnal Archive repo (without .venv)**: ~20MB

## Why is .venv so large?

### Breakdown of Space Usage:
```
4.1GB - NVIDIA CUDA libraries (nvidia package)
1.7GB - PyTorch (torch package)
540MB - Triton compiler
203MB - bitsandbytes (quantization library)
147MB - Semgrep (security scanning)
137MB - PyArrow (data processing)
```

### Root Cause:
The **FinGPT integration** requires heavy ML dependencies:
- `transformers>=4.44` - Hugging Face transformers library
- `torch` - PyTorch deep learning framework (pulls NVIDIA CUDA)
- `accelerate>=0.33` - Training optimization
- `peft>=0.12` - Parameter-efficient fine-tuning
- `bitsandbytes>=0.43` - Model quantization
- `sentence-transformers>=2.7.0` - Embedding models

These are defined in `nocturnal-archive-api/requirements.txt` (lines 21-25, 40).

## Is This Normal?
**Yes**, for projects with ML/AI features:
- PyTorch + CUDA is ~6GB standard
- Transformers library is large due to model architectures
- Production ML deployments typically have 5-10GB environments

## Options to Reduce Size:

### Option 1: Skip ML Features (Recommended for Development)
```bash
# Use base requirements only
pip install -r requirements.txt  # with ML deps commented out
```

**Impact**:
- .venv shrinks to ~1.3GB
- FinGPT sentiment analysis unavailable
- Core financial APIs still work

### Option 2: Use CPU-only PyTorch
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Impact**:
- .venv shrinks to ~3GB
- FinGPT works but slower
- No GPU acceleration

### Option 3: Docker with Multi-stage Builds
```dockerfile
# Build stage with ML deps
# Runtime stage with only needed artifacts
```

**Impact**:
- Final image ~4GB (vs 7.4GB)
- Requires Docker setup

## Current Implementation:
- Created `requirements-ml.txt` for optional ML dependencies
- Commented out heavy dependencies in base `requirements.txt`
- FinGPT features gracefully degrade if not installed

## Recommendation:
**For local development**: Skip ML deps unless testing sentiment analysis
**For production**: Use full requirements with Docker optimization
**For CI/CD**: Cache .venv between builds to avoid repeated downloads

---

**Note**: This is NOT a bloat issue - it's the expected size for modern ML stacks. The alternative is to remove FinGPT integration entirely.
