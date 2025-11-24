# 🔬 Auto-Research Agent 2.0

**AI-Powered Multi-Agent Research Platform with Streamlit Web Interface**

> 🌟 **NEW**: Complete web application with authentication, subscription tiers, and real-time research workflow!

---

## 📌 Overview

Auto-Research Agent 2.0 is an autonomous AI research platform that performs comprehensive research on any topic. The system uses 9 specialized AI agents working together to search, analyze, verify facts, and generate professional reports with citations.

**What's New in v2.0:**
- ✨ **Streamlit Web UI** - Modern, responsive web interface
- 🔐 **User Authentication** - Secure login/signup with JWT tokens
- 💎 **Subscription Tiers** - Free (5 researches/day) and Premium (unlimited)
- 📊 **Real-time Dashboard** - Track usage, view history, manage settings
- 🚀 **3 Research Modes** - Quick, Standard, and Deep research
- 💾 **Smart Caching** - Instant results for repeated queries
- 📥 **Multi-format Export** - PDF, DOCX, Markdown downloads

---

## ✨ Key Features

### Core Research Capabilities
- 🤖 **9 AI Agents** - Query expansion, search, summarization, fact-checking, writing, editing, citations
- 🔍 **Multi-Source Search** - Wikipedia, Brave Search, SerpAPI, Exa with automatic fallbacks
- ✅ **Fact Verification** - Cross-reference claims with confidence scoring
- 📚 **Smart Citations** - APA, MLA, Chicago formatting with inline references
- 📈 **Credibility Scoring** - Source reliability analysis (0-100 scale)
- 🔄 **Iterative Research** - Gap detection and progressive information gathering

### Web Application Features
- 🎨 **Modern Dark Theme** - Professional, eye-friendly interface
- 👤 **User Management** - Secure accounts with password hashing (bcrypt)
- 📊 **Usage Analytics** - Daily limits, cache stats, research history
- 🗂️ **Research History** - Download previous reports (MD, PDF, DOCX)
- ⚙️ **Settings Page** - Account info and premium upgrade options
- 📱 **Responsive Design** - Works on desktop and mobile

---

## 🆓 Free vs 💎 Premium

| Feature | Free Tier | Premium Tier |
|---------|-----------|--------------|
| **Daily Limit** | 5 researches | ♾️ Unlimited |
| **Research Modes** | Quick + Standard | Quick + Standard + **Deep** |
| **Max Sources** | 5 sources | 15+ sources |
| **Word Limit** | 2,000 words | 5,000+ words |
| **Export Formats** | PDF + Markdown | PDF + **DOCX** + Markdown |
| **Citations** | Basic | APA + MLA + Chicago |
| **Charts** | ❌ | ✅ Visualizations |
| **Priority** | Standard | Priority processing |
| **Cost** | **$0/month** | **$29/month** |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **API Keys** (get free keys in 5 minutes):
  - **Groq** (free): https://console.groq.com
  - **Google Gemini** (free): https://aistudio.google.com/apikey
  - **OpenAI** (optional, paid): https://platform.openai.com/api-keys

### Installation

**1. Clone Repository**
```powershell
git clone <your-repo-url>
cd "Auto Reasearch Agent"
```

**2. Run Setup Script**
```powershell
.\setup.ps1
```

This automatically:
- Creates virtual environment
- Installs all dependencies (streamlit, bcrypt, matplotlib, etc.)
- Sets up directory structure

**3. Configure API Keys**
```powershell
# Copy template
Copy-Item .env.example .env

# Edit .env and add your keys
notepad .env
```

Required keys:
```env
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=AIzaSy_your_key_here
```

Optional (for premium features):
```env
OPENAI_API_KEY=sk-proj-your_key_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

**4. Launch Application**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate

# Start Streamlit server
streamlit run app.py
```

The app opens at: **http://localhost:8501** 🎉

---

## 💻 Usage Guide

### 1️⃣ Create Account

