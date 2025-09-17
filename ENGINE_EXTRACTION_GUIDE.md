# 🔄 Research Engine Extraction & Recycling Guide

## Overview
This guide explains how to extract and recycle the Nocturnal Archive research engine for other use cases. The engine is modular and can be adapted for various AI-powered research and analysis applications.

## 🏗️ Core Architecture Components

### 1. **Service Layer** (`src/services/`)
The heart of the engine - modular services that can be mixed and matched:

#### **LLM Service** (`src/services/llm_service/`)
- **Core Files to Extract:**
  - `llm_manager.py` - Central LLM orchestration
  - `model_dispatcher.py` - Multi-provider routing
  - `usage_tracker.py` - Cost and usage monitoring
  - `api_clients/` - Provider-specific clients (Mistral, Cerebras, Cohere)

- **Use Cases:**
  - Any application needing multi-LLM support
  - Cost optimization across providers
  - Fallback mechanisms for reliability

#### **Research Service** (`src/services/research_service/`)
- **Core Files to Extract:**
  - `synthesizer.py` - Document synthesis and analysis
  - `context_manager.py` - Research context management
  - `enhanced_synthesizer.py` - Advanced synthesis capabilities

- **Use Cases:**
  - Document analysis and summarization
  - Knowledge synthesis from multiple sources
  - Research paper processing

#### **Search Service** (`src/services/search_service/`)
- **Core Files to Extract:**
  - `search_engine.py` - Vector and semantic search
  - `vector_search.py` - FAISS-based vector operations
  - `rerank/` - Result reranking algorithms

- **Use Cases:**
  - Semantic document search
  - RAG (Retrieval-Augmented Generation) systems
  - Knowledge base search

### 2. **Storage Layer** (`src/storage/`)
Database and caching infrastructure:

#### **Database Operations** (`src/storage/db/`)
- **Core Files to Extract:**
  - `operations.py` - Database CRUD operations
  - `models.py` - Pydantic data models
  - `connections.py` - Database connection management

- **Use Cases:**
  - Any application needing structured data storage
  - Document metadata management
  - Session and user data persistence

### 3. **Configuration System** (`src/config/`)
- **Core Files to Extract:**
  - `api_config.json` - Service configuration
  - `env_loader.py` - Environment variable management

- **Use Cases:**
  - Multi-service configuration management
  - Environment-based deployment
  - API key and credential management

## 🎯 Extraction Strategies by Use Case

### **Strategy 1: Minimal LLM Service**
For simple applications needing just LLM capabilities:

**Files to Extract:**
```
src/services/llm_service/
├── llm_manager.py
├── model_dispatcher.py
├── usage_tracker.py
└── api_clients/
    ├── mistral_client.py
    ├── cerebras_client.py
    └── cohere_client.py

src/config/
├── api_config.json
└── env_loader.py

src/utils/
└── logger.py
```

**Dependencies:**
- `requirements.txt` (LLM-related packages only)
- Environment variables for API keys

### **Strategy 2: Research & Analysis Engine**
For document analysis and research applications:

**Files to Extract:**
```
src/services/
├── llm_service/ (entire directory)
├── research_service/
│   ├── synthesizer.py
│   ├── context_manager.py
│   └── enhanced_synthesizer.py
└── search_service/
    ├── search_engine.py
    └── vector_search.py

src/storage/db/
├── operations.py
├── models.py
└── connections.py

src/config/ (entire directory)
```

### **Strategy 3: Full Research Platform**
For complete research management systems:

**Files to Extract:**
```
src/ (entire directory)
```

## 🔧 Migration Steps

### **Step 1: Environment Setup**
1. **Copy Configuration:**
   ```bash
   cp src/config/api_config.json your_project/config/
   cp src/config/env_loader.py your_project/config/
   ```

2. **Update Environment Variables:**
   ```bash
   # Copy relevant API keys
   MISTRAL_API_KEY=your_key
   CEREBRAS_API_KEY=your_key
   COHERE_API_KEY=your_key
   MONGODB_URL=your_mongodb_url
   REDIS_URL=your_redis_url
   ```

### **Step 2: Dependency Management**
1. **Extract Required Packages:**
   ```bash
   # From requirements.txt, extract only what you need:
   pip install openai mistralai cohere langchain faiss-cpu redis pymongo
   ```

2. **Update Import Paths:**
   ```python
   # Change imports from:
   from src.services.llm_service.llm_manager import LLMManager
   
   # To your project structure:
   from your_project.services.llm_service.llm_manager import LLMManager
   ```

### **Step 3: Service Integration**
1. **Initialize Core Services:**
   ```python
   from your_project.services.llm_service.llm_manager import LLMManager
   from your_project.config.env_loader import load_config
   
   config = load_config()
   llm_manager = LLMManager(
       redis_url=config["redis_url"],
       db_ops=None  # Optional
   )
   ```

2. **Adapt for Your Use Case:**
   ```python
   # Example: Simple document analysis
   async def analyze_document(text: str):
       response = await llm_manager.generate_response(
           prompt=f"Analyze this document: {text}",
           model_type="synthesis"
       )
       return response
   ```

