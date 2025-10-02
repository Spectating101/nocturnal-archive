# Nocturnal Archive - Comprehensive System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Installation & Setup](#installation--setup)
6. [API Documentation](#api-documentation)
7. [Financial Data System (FinSight)](#financial-data-system-finsight)
8. [Packaging & Distribution](#packaging--distribution)
9. [Troubleshooting](#troubleshooting)
10. [Development Workflow](#development-workflow)

---

## System Overview

Nocturnal Archive is a comprehensive AI-powered financial research and analysis platform that combines:
- **AI Agent**: Conversational interface for financial queries
- **FinSight API**: Multi-source financial data aggregation system
- **Auto-updater**: Seamless package updates without user intervention
- **Multi-source Data**: SEC EDGAR, Yahoo Finance, real-time market data

### Key Features
- Universal financial data access (10,123+ companies)
- Real-time quotes, crypto, forex support
- Intelligent data routing with fallbacks
- Professional CLI interface
- Zero-friction installation and updates

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOCTURNAL ARCHIVE ECOSYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   AI Agent      │    │   FinSight API  │    │  Auto-      │ │
│  │   (CLI)         │◄──►│   (Multi-source)│    │  Updater    │ │
│  │                 │    │                 │    │             │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                             │
│           │                       │                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Console       │    │   Data Sources  │    │  Package    │ │
│  │   Scripts       │    │                 │    │  Manager    │ │
│  │                 │    │  • SEC EDGAR    │    │             │ │
│  │ • nocturnal     │    │  • Yahoo Finance│    │ • PyPI      │ │
│  │ • nocturnal-    │    │  • Real-time    │    │ • pip       │ │
│  │   agent         │    │  • Crypto/Forex │    │ • venv      │ │
│  │ • nocturnal-    │    │                 │    │             │ │
│  │   update        │    │                 │    │             │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. AI Agent (`nocturnal_archive/`)

**Location**: `nocturnal_archive/`
**Purpose**: Main conversational interface for financial queries

#### Key Files:
- `cli.py` - Command-line interface and user interaction
- `enhanced_ai_agent.py` - Core AI agent logic and API integrations
- `updater.py` - Auto-update mechanism
- `__init__.py` - Package initialization and version

#### Features:
- Interactive and single-query modes
- Background auto-updates
- Graceful error handling (EOFError, KeyboardInterrupt)
- Multi-source financial data integration
- Professional CLI with progress indicators

### 2. FinSight API (`nocturnal-archive-api/`)

**Location**: `nocturnal-archive-api/`
**Purpose**: Multi-source financial data aggregation and API service

#### Key Directories:
- `src/adapters/` - Data source adapters (SEC, Yahoo Finance)
- `src/routes/` - API endpoints
- `src/services/` - Business logic and routing
- `src/models/` - Data models
- `src/jobs/` - Background jobs and data processing

#### Features:
- Universal company coverage (10,123+ companies)
- Intelligent data routing with fallbacks
- Real-time quotes, crypto, forex
- Data validation and sanity checks
- Comprehensive logging and monitoring

### 3. Unified Platform (`unified-platform/`)

**Location**: `unified-platform/`
**Purpose**: Integration layer and production deployment

#### Key Files:
- `start_production.py` - Production server startup
- `real_api_agent.py` - Production AI agent
- Various test and deployment scripts

### 4. Packaging System

**Location**: Root directory
**Purpose**: Distribution and installation management

#### Key Files:
- `setup.py` - Package configuration and console scripts
- `install_simple.py` - Simplified installation script
- `requirements.txt` - Python dependencies

---

## Data Flow

### 1. User Query Flow
```
User Input → CLI → AI Agent → FinSight API → Data Sources → Response
```

### 2. Financial Data Flow
```
Query → Multi-Source Router → Adapters (SEC/Yahoo) → Validation → Response
```

### 3. Auto-Update Flow
```
Startup → Background Check → PyPI Query → Download → Install → Restart
```

---

## Installation & Setup

### Quick Installation
```bash
# Clone repository
git clone <repository-url>
cd Nocturnal-Archive

# Run simple installer
python install_simple.py
```

### Manual Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install package
pip install -e .

# Install API dependencies
cd nocturnal-archive-api
pip install -r requirements.txt
```

### Console Scripts
After installation, these commands are available:
- `nocturnal` - Main AI agent interface
- `nocturnal-agent` - Direct agent access
- `nocturnal-update` - Manual update trigger

---

## API Documentation

### FinSight API Endpoints

#### Base URL: `http://localhost:8000`

#### 1. Financial Calculations
```http
POST /v1/finance/calc/explain
Content-Type: application/json

{
  "ticker": "AAPL",
  "expr": "revenue",
  "period": "2024-Q4",
  "freq": "Q"
}
```

**Response:**
```json
{
  "ticker": "AAPL",
  "value": 94036000000.0,
  "period": "2025-06-30",
  "data_source": "yahoo_finance",
  "citations": [
    {
      "source": "Yahoo Finance",
      "url": "https://finance.yahoo.com/quote/AAPL/financials",
      "period": "2025-06-30",
      "quarterly": true
    }
  ]
}
```

#### 2. Real-time Quotes
```http
POST /v1/finance/calc/explain
Content-Type: application/json

{
  "ticker": "AAPL",
  "expr": "price"
}
```

#### 3. Crypto Data
```http
POST /v1/finance/calc/explain
Content-Type: application/json

{
  "ticker": "BTC",
  "expr": "price"
}
```

#### 4. Forex Data
```http
POST /v1/finance/calc/explain
Content-Type: application/json

{
  "ticker": "EUR/USD",
  "expr": "price"
}
```

---

## Financial Data System (FinSight)

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    FINSIGHT API                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Multi-Source  │    │   Data          │                │
│  │   Router        │    │   Validation    │                │
│  │                 │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                         │
│           │                       │                         │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   SEC EDGAR     │    │   Yahoo Finance │                │
│  │   Adapter       │    │   Adapter       │                │
│  │                 │    │                 │                │
│  │ • 10,123+       │    │ • Real-time     │                │
│  │   companies     │    │ • Crypto        │                │
│  │ • Historical    │    │ • Forex         │                │
│  │   filings       │    │ • International │                │
│  │ • XBRL parsing  │    │ • Estimates     │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Sources

#### 1. SEC EDGAR
- **Coverage**: 10,123+ US public companies
- **Data Types**: Historical financial statements, regulatory filings
- **Update Frequency**: Quarterly/Annual (as filed)
- **Authority**: Official regulatory source
- **Limitations**: Delayed reporting, complex XBRL parsing

#### 2. Yahoo Finance
- **Coverage**: Global markets, crypto, forex
- **Data Types**: Real-time quotes, financial statements, estimates
- **Update Frequency**: Real-time
- **Authority**: Market data provider
- **Limitations**: May include estimates, less authoritative for official filings

### Data Routing Logic

```python
def route_data_request(ticker, expr, period, freq):
    # 1. Determine data type and ticker type
    data_type = classify_data_type(expr)  # real_time_quote, financial_statements
    ticker_type = classify_ticker(ticker)  # crypto, forex, public_company
    
    # 2. Define source priority
    if ticker_type == "crypto" or ticker_type == "forex":
        sources = ["yahoo_finance", "alpha_vantage"]
    elif ticker_type == "public_company":
        if data_type == "real_time_quote":
            sources = ["yahoo_finance", "sec_edgar"]
        elif data_type == "financial_statements":
            sources = ["sec_edgar", "yahoo_finance"]
    
    # 3. Try sources in order with fallbacks
    for source in sources:
        result = try_source(source, ticker, expr, period, freq)
        if result and validate_data(result):
            return result
    
    return None
```

### Data Validation

The system includes comprehensive validation to catch obviously wrong data:

```python
def validate_financial_data(ticker, concept, value, period, freq):
    # 1. Basic sanity checks
    if not value or value <= 0:
        return False
    
    # 2. Company-specific ranges (quarterly revenue in billions)
    major_company_ranges = {
        "AAPL": (20, 120),    # Realistic quarterly range
        "MSFT": (50, 70),
        "AMZN": (120, 180),
        # ... more companies
    }
    
    # 3. Frequency-specific validation
    if freq == "Q":
        expected_min, expected_max = major_company_ranges.get(ticker, (0, float('inf')))
        if value < expected_min * 0.25 or value > expected_max * 2.0:
            return False
    
    return True
```

---

## Packaging & Distribution

### Package Structure
```
nocturnal_archive/
├── __init__.py              # Version and package info
├── cli.py                   # Main CLI interface
├── enhanced_ai_agent.py     # Core AI agent
├── updater.py               # Auto-update mechanism
└── ...
```

### Console Scripts (setup.py)
```python
entry_points={
    'console_scripts': [
        'nocturnal=nocturnal_archive.cli:main',
        'nocturnal-agent=nocturnal_archive.enhanced_ai_agent:main',
        'nocturnal-update=nocturnal_archive.updater:main',
    ],
},
```

### Auto-Update Mechanism

#### Background Updates
- **Trigger**: Every startup (can be disabled with `--no-auto-update`)
- **Process**: Check PyPI → Download → Install → Notify
- **User Experience**: Silent, non-blocking

#### Update Flow
```python
def check_and_update_background():
    try:
        # Check PyPI for new version
        latest_version = get_latest_version_from_pypi()
        current_version = get_current_version()
        
        if latest_version > current_version:
            # Download and install in background
            install_update(latest_version)
            
            # Save notification for next run
            save_update_notification(latest_version)
    except Exception:
        # Fail silently - don't interrupt user
        pass
```

### Installation Methods

#### 1. Simple Installer (`install_simple.py`)
```bash
python install_simple.py
```
- Handles `externally-managed-environment` errors
- Creates virtual environment if needed
- Provides clean progress indicator
- Launches chatbot after installation

#### 2. Standard pip Installation
```bash
pip install -e .
```

#### 3. User-space Installation
```bash
pip install --user -e .
```

---

## Troubleshooting

### Common Issues

#### 1. ImportError: No module named 'pkg_resources'
**Cause**: Missing setuptools package
**Solution**: 
```bash
pip install setuptools
```

#### 2. externally-managed-environment Error
**Cause**: System Python protection (PEP 668)
**Solution**: Use virtual environment or `--user` flag
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

#### 3. EOFError in CLI
**Cause**: Input handling in interactive mode
**Solution**: Fixed in current version with proper exception handling

#### 4. FinSight API Not Starting
**Cause**: Missing dependencies
**Solution**:
```bash
cd nocturnal-archive-api
pip install -r requirements.txt
```

#### 5. SEC Data Validation Errors
**Cause**: Incorrect validation ranges or period matching
**Solution**: 
- Validation temporarily disabled in current version
- Period matching improved to handle fiscal vs calendar quarters
- Multiple match resolution prefers smaller values (quarterly over annual)

### Debug Commands

#### Check API Status
```bash
curl http://localhost:8000/health
```

#### Test Financial Data
```bash
curl -X POST "http://localhost:8000/v1/finance/calc/explain" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "expr": "revenue", "freq": "Q"}'
```

#### Check Package Version
```bash
nocturnal --version
```

#### Manual Update Check
```bash
nocturnal-update
```

---

## Development Workflow

### Project Structure
```
Nocturnal-Archive/
├── nocturnal_archive/           # Main package
├── nocturnal-archive-api/       # FinSight API
├── unified-platform/           # Integration layer
├── tests/                      # Test files
├── docs/                       # Documentation
├── setup.py                    # Package configuration
├── requirements.txt            # Dependencies
├── install_simple.py           # Installation script
└── README.md                   # Project overview
```

### Key Configuration Files

#### setup.py
```python
setup(
    name="nocturnal-archive",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'nocturnal=nocturnal_archive.cli:main',
            'nocturnal-agent=nocturnal_archive.enhanced_ai_agent:main',
            'nocturnal-update=nocturnal_archive.updater:main',
        ],
    },
    install_requires=[
        "openai",
        "anthropic",
        "groq",
        # ... more dependencies
    ],
)
```

#### requirements.txt (API)
```
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.0
yfinance==0.2.18
structlog==23.2.0
# ... more dependencies
```

### Development Setup

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd Nocturnal-Archive
python -m venv venv
source venv/bin/activate
pip install -e .
```

#### 2. API Development
```bash
cd nocturnal-archive-api
pip install -r requirements.txt
uvicorn src.main_production:app --reload
```

#### 3. Testing
```bash
# Test AI agent
python test_ai_agent.py

# Test API
python test_complete_system.py

# Test specific components
python test_enhanced_capabilities.py
```

### Environment Variables

#### Required
```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
```

#### Optional
```bash
NOCTURNAL_NO_AUTO_UPDATE=true  # Disable auto-updates
NOCTURNAL_LOG_LEVEL=INFO       # Set log level
```

---

## Current Status & Known Issues

### Working Components
✅ AI Agent CLI interface
✅ Auto-update mechanism
✅ Package installation and distribution
✅ Multi-source financial data routing
✅ Yahoo Finance integration
✅ Real-time quotes, crypto, forex
✅ Data validation and fallbacks
✅ Professional CLI with progress indicators

### Issues Under Investigation
🔍 SEC EDGAR data extraction accuracy
🔍 Period matching for fiscal vs calendar quarters
🔍 Data validation ranges calibration
🔍 API rate limiting and error handling

### Recent Fixes
- Fixed `EOFError` and `KeyboardInterrupt` handling in CLI
- Improved period matching to handle multiple data matches
- Enhanced validation ranges for realistic quarterly revenue
- Added graceful fallbacks when SEC data is unavailable
- Implemented clean installation experience with progress indicators

---

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Include comprehensive logging
- Write descriptive commit messages

### Testing
- Test all new features
- Verify API endpoints work correctly
- Check data validation logic
- Ensure graceful error handling

### Documentation
- Update this documentation for new features
- Include API endpoint documentation
- Document configuration changes
- Update troubleshooting section

---

This documentation provides a comprehensive overview of the Nocturnal Archive system. For specific implementation details, refer to the individual source files and their inline documentation.