- Click **"Sign Up"** tab
- Enter name, email, username, password
- Account created as **Free tier** by default

### 2️⃣ Login

- Enter username/email and password
- Access your personalized dashboard

### 3️⃣ Start Research

**Select Research Mode:**
- ⚡ **Quick** - Fast overview (2 sources, ~500 words, 30 sec)
- 📝 **Standard** - Balanced research (5 sources, ~2000 words, 2 min)
- 🔍 **Deep** - Comprehensive (15+ sources, 5000+ words, 5 min) *Premium only*

**Enter Query:**
```
Example: "Impact of artificial intelligence in healthcare"
```

**Watch Live Progress:**
- 📝 Query processing
- 💾 Cache check
- 🔎 Multi-source search
- 🎯 Credibility scoring
- 🤖 AI workflow execution
- ✅ Report generation

### 4️⃣ View Results

**Report Tab:**
- Full research report with citations
- Professional formatting

**Sources Tab:**
- View all sources with credibility scores
- Expandable details (URL, snippet)

**Statistics Tab:**
- Word count, sources used
- Coverage score, time elapsed
- Facts verified count

**Export Tab:**
- 📄 Download Markdown
- 📕 Download PDF
- 📘 Download DOCX *(Premium)*

### 5️⃣ Access History

- 📚 Navigate to **"History"** page
- View all past researches
- Download previous reports (MD, PDF, DOCX)
- See metadata (tier, sources, word count)

### 6️⃣ Check Statistics

- 📊 Navigate to **"Statistics"** page
- View today's usage (X / 5 for free)
- Cache hit rate and efficiency
- Clear cache if needed

### 7️⃣ Manage Settings

- ⚙️ Navigate to **"Settings"** page
- View account information
- See upgrade options (Free users)
- Contact info for premium upgrade

---

## 📊 Research Modes Explained

### ⚡ Quick Mode
- **Purpose:** Fast fact-checking or quick overviews
- **Sources:** 2 reliable sources
- **Length:** ~500 words
- **Time:** 30-60 seconds
- **Best For:** Quick answers, fact verification, brief summaries

### 📝 Standard Mode (Recommended)
- **Purpose:** Balanced, comprehensive research
- **Sources:** 5 high-quality sources
- **Length:** ~2000 words
- **Time:** 1-2 minutes
- **Best For:** Essays, blog posts, presentations, general research

### 🔍 Deep Mode (Premium)
- **Purpose:** Academic-level, exhaustive research
- **Sources:** 15+ peer-reviewed sources
- **Length:** 5000+ words
- **Time:** 4-6 minutes
- **Features:** Charts, advanced fact-checking, gap detection
- **Best For:** Thesis, research papers, technical reports

---

## 🏗️ System Architecture

### Frontend (Streamlit)
- **app.py** - Main web application (765 lines)
  - `AutoResearchApp` class with 10 methods
  - Login/signup forms with validation
  - Dashboard with 4 pages (Research, History, Statistics, Settings)
  - Real-time progress indicators
  - Download buttons for exports

### Backend Modules

**Authentication (`auth/`)**
- `authentication.py` - User database, usage tracking, JWT tokens
- `password_recovery.py` - Password reset functionality

**Research (`research/`)**
- `research_modes.py` - 3 modes with configuration
- `query_processor.py` - Async query expansion and correction

**Orchestrator (`orchestrator/`)**
- `tiered_workflow.py` - Main workflow with 9 stages
  - Stage 1: Query expansion
  - Stage 2-5: Iterative search and fact-checking
  - Stage 6: Report generation
  - Stage 7: Editing (Premium)
  - Stage 8: Citations
  - Stage 9: Publishing

**AI Agents (`agents/`)**
- `query_expansion.py` - Break down topics
- `search_agent.py` - Web search
- `summarizer.py` - Extract key facts
- `fact_checker.py` - Verify claims
- `gap_finder.py` - Identify missing info
- `writer.py` - Generate reports
- `editor.py` - Refine text
- `citation.py` - Format references
- `publisher.py` - Export files

