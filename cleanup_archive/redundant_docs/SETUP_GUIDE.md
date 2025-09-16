# Nocturnal Archive - Setup Guide

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for web interface)
- **Docker** (for database services)
- **Git**

### 2. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Nocturnal-Archive

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp env.example .env.local

# Edit .env.local with your API keys
nano .env.local
```

**Required API Keys:**
- `MISTRAL_API_KEY` - Get from [Mistral AI](https://console.mistral.ai/)
- `COHERE_API_KEY` - Get from [Cohere](https://cohere.ai/)
- `CEREBRAS_API_KEY` - Get from [Cerebras](https://www.cerebras.net/)

### 4. Database Setup

```bash
# Start database services
docker-compose up -d redis mongodb

# Verify services are running
docker-compose ps
```

### 5. Test the System

```bash
# Run demo mode
python launch_enhanced_system.py demo

# Run interactive mode
python launch_enhanced_system.py interactive

# Launch web interface
python launch_enhanced_system.py web
```

## 🔧 Advanced Configuration

### Database URLs

```bash
# MongoDB
MONGO_URL=mongodb://localhost:27017/nocturnal_archive

# Redis
REDIS_URL=redis://localhost:6379

# Optional: Qdrant (vector search)
QDANT_URL=http://localhost:6333

# Optional: Neo4j (knowledge graph)
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### System Configuration

```bash
# Research settings
MAX_RESEARCH_TIME=300        # Maximum research time in seconds
MAX_PAPERS_PER_QUERY=20      # Maximum papers to analyze
CACHE_TTL=3600              # Cache time-to-live in seconds

# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
```

## 🌐 Web Interface Setup

```bash
# Navigate to web interface directory
cd chatbot-ui

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔍 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **Database connection errors**
   - Verify Docker services are running: `docker-compose ps`
   - Check environment variables in `.env.local`

3. **API key errors**
   - Verify API keys are correctly set in `.env.local`
   - Check API key permissions and quotas

4. **Port conflicts**
   - Change ports in `docker-compose.yml` if needed
   - Check for existing services using the same ports

### Logs and Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View system logs
tail -f logs/nocturnal_archive.log

# Test individual components
python -c "from src.services.llm_service.llm_manager import LLMManager; print('LLM Manager OK')"
```

## 📊 System Status

### Health Check

```bash
# Run system health check
python launch_enhanced_system.py demo

# Expected output:
# ✅ Enhanced system initialized successfully
# ✅ Enhanced research completed
# ✅ Demo completed successfully!
```

### Performance Monitoring

- **Memory Usage**: Monitor with `htop` or `docker stats`
- **API Usage**: Check API provider dashboards
- **Database Performance**: Monitor with MongoDB Compass

## 🚀 Production Deployment

### Environment Variables

```bash
# Production settings
LOG_LEVEL=WARNING
MAX_RESEARCH_TIME=600
CACHE_TTL=7200

# Security
ENABLE_RATE_LIMITING=true
ENABLE_CORS=true
```

### Security Considerations

1. **API Keys**: Store securely, rotate regularly
2. **Database**: Use strong passwords, enable authentication
3. **Network**: Use HTTPS, configure firewalls
4. **Monitoring**: Set up alerts for system health

## 📚 Next Steps

1. **Customize Research Sources**: Modify paper retrieval services
2. **Add Custom Visualizations**: Extend visualization capabilities
3. **Integrate with External Systems**: Connect to existing workflows
4. **Scale Infrastructure**: Add load balancing and caching

## 🆘 Support

- **Documentation**: Check `README.md` for detailed information
- **Issues**: Report bugs on GitHub
- **Community**: Join discussions in project forums

---

**Nocturnal Archive is now ready for production use!** 🎉
