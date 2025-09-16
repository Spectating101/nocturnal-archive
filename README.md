# Nocturnal Archive

**AI-Powered Academic Research Platform**

A comprehensive research automation system that combines advanced AI with academic databases to provide intelligent literature reviews, citation analysis, and knowledge synthesis.

## 🚀 Live Demo

**Frontend:** [nocturnal-archive-frontend.vercel.app](https://nocturnal-archive-frontend.vercel.app)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Supabase)    │
│   Vercel        │    │   Railway       │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
Nocturnal-Archive/
├── chatbot-ui/              # Next.js frontend application
│   ├── app/                 # App router pages and API routes
│   ├── components/          # React components
│   ├── lib/                 # Utilities and configurations
│   └── supabase/           # Database schema and migrations
├── src/                     # FastAPI backend application
├── deployment/              # Deployment configurations
├── monitoring/              # Monitoring and observability
├── nginx/                   # Web server configuration
├── rust_performance/        # Performance optimization modules
```

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Supabase** - Database and authentication
- **Vercel** - Deployment and hosting

### Backend
- **FastAPI** - High-performance Python API
- **Python 3.11+** - Core language
- **Pydantic** - Data validation
- **Railway** - Backend hosting

### Database
- **Supabase** - PostgreSQL with real-time features
- **Row Level Security** - Data protection
- **Real-time subscriptions** - Live updates

## 🚀 Quick Start

### Frontend Development
```bash
cd chatbot-ui
npm install
npm run dev
```

### Backend Development
```bash
cd src
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 🔧 Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_BACKEND_URL=your_backend_url
```

### Backend
```env
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_key
```

## 📊 Features

- **Intelligent Research** - AI-powered literature analysis
- **Citation Management** - Automated reference tracking
- **Real-time Collaboration** - Multi-user research sessions
- **Knowledge Synthesis** - Cross-paper insights
- **Academic Database Integration** - arXiv, PubMed, etc.

## 🔒 Security

- Row-level security in Supabase
- Environment variable protection
- CORS configuration
- API rate limiting

## 📈 Deployment Status

- ✅ **Frontend**: Deployed on Vercel
- ✅ **Database**: Configured on Supabase
- 🔄 **Backend**: Ready for Railway deployment
- 🔄 **Monitoring**: Sentry integration pending

## 🤝 Contributing

This is a private research project. For access or collaboration, please contact the maintainer.

## 📄 License

Private - All rights reserved

---

**Status**: Beta - In active development
**Last Updated**: September 2024
