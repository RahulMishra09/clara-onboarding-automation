# Production Deployment Guide

This guide covers deploying the Clara AI Automation Pipeline to production.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Production Setup](#production-setup)
3. [Configuration](#configuration)
4. [Health Checks](#health-checks)
5. [Monitoring](#monitoring)
6. [Backup & Recovery](#backup--recovery)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

---

## Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All tests pass (`cd tests && python test_*.py`)
- [ ] Environment variables configured in `.env`
- [ ] Supabase database schema created (`python setup_schema.py`)
- [ ] Ollama server running with required model
- [ ] Health check passes (`python scripts/health_check.py`)
- [ ] Backups configured for critical data
- [ ] Monitoring and alerting set up

---

## Production Setup

### 1. Quick Start

```bash
# Clone or copy the project
cd /path/to/clara-onboarding-automation

# Run the startup script (automated setup + health check)
./start.sh
```

The `start.sh` script will:
- Create virtual environment if needed
- Install dependencies
- Run comprehensive health checks
- Display available commands

### 2. Manual Setup

If you prefer manual setup:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 4. Run health check
python scripts/health_check.py

# 5. Setup database (if using Supabase)
python setup_schema.py
```

---

## Configuration

### Environment Variables

Edit `.env` file with production values:

```bash
# LLM Provider
LLM_PROVIDER=ollama                    # Options: ollama, anthropic, openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Storage
STORAGE_TYPE=supabase                  # Options: supabase, local
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Processing
MAX_RETRIES=3
TIMEOUT_SECONDS=30
LOG_LEVEL=INFO                         # Options: DEBUG, INFO, WARNING, ERROR

# Output
OUTPUT_DIR=./outputs/accounts
LOG_DIR=./logs
```

### Storage Configuration

#### Option A: Supabase (Recommended for Production)

**Pros:**
- Cloud-hosted, automatic backups
- Built-in API and auth
- Free tier: 500MB database
- Easy to scale

**Setup:**
1. Go to https://supabase.com/dashboard
2. Create new project (free tier)
3. Copy URL and anon key to `.env`
4. Run: `python setup_schema.py`

#### Option B: Local JSON Storage

**Pros:**
- Zero external dependencies
- Complete control over data
- Works offline

**Setup:**
```bash
# In .env
STORAGE_TYPE=local
```

Data stored in: `outputs/accounts/<account-id>/`

---

## Health Checks

### Automated Health Check

Run before every deployment:

```bash
python scripts/health_check.py
```

**Checks performed:**
- ✅ Environment variables
- ✅ Configuration validation
- ✅ Required directories
- ✅ Prompt templates
- ✅ Python dependencies
- ✅ Ollama server connectivity
- ✅ Ollama model availability
- ✅ Supabase connection
- ✅ Write permissions

**Exit codes:**
- `0` - All checks passed
- `1` - Critical errors found

### Manual Health Checks

```bash
# Check Ollama
curl http://localhost:11434/api/version

# Check Supabase
curl -H "apikey: YOUR_KEY" \
     -H "Authorization: Bearer YOUR_KEY" \
     https://your-project.supabase.co/rest/v1/

# Check configuration
python scripts/config.py

# Check LLM client
python scripts/llm_client.py
```

---

## Monitoring

### Log Files

Logs are written to `logs/` directory:

- `extraction.log` - LLM extraction operations
- `processing.log` - Pipeline processing
- `validation.log` - Validation errors

**View logs in real-time:**

```bash
# Watch all logs
tail -f logs/*.log

# Watch extraction logs only
tail -f logs/extraction.log
```

### Key Metrics to Monitor

1. **Processing Time**
   - Demo call extraction: 15-25 seconds (Ollama)
   - Onboarding call extraction: 20-30 seconds (Ollama)

2. **Error Rates**
   - LLM extraction failures
   - Validation errors
   - Storage write failures

3. **Resource Usage**
   - Disk space (outputs + logs)
   - Ollama memory usage
   - API rate limits (if using cloud LLM)

### Dashboard

Start the dashboard for real-time monitoring:

```bash
python scripts/dashboard_server.py
```

Open: http://localhost:8000/viewer.html

**Features:**
- View all accounts
- Compare v1 vs v2
- Review changelogs
- Syntax-highlighted JSON

---

## Backup & Recovery

### What to Backup

1. **Critical Data:**
   - `.env` file (contains credentials)
   - `outputs/accounts/` (all processed data)
   - `data/` (original transcripts)

2. **Optional:**
   - `logs/` (for audit trail)
   - `prompts/` (if customized)

### Backup Strategy

#### Option A: Supabase (Automated)

Supabase automatically backs up your database. Additional backups:

```bash
# Export all data
python scripts/backup_supabase.py
```

#### Option B: Local Storage

```bash
# Create timestamped backup
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backups/backup_${DATE}.tar.gz \
    outputs/ \
    data/ \
    .env

# Keep last 30 days
find backups/ -name "backup_*.tar.gz" -mtime +30 -delete
```

### Recovery

```bash
# Restore from backup
tar -xzf backups/backup_20260305_143000.tar.gz

# Verify health after restore
python scripts/health_check.py
```

---

## Troubleshooting

### Common Issues

#### 1. Ollama Connection Refused

**Symptoms:**
```
❌ Ollama Server: Server not running
```

**Solution:**
```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/version
```

#### 2. Model Not Found

**Symptoms:**
```
⚠️ Ollama Model: Model 'llama3.1' not found
```

**Solution:**
```bash
# Pull the model (~4GB)
ollama pull llama3.1

# Verify it's downloaded
ollama list
```

#### 3. Supabase Connection Failed

**Symptoms:**
```
❌ Supabase Connection: Connection error
```

**Solution:**
1. Verify credentials in `.env`
2. Check Supabase project is active
3. Test connection:
   ```bash
   python -c "
   import os, requests
   from dotenv import load_dotenv
   load_dotenv()
   url = os.getenv('SUPABASE_URL')
   key = os.getenv('SUPABASE_KEY')
   r = requests.get(f'{url}/rest/v1/', headers={'apikey': key})
   print(f'Status: {r.status_code}')
   "
   ```

#### 4. Permission Denied

**Symptoms:**
```
❌ Write Permissions: No write access to outputs
```

**Solution:**
```bash
# Fix permissions
chmod -R u+w outputs logs

# Or recreate directories
rm -rf outputs logs
mkdir -p outputs/accounts logs
```

#### 5. Extraction Timeout

**Symptoms:**
```
ERROR - Extraction timeout after 30 seconds
```

**Solution:**
```bash
# Increase timeout in .env
TIMEOUT_SECONDS=60

# Or use faster model
OLLAMA_MODEL=llama3.1:8b  # Smaller, faster
```

---

## Security Best Practices

### 1. Environment Variables

- ✅ **DO:** Store credentials in `.env` (not committed to git)
- ✅ **DO:** Use `.env.example` for templates (no real credentials)
- ❌ **DON'T:** Hardcode credentials in scripts
- ❌ **DON'T:** Commit `.env` to version control

### 2. API Keys

- ✅ **DO:** Use anon/public keys for Supabase (not service_role)
- ✅ **DO:** Rotate keys periodically
- ❌ **DON'T:** Share keys in logs or error messages

### 3. File Permissions

```bash
# Restrict .env file
chmod 600 .env

# Allow execution of scripts only
chmod 755 scripts/*.py
chmod 755 start.sh
```

### 4. Network Security

- ✅ **DO:** Use HTTPS for Supabase connections
- ✅ **DO:** Run Ollama on localhost (not exposed to internet)
- ❌ **DON'T:** Expose dashboard server to public internet

### 5. Data Privacy

- ✅ **DO:** Sanitize transcripts before storage (remove PII if needed)
- ✅ **DO:** Encrypt backups
- ✅ **DO:** Use Supabase RLS (Row Level Security) policies
- ❌ **DON'T:** Store sensitive customer data without encryption

---

## Production Workflows

### Daily Operations

**Morning:**
```bash
# 1. Start system
./start.sh

# 2. Process overnight transcripts
python scripts/batch_process.py
```

**During Day:**
```bash
# Process individual calls as they come in
python scripts/pipeline_a.py data/demo_calls/new_call.txt
```

**Evening:**
```bash
# Review dashboard for any issues
python scripts/dashboard_server.py
# Open: http://localhost:8000/viewer.html

# Check logs for errors
grep ERROR logs/*.log
```

### Weekly Maintenance

```bash
# 1. Backup data
./scripts/backup.sh

# 2. Clean old logs (optional)
find logs/ -name "*.log" -mtime +30 -delete

# 3. Update dependencies
pip install --upgrade -r requirements.txt

# 4. Run all tests
cd tests && python test_*.py
```

---

## Performance Tuning

### Ollama Performance

**Faster processing:**
```bash
# Use smaller model (faster, less accurate)
OLLAMA_MODEL=llama3.1:8b

# Or use faster model family
OLLAMA_MODEL=mistral
```

**Better quality:**
```bash
# Use larger model (slower, more accurate)
OLLAMA_MODEL=llama3.1:70b
```

### Batch Processing

```bash
# Process multiple files in parallel (careful with resource usage)
python scripts/batch_process.py --parallel 3
```

### Storage Optimization

**Supabase:**
- Use proper indexes (already set up by `setup_schema.py`)
- Archive old versions periodically

**Local:**
- Compress old data: `gzip outputs/accounts/*/v1/*.json`
- Move archived data to separate directory

---

## Scaling Considerations

### Current Limits (Free Tier)

- **Ollama:** Unlimited (local processing)
- **Supabase:** 500MB database, 1GB storage
- **Processing:** ~3-5 minutes for 10 calls

### When to Scale

**Upgrade Supabase** when:
- Database > 400MB (~10,000 accounts)
- Need faster query performance
- Need more storage

**Upgrade LLM** when:
- Need faster processing (use cloud LLM)
- Need better accuracy (use GPT-4 or Claude)

**Horizontal Scaling:**
- Run multiple Ollama instances
- Use load balancer for dashboard
- Implement job queue (e.g., Celery + Redis)

---

## Support & Resources

- **Documentation:** [README.md](README.md)
- **Quick Start:** [QUICK_START_OLLAMA.md](QUICK_START_OLLAMA.md)
- **Complete Docs:** [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)

- **Supabase Docs:** https://supabase.com/docs
- **Ollama Docs:** https://ollama.ai/docs

---

**Last Updated:** 2026-03-05
**Version:** 1.0.0
**Status:** Production Ready ✅