## 🎨 Customization Patterns

### **Pattern 1: Chatbot Integration**
```python
# Extract: llm_manager.py, model_dispatcher.py
class YourChatbot:
    def __init__(self):
        self.llm_manager = LLMManager(redis_url="redis://localhost:6379")
    
    async def chat(self, message: str):
        return await self.llm_manager.generate_response(message)
```

### **Pattern 2: Document Processing**
```python
# Extract: synthesizer.py, llm_manager.py
class DocumentProcessor:
    def __init__(self):
        self.synthesizer = ResearchSynthesizer(db_ops, llm_manager, redis_url)
    
    async def process_document(self, content: str):
        return await self.synthesizer.synthesize_papers([content])
```

### **Pattern 3: Search & Retrieval**
```python
# Extract: search_engine.py, vector_search.py
class KnowledgeSearch:
    def __init__(self):
        self.search_engine = SearchEngine(db_ops, redis_url)
    
    async def search(self, query: str):
        return await self.search_engine.search_papers(query)
```

## 📦 Package Structure for New Projects

### **Minimal Package:**
```
your_project/
├── services/
│   └── llm_service/
│       ├── __init__.py
│       ├── llm_manager.py
│       └── model_dispatcher.py
├── config/
│   ├── __init__.py
│   └── api_config.json
└── requirements.txt
```

### **Full Package:**
```
your_project/
├── services/
│   ├── llm_service/
│   ├── research_service/
│   └── search_service/
├── storage/
│   └── db/
├── config/
├── utils/
└── requirements.txt
```

## 🔄 Adaptation Guidelines

### **1. Configuration Adaptation**
- Update `api_config.json` for your LLM providers
- Modify environment variable names if needed
- Adjust model priorities and fallback chains

### **2. Data Model Adaptation**
- Modify `models.py` for your data structures
- Update database schemas in `operations.py`
- Adapt to your storage requirements

### **3. Service Integration**
- Implement your specific business logic
- Add custom validation and processing
- Integrate with your existing systems

### **4. Error Handling**
- Adapt error messages for your domain
- Implement your logging and monitoring
- Add custom retry and fallback logic

## 🚀 Quick Start Templates

### **Template 1: Simple LLM Service**
```python
# main.py
from services.llm_service.llm_manager import LLMManager
from config.env_loader import load_config

async def main():
    config = load_config()
    llm = LLMManager(config["redis_url"])
    
    response = await llm.generate_response("Hello, world!")
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### **Template 2: Document Analysis Service**
```python
# document_analyzer.py
from services.research_service.synthesizer import ResearchSynthesizer
from services.llm_service.llm_manager import LLMManager

class DocumentAnalyzer:
    def __init__(self):
        self.llm_manager = LLMManager("redis://localhost:6379")
        self.synthesizer = ResearchSynthesizer(None, self.llm_manager, "redis://localhost:6379")
    
    async def analyze(self, documents: list):
        return await self.synthesizer.synthesize_papers(documents)
```

## 📋 Extraction Checklist

### **Pre-Extraction:**
- [ ] Identify your specific use case
- [ ] Determine which services you need
- [ ] Plan your project structure
- [ ] Set up your development environment

### **During Extraction:**
- [ ] Copy required files and directories
- [ ] Update import paths
- [ ] Modify configuration files
- [ ] Install required dependencies
- [ ] Test basic functionality

### **Post-Extraction:**
- [ ] Adapt data models for your use case
- [ ] Implement your business logic
- [ ] Add custom error handling
- [ ] Set up monitoring and logging
- [ ] Deploy and test in production

## 🎯 Use Case Examples

### **1. Customer Support Chatbot**
- Extract: `llm_manager.py`, `model_dispatcher.py`
- Adapt: Add customer service prompts and context
- Integrate: With your ticketing system

### **2. Legal Document Analysis**
- Extract: `synthesizer.py`, `llm_manager.py`, `search_engine.py`
- Adapt: Add legal-specific processing and validation
- Integrate: With document management systems

### **3. Content Generation Platform**
- Extract: `llm_manager.py`, `usage_tracker.py`
- Adapt: Add content templates and style guides
- Integrate: With CMS and publishing systems

### **4. Research Assistant**
- Extract: Full research service stack
- Adapt: Add domain-specific knowledge bases
- Integrate: With academic databases and APIs

## 🔧 Troubleshooting

### **Common Issues:**
1. **Import Errors:** Update all import paths to match your project structure
2. **Configuration Issues:** Verify environment variables and API keys
3. **Database Connection:** Ensure MongoDB and Redis are running
4. **Dependency Conflicts:** Use virtual environments and pin package versions

### **Performance Optimization:**
1. **Caching:** Leverage Redis for response caching
2. **Async Operations:** Use async/await for I/O operations
3. **Connection Pooling:** Configure database connection pools
4. **Model Selection:** Choose appropriate models for your use case

This guide provides a comprehensive framework for extracting and recycling the research engine components for various use cases. The modular architecture makes it easy to pick and choose the components you need while maintaining the robust error handling and performance optimizations built into the original system.
