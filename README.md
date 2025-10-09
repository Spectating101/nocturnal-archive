# Cite-Agent

> A fast, affordable AI research assistant with built-in citation capabilities

**Cite-Agent** is a terminal-based AI assistant designed for research and finance, offering 70B model access at half the cost of comparable services.

---

## 🎯 What is Cite-Agent?

Cite-Agent is an AI-powered research tool that:
- Answers complex questions using state-of-the-art 70B language models
- Provides accurate, source-grounded responses (hence "cite")
- Executes code (Python, R, SQL) for data analysis
- Operates through a beautiful terminal interface
- Costs $10/month (vs $20+ for Claude/ChatGPT)

---

## ✨ Key Features

### 🧠 **Powerful AI**
- Access to Llama 3.3 70B via Cerebras & Groq
- Multi-provider fallback for 99.9% uptime
- 50 queries/day (50,000 tokens)
- 2-5 second response times

### 🎓 **Truth-Seeking**
- Explicitly designed to correct user errors
- Admits uncertainty instead of guessing
- Cites sources and reasoning
- Anti-appeasement prompts

### 💻 **Code Execution**
- Python, R, and SQL support
- Data analysis and visualization
- Financial calculations
- Research automation

### 🔒 **Secure & Private**
- API keys never leave the backend
- JWT-based authentication
- Rate limiting per user
- HTTPS-only communication

### 📊 **Analytics**
- Track your usage
- Monitor token consumption
- View query history
- Download statistics

---

## 💰 Pricing

| Plan | Price | Queries/Day | Features |
|------|-------|-------------|----------|
| **Student** | $10/month (300 NTD) | 50 | Full access |
| **Public** | $10/month (400 NTD) | 50 | Full access |

**Beta**: First 50 users get 3 months free

---

## 🚀 Quick Start

### For Users

1. **Download** for your OS:
   - [Windows](https://cite-agent-api.herokuapp.com/api/downloads/windows)
   - [macOS](https://cite-agent-api.herokuapp.com/api/downloads/macos)
   - [Linux](https://cite-agent-api.herokuapp.com/api/downloads/linux)

2. **Install** the downloaded package

3. **Run** `cite-agent` in your terminal

4. **Register** with email + password

5. **Start asking questions!**

### For Developers

See [DEVELOPMENT.md](./docs/DEVELOPMENT.md) for setup instructions.

---

## 🏗️ Architecture

```
User's Machine                Backend (Heroku)              AI Providers
┌─────────────┐              ┌──────────────┐              ┌──────────┐
│             │              │              │              │          │
│   Terminal  │─────────────▶│   FastAPI    │─────────────▶│ Cerebras │
│     UI      │              │     API      │              │  (70B)   │
│             │◀─────────────│              │◀─────────────│          │
│   (cite_    │              │  - Auth      │              └──────────┘
│   agent/)   │              │  - Rate      │              
│             │              │    Limiting  │              ┌──────────┐
└─────────────┘              │  - Analytics │              │          │
                             │  - Proxy     │─────────────▶│   Groq   │
                             │              │              │  (70B)   │
                             └──────────────┘              │          │
                                    │                      └──────────┘
                             ┌──────────────┐
                             │  PostgreSQL  │
                             │   Database   │
                             └──────────────┘
```

### Components

**Frontend (cite_agent/)**
- Terminal UI using `rich` library
- JWT authentication
- Query management
- Local session storage

**Backend (cite-agent-api/)**
- FastAPI REST API
- User authentication & rate limiting
- Multi-provider LLM routing
- Analytics & tracking
- PostgreSQL database

**AI Providers**
- **Primary**: Cerebras (14,400 RPD × 3 keys = 43,200/day)
- **Backup**: Groq (1,000 RPD × 3 keys = 3,000/day)
- **Total capacity**: ~46,000 queries/day

---

## 📖 Documentation

- **[DEVELOPMENT.md](./docs/DEVELOPMENT.md)** - Developer setup guide
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - How to deploy (Heroku)
- **[API_REFERENCE.md](./docs/API_REFERENCE.md)** - API endpoints
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design details
- **[ROADMAP.md](./ROADMAP.md)** - Future plans

---

## 🛠️ Tech Stack

**Frontend**
- Python 3.13+
- `rich` for terminal UI
- `httpx` for async HTTP
- `pydantic` for data validation

**Backend**
- FastAPI
- PostgreSQL
- JWT authentication
- Multi-provider LLM integration

**AI Providers**
- Cerebras Inference API
- Groq Cloud
- Cloudflare Workers AI (fallback)
- OpenRouter (fallback)

**Deployment**
- Heroku (backend + database)
- GitHub Releases (installers)

---

## 🤝 Contributing

We're not accepting contributions yet (private beta), but stay tuned!

---

## 📜 License

Proprietary - All rights reserved

---

## 📧 Support

- **Email**: s1133958@mail.yzu.edu.tw
- **Issues**: Coming soon
- **Documentation**: See `/docs` directory

---

## 🙏 Acknowledgments

- **Cerebras** for generous free tier (14,400 RPD)
- **Groq** for fast 70B inference
- **GitHub Student Pack** for free hosting credits
- **FastAPI** for excellent async framework

---

**Built with ❤️ for researchers and analysts**

*Cite-Agent - Because accuracy matters more than agreeableness*
