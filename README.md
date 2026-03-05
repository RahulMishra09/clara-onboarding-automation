# Clara AI Automation Pipeline

**Transform call transcripts into production-ready voice AI agent configurations — automatically, at zero cost.**

---

## 🚀 Quick Start

```bash
# 1. Clone and navigate
cd clara-onboarding-automation

# 2. Start the system (automated setup + health check)
./start.sh

# 3. Process your first call
python scripts/pipeline_a.py data/demo_calls/test_demo.txt

# 4. View results in dashboard
python scripts/dashboard_server.py
# Open: http://localhost:8000/viewer.html
```

**That's it!** The `start.sh` script handles virtual environment setup, dependency installation, and health checks automatically.

---

## 📚 Documentation

- **[QUICK_START_OLLAMA.md](QUICK_START_OLLAMA.md)** - Step-by-step guide for Ollama + Supabase
- **[PRODUCTION.md](PRODUCTION.md)** - Production deployment & operations guide
- **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** - Complete technical documentation

---

## ✨ What This Does

Processes transcripts through a two-stage pipeline:

### Pipeline A: Demo Call → v1
```bash
python scripts/pipeline_a.py data/demo_calls/call.txt
```
**Output:** v1 Account Memo + v1 Retell Agent Spec

### Pipeline B: Onboarding Call → v2
```bash
python scripts/pipeline_b.py data/onboarding_calls/call.txt <account-id>
```
**Output:** v2 Account Memo + v2 Retell Agent Spec + Changelog (v1 → v2)

---

## 🎯 Key Features

- ✅ **Zero Hallucination** - Explicit unknowns field, never invents data
- ✅ **Version Control** - Complete v1 → v2 audit trail with changelog
- ✅ **Safety-First** - Validated prompts, forbidden term detection
- ✅ **Zero Cost** - $0 spent (Ollama + Supabase free tier)
- ✅ **Production-Ready** - Health checks, error handling, monitoring
- ✅ **Fully Tested** - 35 automated tests, 100% pass rate

---

## 📁 Project Structure

```
clara-onboarding-automation/
├── start.sh                    # 🚀 Production startup script
├── .env                        # Configuration (Ollama + Supabase)
├── requirements.txt            # Python dependencies
│
├── scripts/                    # Core Python modules
│   ├── health_check.py        # System health validation
│   ├── pipeline_a.py          # Demo → v1 pipeline
│   ├── pipeline_b.py          # Onboarding → v2 pipeline
│   ├── batch_process.py       # Batch processor
│   ├── extract_memo.py        # LLM extraction engine
│   ├── generate_prompt.py     # Agent spec generation
│   ├── storage.py             # Storage abstraction
│   ├── llm_client.py          # Multi-provider LLM client
│   ├── schemas.py             # Pydantic data models
│   ├── validators.py          # Safety validation
│   ├── logger.py              # Logging utilities
│   └── dashboard_server.py    # Dashboard API server
│
├── data/                       # Input transcripts
│   ├── demo_calls/            # Demo call transcripts
│   └── onboarding_calls/      # Onboarding call transcripts
│
├── outputs/                    # Generated outputs
│   └── accounts/              # Per-account data
│       └── <account-id>/
│           ├── v1/            # Version 1 (from demo)
│           ├── v2/            # Version 2 (from onboarding)
│           └── metadata.json  # Processing metadata
│
├── prompts/                    # LLM prompt templates
│   ├── extract_demo.txt       # Demo extraction prompt
│   └── extract_onboarding.txt # Onboarding extraction prompt
│
├── tests/                      # Automated tests
│   ├── test_schemas.py        # Schema validation tests
│   ├── test_validators.py     # Safety validator tests
│   └── test_storage.py        # Storage tests
│
├── dashboard/                  # Web dashboard
│   ├── viewer.html            # Interactive account viewer
│   └── index.html             # Landing page
│
├── workflows/                  # n8n automation (optional)
│   └── README.md              # Workflow blueprints
│
├── logs/                       # System logs
│   ├── extraction.log         # LLM extraction logs
│   ├── processing.log         # Pipeline logs
│   └── validation.log         # Validation logs
│
└── setup_schema.py             # Supabase schema setup
```

---

## 🏥 Health Checks

Run system health check anytime:

```bash
python scripts/health_check.py
```

