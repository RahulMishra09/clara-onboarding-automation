# Quick Start with Ollama + Supabase

## Current Status ✅

Your system is configured and ready! Here's what's set up:

- ✅ Configuration validated (`config.py` test passed)
- ✅ LLM Provider: Ollama (local, free)
- ✅ Storage Type: Supabase (cloud, free tier)
- ✅ Virtual environment ready
- ⚠️ Ollama server needs to be started
- ⚠️ Supabase credentials need to be added to `.env`

---

## Step 1: Start Ollama (Required)

Open a **new terminal window** and keep it running:

```bash
ollama serve
```

**Expected output:**
```
2026/03/05 14:30:00 routes.go:1148: Listening on 127.0.0.1:11434
```

**Keep this terminal open!** The Ollama server must stay running.

---

## Step 2: Download Model (One-Time)

In **another terminal**:

```bash
# Download LLama 3.1 model (~4GB, takes 5-10 minutes)
ollama pull llama3.1

# Verify it's installed
ollama list
```

**Expected output:**
```
NAME            ID              SIZE    MODIFIED
llama3.1:latest abc123def456    4.7 GB  2 minutes ago
```

---

## Step 3: Configure Supabase

### Option A: Use Existing Supabase Project

If you already have a Supabase project:

1. Go to https://supabase.com/dashboard
2. Open your project
3. Go to **Settings → API**
4. Copy:
   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

5. Edit `.env` file and replace:
   ```bash
   SUPABASE_URL=https://your-actual-project-id.supabase.co
   SUPABASE_KEY=your-actual-anon-key-here
   ```

### Option B: Create New Supabase Project

1. Go to https://supabase.com/dashboard
2. Click **"New Project"**
3. Fill in:
   - Name: `clara-ai-automation`
   - Database Password: (create strong password, **save it**)
   - Region: Choose closest to you
   - Pricing: **Free** (500MB database)
4. Wait 2-3 minutes for initialization
5. Follow steps from Option A to get credentials

### Option C: Use Local Storage (Temporary)

If you want to test without Supabase first:

Edit `.env`:
```bash
# Change this line:
STORAGE_TYPE=local

# Comment out Supabase lines:
# SUPABASE_URL=...
# SUPABASE_KEY=...
```

---

## Step 4: Test Your Setup

```bash
cd /Users/rahulmishra/Desktop/clara-onboarding-automation
source venv/bin/activate
cd scripts

# Test configuration
python config.py

# Test Ollama connection
python llm_client.py
```

**Expected output:**
```
✅ Configuration is valid
LLM Provider: ollama
Storage Type: supabase (or local)

INFO     [clara.extraction] Initializing LLM client: ollama
INFO     [clara.extraction] ✅ Ollama client initialized (llama3.1)
INFO     [clara.extraction] Testing LLM client...
INFO     [clara.extraction] Response: {"company_name": "Acme Fire Protection Services"}
INFO     [clara.extraction] ✅ LLM client test passed!
```

---

## Step 5: Process Your First Transcript

Once tests pass:

```bash
# Process demo transcript (creates v1 Account Memo + Agent Spec)
python pipeline_a.py ../data/demo_calls/test_demo.txt
```

**What happens:**
1. Reads transcript from `test_demo.txt`
2. Sends to Ollama for extraction (~20 seconds)
3. Generates v1 Account Memo
4. Generates v1 Retell Agent Spec
5. Saves to Supabase (or local storage)

**Expected output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           PIPELINE A: DEMO → V1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] Reading transcript...
✅ Loaded: test_demo.txt (1234 chars)

[2/5] Extracting v1 Account Memo (LLM)...
⏳ This may take 15-25 seconds with Ollama...
✅ Extracted v1 memo for: Acme Fire Protection

[3/5] Generating v1 Agent Spec...
✅ Generated v1 agent spec

[4/5] Saving outputs...
✅ Saved to: outputs/accounts/acme-fire-protection/v1/

[5/5] Updating metadata...
✅ Metadata updated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           ✅ PIPELINE A COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Troubleshooting

### "could not connect to ollama server"

**Problem:** Ollama server not running

**Solution:**
```bash
# In a separate terminal:
ollama serve
```

Keep this terminal open while processing transcripts.

### "Connection refused" (Ollama)

**Problem:** Ollama still starting

**Solution:**
```bash
# Wait 10 seconds after starting ollama serve
# Check it's running:
curl http://localhost:11434
# Should return: Ollama is running
```

### "Invalid Supabase credentials"

**Problem:** Wrong URL or key in `.env`

**Solution:**
1. Go to Supabase dashboard
2. Settings → API
3. Copy **Project URL** and **anon public** key
4. Paste into `.env` (no quotes needed)

### Ollama is slow

**Normal!** First run downloads the model (~4GB).

Check progress:
```bash
ollama pull llama3.1
```

After download, each extraction takes 10-20 seconds (local processing).

---

## What's Next?

1. **Process onboarding transcript:**
   ```bash
   python pipeline_b.py ../data/onboarding_calls/test_onboarding.txt acme-fire-protection
   ```

2. **Batch process all files:**
   ```bash
   python batch_process.py
   ```

3. **View dashboard:**
   ```bash
   python dashboard_server.py
   # Open http://localhost:8000/viewer.html in browser
   ```

---

## Performance Expectations

### With Ollama (Local):
- **Demo extraction:** 15-25 seconds per file
- **Onboarding extraction:** 20-30 seconds per file
- **Total for 10 files:** ~3-5 minutes

### With Supabase:
- **Save operation:** <1 second
- **Load operation:** <1 second
- **No rate limits** on free tier

---

## Cost Breakdown

- **Ollama:** $0.00 (100% free, unlimited)
- **Supabase Free Tier:** $0.00 (500MB database, 1GB storage)
- **Total:** $0.00 ✅

---

## Need More Help?

- **Detailed setup:** See `OLLAMA_SUPABASE_SETUP.md`
- **Full documentation:** See `PROJECT_COMPLETE.md`
- **General setup:** See `SETUP_GUIDE.md`
- **Project overview:** See `README.md`

---

**You're all set! Start with Step 1 above.** 🚀
