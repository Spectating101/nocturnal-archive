# 🌙 Nocturnal Platform - Unified AI Assistant

**The unified platform combining FinSight (Financial Data), Archive (Research), and Assistant (R/SQL) into one powerful API.**

## 🎯 **What is Nocturnal Platform?**

Nocturnal Platform is a unified AI-powered API that combines three specialized modules:

- **🔍 FinSight**: Financial data analysis and SEC EDGAR integration
- **📚 Archive**: Academic research and synthesis platform  
- **💻 Assistant**: R/SQL programming assistance
- **🔗 Unified**: Cross-module search and analysis

All powered by **Groq's free tier** for cost-effective AI processing.

## 🚀 **Quick Start**

### 1. **Get Groq API Keys (Free!)**
```bash
# Visit https://console.groq.com/
# Sign up and get 3 free API keys
# Each key gives you 14,400 requests/day for free!
```

### 2. **Setup Environment**
```bash
# Clone the repository
cd unified-platform

# Copy environment template
cp env.example .env

# Edit .env with your Groq API keys
nano .env
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Run the Platform**
```bash
# Development mode
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. **Test the API**
```bash
# Health check
curl http://localhost:8000/health

# R/SQL Assistant (working immediately!)
curl -X POST http://localhost:8000/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I create a scatter plot in R?"}'
```

## 📊 **API Endpoints**

### **Core Platform**
- `GET /` - Platform overview and status
- `GET /health` - Detailed health check
- `GET /status` - Platform status and statistics

### **Assistant Module (R/SQL)**
- `POST /api/v1/assistant/chat` - Chat assistance
- `GET /api/v1/assistant/chat` - Chat assistance (GET)
- `POST /api/v1/assistant/code-example` - Get code examples
- `GET /api/v1/assistant/r-example` - R code examples
- `GET /api/v1/assistant/sql-example` - SQL code examples

### **Unified Features**
- `GET /api/v1/unified/search` - Cross-module search
- `POST /api/v1/unified/search` - Cross-module search (POST)
- `POST /api/v1/unified/analyze` - Cross-module analysis
- `GET /api/v1/unified/dashboard` - Unified dashboard

### **Module Status**
- `GET /api/v1/finsight/status` - FinSight status (placeholder)
- `GET /api/v1/archive/status` - Archive status (placeholder)
- `GET /api/v1/assistant/status` - Assistant status

## 🔧 **Configuration**

### **Environment Variables**

Key configuration options in `.env`:

```bash
# Groq API Keys (REQUIRED)
GROQ_API_KEY_1=your_first_groq_api_key_here
GROQ_API_KEY_2=your_second_groq_api_key_here
GROQ_API_KEY_3=your_third_groq_api_key_here

# Module Toggles
FINSIGHT_ENABLED=true
ARCHIVE_ENABLED=true
ASSISTANT_ENABLED=true

# Rate Limiting
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_BURST=10

# Database (optional for basic functionality)
DATABASE_URL=postgresql://user:password@localhost:5432/nocturnal_platform
REDIS_URL=redis://localhost:6379
```

### **Module Configuration**

Each module can be enabled/disabled independently:

```bash
# Enable only Assistant for R/SQL help
ASSISTANT_ENABLED=true
FINSIGHT_ENABLED=false
ARCHIVE_ENABLED=false

# Enable all modules for full platform
FINSIGHT_ENABLED=true
ARCHIVE_ENABLED=true
ASSISTANT_ENABLED=true
```

## 🎯 **Use Cases**

### **1. R/SQL Programming Help**
```bash
# Get R help
curl -X POST http://localhost:8000/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I filter data in R using dplyr?"}'

# Get SQL help
curl -X POST http://localhost:8000/api/v1/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I write a complex JOIN query?"}'
```

### **2. Code Examples**
```bash
# Get R code example
curl "http://localhost:8000/api/v1/assistant/r-example?task=Create%20a%20scatter%20plot"

# Get SQL code example
curl "http://localhost:8000/api/v1/assistant/sql-example?task=Join%20two%20tables"
```

### **3. Cross-Module Search** (Future)
```bash
# Search across all modules
curl "http://localhost:8000/api/v1/unified/search?query=machine%20learning&modules=finsight,archive,assistant"
```

## 🏗️ **Architecture**