**Validates:**
- ✅ Environment configuration
- ✅ Required directories & files
- ✅ Ollama server connectivity
- ✅ Ollama model availability
- ✅ Supabase connection
- ✅ Python dependencies
- ✅ Write permissions

**Exit codes:**
- `0` - All checks passed (ready to process)
- `1` - Errors found (review output)

---

## ⚙️ Configuration

Edit [.env](.env) file:

```bash
# LLM Provider (choose one)
LLM_PROVIDER=ollama                    # Free, local (recommended)
# LLM_PROVIDER=anthropic               # Cloud, requires API key
# LLM_PROVIDER=openai                  # Cloud, requires API key

# Ollama Settings (if using ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Storage (choose one)
STORAGE_TYPE=supabase                  # Cloud storage (recommended)
# STORAGE_TYPE=local                   # Local JSON files

# Supabase Settings (if using supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Processing
MAX_RETRIES=3
TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
```

---

## 🔄 Common Workflows

### Process Single Demo Call
```bash
python scripts/pipeline_a.py data/demo_calls/new_call.txt
```

### Process Single Onboarding Call
```bash
python scripts/pipeline_b.py data/onboarding_calls/new_call.txt acme-fire-protection
```

### Batch Process All Calls
```bash
python scripts/batch_process.py
```
Processes all files in `data/demo_calls/` and `data/onboarding_calls/`

### View Dashboard
```bash
python scripts/dashboard_server.py
```
Then open: http://localhost:8000/viewer.html

### Setup Supabase Database
```bash
python setup_schema.py
```
Creates required tables: `conversations`, `account_memos`, `agent_specs`, `changelogs`

---

## 🧪 Testing

Run all tests:

```bash
cd tests
python test_schemas.py
python test_validators.py
python test_storage.py
```

**Test Coverage:**
- Schema validation (12 tests)
- Safety validators (10 tests)
- Storage operations (13 tests)
- **Total: 35 tests, 100% pass rate**

---

## 🐛 Troubleshooting

### Ollama Connection Refused

**Problem:** `❌ Ollama Server: Server not running`

**Solution:**
```bash
# Start Ollama server (in separate terminal)
ollama serve

# Pull model if needed
ollama pull llama3.1
```

### Supabase Connection Failed

**Problem:** `❌ Supabase Connection: Connection error`

**Solution:**
1. Verify credentials in `.env`
2. Check project is active at https://supabase.com/dashboard
3. Test connection: `python scripts/health_check.py`

### Module Not Found

**Problem:** `ImportError: No module named 'anthropic'`

**Solution:**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

**See [PRODUCTION.md](PRODUCTION.md#troubleshooting) for more solutions**

---

## 📊 Performance

### Processing Times (Ollama, local)

- Demo call extraction: **15-25 seconds**
- Onboarding call extraction: **20-30 seconds**
- Batch processing (10 files): **3-5 minutes**

### Cost Breakdown

- **Ollama:** $0.00 (unlimited, local)
- **Supabase Free Tier:** $0.00 (500MB database)
- **Total:** **$0.00** ✅

---

## 🔒 Security

- ✅ Credentials stored in `.env` (not committed)
- ✅ Supabase uses anon/public key (not service_role)
- ✅ Ollama runs locally (not exposed to internet)
- ✅ Safety validators prevent prompt injection
- ✅ Forbidden term detection in generated prompts

**See [PRODUCTION.md](PRODUCTION.md#security-best-practices) for details**

---

## 📦 Requirements

- Python 3.10+
- Ollama (for local LLM) or API keys (for cloud LLM)
- Supabase account (free tier) or local storage
- 4GB+ disk space (for Ollama model)

---

## 🎓 Learn More

- **Quick Start:** [QUICK_START_OLLAMA.md](QUICK_START_OLLAMA.md)
- **Production Deployment:** [PRODUCTION.md](PRODUCTION.md)
- **Complete Docs:** [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)
- **Dashboard Guide:** [dashboard/README.md](dashboard/README.md)
- **n8n Automation:** [workflows/README.md](workflows/README.md)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Support

- **Issues:** Report at GitHub repository
- **Documentation:** All guides in `*.md` files
- **Health Check:** Run `python scripts/health_check.py`

---

**Built with:** Python • Pydantic • Ollama • Supabase • n8n (optional)

**Status:** ✅ Production Ready

**Version:** 1.0.0

**Last Updated:** 2026-03-05
