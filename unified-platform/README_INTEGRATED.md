# 🌙 Nocturnal Platform - Integrated Server

**The unified platform combining RStudio Extension's proven Groq service with unified platform features.**

## 🎯 **What's Ready Now**

### ✅ **Working Immediately**
- **R/SQL Assistant**: Full Groq integration with API key rotation
- **Unified API**: Single FastAPI server with all endpoints
- **Production Features**: Rate limiting, monitoring, error handling
- **Easy Deployment**: Simple setup with Railway or local

### 🚧 **Coming Soon**
- **FinSight Module**: Financial data analysis
- **Archive Module**: Academic research platform
- **Cross-module Search**: Unified search across all modules

## 🚀 **Quick Start**

### **1. Add Your Groq API Key**
```bash
# Copy the template
cp env_simple.txt .env

# Edit .env and add your Groq key
nano .env
# Change: GROQ_API_KEY_1=your_groq_api_key_here
```

### **2. Run the Server**
```bash
# Make it executable and run
chmod +x run_integrated.sh
./run_integrated.sh
```

### **3. Test the API**
```bash
# Health check
curl http://localhost:8000/health

# R/SQL Assistant
curl -X POST http://localhost:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I create a scatter plot in R?"}'
```

## 📊 **API Endpoints**

### **Core Platform**
- `GET /` - Platform overview
- `GET /health` - Health check
- `GET /status` - Detailed status

### **Assistant Module (R/SQL)**
- `POST /assistant/chat` - Chat assistance
- `GET /assistant/chat` - Chat assistance (GET)
- `GET /assistant/status` - Assistant status

### **Unified Module**
- `POST /unified/search` - Cross-module search
- `GET /unified/search` - Cross-module search (GET)

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required
GROQ_API_KEY_1=sk-your-groq-key-here

# Optional
GROQ_API_KEY_2=sk-second-key-here
GROQ_API_KEY_3=sk-third-key-here
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### **API Key Management**
- **Automatic rotation**: Uses multiple keys for redundancy
- **Rate limiting**: 30 requests/minute per key
- **Daily limits**: 14,400 requests/day per key (Groq free tier)
- **Health monitoring**: Tracks key health and errors

## 🎯 **What Makes This Special**

### **1. Proven Foundation**
- ✅ **RStudio Extension's Groq service** (battle-tested)
- ✅ **API key rotation** (production-ready)
- ✅ **Simple deployment** (Railway proven)

### **2. Unified Platform Features**
- ✅ **Production middleware** (rate limiting, monitoring)
- ✅ **Unified API structure** (consistent endpoints)
- ✅ **Error handling** (graceful failures)
- ✅ **Request tracking** (usage statistics)

### **3. Groq Integration**
- ✅ **Free tier advantage** (14,400 requests/day per key)
- ✅ **Multiple key support** (redundancy and load balancing)
- ✅ **Intelligent responses** (understands R, SQL, and more)

## 🚀 **Deployment Options**

### **Local Development**
```bash
./run_integrated.sh
```

### **Railway Deployment**
```bash
# Push to Railway
git add .
git commit -m "Deploy integrated Nocturnal Platform"
git push railway main
```

### **Production Deployment**
```bash
# With Gunicorn
gunicorn integrated_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📈 **Usage Examples**

### **R Programming Help**
```bash
curl -X POST http://localhost:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I filter data in R using dplyr?"}'
```

### **SQL Help**
```bash
curl -X POST http://localhost:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I write a complex JOIN query?"}'
```

### **Code Examples**
```bash
curl -X POST http://localhost:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me how to create a bar chart in R with ggplot2"}'
```

## 🔍 **Monitoring**

### **Health Check**
```bash
curl http://localhost:8000/health
```

### **Status Check**
```bash
curl http://localhost:8000/status
```

### **Logs**
```bash
tail -f nocturnal_platform.log
```

## 🎯 **Next Steps**

### **Phase 1: R/SQL Assistant (Ready Now)**
- ✅ **Working**: R/SQL programming help
- ✅ **Deployed**: Ready for your classmates
- ✅ **Tested**: Proven with your professor

### **Phase 2: Add FinSight (Week 2)**
- 🔄 **Next**: Financial data analysis
- 🔄 **Integration**: SEC EDGAR data
- 🔄 **Features**: Financial metrics and insights

### **Phase 3: Add Archive (Week 3)**
- 🔄 **Next**: Academic research platform
- 🔄 **Integration**: OpenAlex and research papers
- 🔄 **Features**: Research synthesis and citations

### **Phase 4: Cross-Module Features (Week 4)**
- 🔄 **Next**: Unified search and analysis
- 🔄 **Integration**: Connect all modules
- 🔄 **Features**: Cross-module insights

## 🎉 **Ready to Launch!**

**Your integrated Nocturnal Platform is ready!**

1. **Add your Groq API key** to `.env`
2. **Run the server** with `./run_integrated.sh`
3. **Test with your classmates** using the R/SQL Assistant
4. **Deploy to Railway** for production use

**The R/SQL Assistant is working immediately, and you can add FinSight and Archive modules incrementally!**

---

**Status**: Ready for beta launch with R/SQL Assistant  
**Next**: Add your Groq key and start testing!  
**Timeline**: 1 week to full unified platform