### **Unified Design**
```
┌─────────────────────────────────────────────────────────┐
│                 Nocturnal Platform                      │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   FinSight  │  │   Archive   │  │  Assistant  │     │
│  │ (Financial) │  │ (Research)  │  │   (R/SQL)   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Unified Services                       │ │
│  │  • Groq LLM Service (API key rotation)             │ │
│  │  • Rate Limiting & Security                        │ │
│  │  • Monitoring & Metrics                            │ │
│  │  • Cross-module Search & Analysis                  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### **Key Features**
- **🔄 API Key Rotation**: Automatic Groq API key rotation for reliability
- **⚡ Rate Limiting**: Production-grade rate limiting and burst protection
- **📊 Monitoring**: Prometheus metrics and structured logging
- **🔒 Security**: Security headers and authentication
- **🎯 Modular**: Enable/disable modules independently
- **💰 Cost-Effective**: Free Groq tier for unlimited usage

## 🚀 **Deployment**

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### **Production Deployment**
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### **Railway Deployment**
```bash
# Railway will automatically detect FastAPI and deploy
# Just push to your Railway-connected repository
git push railway main
```

## 📈 **Monitoring & Metrics**

### **Health Checks**
- `GET /health` - Detailed health status
- `GET /status` - Platform statistics
- `GET /api/v1/assistant/status` - Module-specific status

### **Metrics**
- Request counts by module
- Response times
- Error rates
- Groq API key usage
- Rate limiting statistics

## 🔧 **Development**

### **Project Structure**
```
unified-platform/
├── src/
│   ├── main.py                 # Main FastAPI application
│   ├── config/
│   │   └── settings.py         # Unified configuration
│   ├── services/
│   │   └── groq_service.py     # Groq LLM service
│   ├── middleware/
│   │   ├── rate_limit.py       # Rate limiting
│   │   ├── monitoring.py       # Metrics & monitoring
│   │   └── security.py         # Security headers
│   └── routes/
│       ├── assistant.py        # R/SQL Assistant routes
│       ├── finsight.py         # FinSight routes (placeholder)
│       ├── archive.py          # Archive routes (placeholder)
│       └── unified.py          # Cross-module routes
├── requirements.txt            # Dependencies
├── env.example                 # Environment template
└── README.md                   # This file
```

### **Adding New Modules**
1. Create route file in `src/routes/`
2. Add configuration in `src/config/settings.py`
3. Include router in `src/main.py`
4. Add module-specific services if needed

## 🎯 **Beta Launch Strategy**

### **Phase 1: R/SQL Assistant (Week 1)**
- ✅ **Working Now**: R/SQL Assistant is fully functional
- 🎯 **Target**: Your R Studio classmates
- 📊 **Validation**: Proven market demand

### **Phase 2: FinSight Integration (Week 2)**
- 🔄 **Next**: Integrate FinSight financial data
- 🎯 **Target**: Finance students
- 💰 **Value**: SEC EDGAR data analysis

### **Phase 3: Archive Integration (Week 3)**
- 🔄 **Next**: Integrate Archive research platform
- 🎯 **Target**: Research students
- 📚 **Value**: Academic paper synthesis

### **Phase 4: Cross-Module Features (Week 4)**
- 🔄 **Next**: Unified search and analysis
- 🎯 **Target**: All students
- 🚀 **Value**: Combined insights

## 💡 **Why This Works**

### **1. Groq's Free Tier Advantage**
- **14,400 requests/day per key** (free!)
- **Multiple keys** for redundancy
- **No cost concerns** (Elon Musk backing)
- **High performance** (fast inference)

### **2. Proven Market Validation**
- **R/SQL Assistant** already impressed your professor
- **Terminal-based** approach works
- **Immediate value** for students

### **3. Unified Architecture**
- **Single deployment** (easier management)
- **Shared infrastructure** (cost optimization)
- **Cross-module features** (increased value)
- **Scalable design** (grow with demand)

## 🎉 **Getting Started**

1. **Get Groq API keys** (free at console.groq.com)
2. **Copy env.example to .env** and add your keys
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Run the platform**: `python src/main.py`
5. **Test R/SQL Assistant**: Use the chat endpoints
6. **Deploy to Railway**: Push to your repository

**You're ready to launch your unified AI platform! 🚀**

---

**Status**: Ready for beta launch with R/SQL Assistant  
**Next**: Integrate FinSight and Archive modules  
**Timeline**: 1 week to full unified platform