**Utilities (`utils/`)**
- `search_engines.py` - Multi-source search with fallbacks
- `cache_system.py` - Query caching with similarity matching
- `credibility_scorer.py` - Source reliability analysis
- `chart_generator.py` - Data visualizations
- `advanced_exports.py` - PDF/DOCX generation

**Subscription (`subscription/`)**
- `manager.py` - Tier management and usage tracking

**Models (`models/`)**
- `router.py` - AI model selection by tier

---

## 📁 Project Structure

```
Auto Reasearch Agent/
├── app.py                      # 🚀 Main Streamlit application (START HERE)
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── setup.ps1                   # Automated setup script
│
├── agents/                     # 9 specialized AI agents
│   ├── query_expansion.py
│   ├── search_agent.py
│   ├── summarizer.py
│   ├── fact_checker.py
│   ├── gap_finder.py
│   ├── writer.py
│   ├── editor.py
│   ├── citation.py
│   └── publisher.py
│
├── auth/                       # Authentication system
│   ├── authentication.py       # Users, JWT, usage tracking
│   └── password_recovery.py    # Password reset
│
├── orchestrator/               # Research workflow
│   └── tiered_workflow.py      # 9-stage pipeline
│
├── research/                   # Research components
│   ├── research_modes.py       # Quick/Standard/Deep modes
│   └── query_processor.py      # Query analysis
│
├── subscription/               # Subscription management
│   └── manager.py              # Tiers, limits, features
│
├── utils/                      # Utilities
│   ├── search_engines.py       # Multi-source search
│   ├── cache_system.py         # Result caching
│   ├── credibility_scorer.py   # Source scoring
│   ├── chart_generator.py      # Visualizations
│   └── advanced_exports.py     # PDF/DOCX export
│
├── models/                     # AI model routing
│   └── router.py               # Model selection
│
├── database/                   # SQLite databases
├── cache/                      # Cached results
├── output_files/               # Generated reports
├── logs/                       # Application logs
│
└── docs/                       # Documentation
    ├── UPGRADE_GUIDE.md        # Complete feature guide
    ├── UPGRADE_SUMMARY.md      # Quick overview
    └── TROUBLESHOOTING.md      # Common issues
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Required: Free tier models
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...

# Optional: Premium tier models
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Search APIs
BRAVE_API_KEY=BSA...
SERPAPI_KEY=...
EXA_API_KEY=...

# Application
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### config.py Settings

```python
# Output
OUTPUT_DIR = "output_files"
CACHE_DIR = "cache"

# Search
DEFAULT_SEARCH_RESULTS = 10
MAX_CONCURRENT_SEARCHES = 5

# Reports
DEFAULT_FORMAT = "pdf"
CITATION_STYLE = "APA"

# Subscription
FREE_DAILY_LIMIT = 5
CACHE_TTL_HOURS = 24
```

---

## 🐛 Troubleshooting

### App Won't Start

```powershell
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt

# Check for port conflicts
netstat -ano | findstr :8501
```

### API Key Errors

```powershell
# Verify .env file exists
Get-Content .env

# Check key format
# Groq: starts with "gsk_"
# Gemini: starts with "AIzaSy"
```

### Database Errors

```powershell
# Reset database
Remove-Item database/*.db
# Restart app (recreates tables)
```

### Cache Issues

- Clear cache from Statistics page
- Or delete manually:
```powershell
Remove-Item -Recurse cache/*
```

---

## 📄 License

MIT License - See LICENSE file for details

---


## 🌟 Acknowledgments

Built with:
- **Streamlit** - Web framework
- **OpenAI GPT-4** - Language models
- **Groq** - Fast inference
- **Google Gemini** - Free AI models
- **SQLite** - Database
- **BeautifulSoup** - Web scraping
- **Matplotlib** - Charts
- **bcrypt** - Password hashing

---

**Made by Sahil Garg**
