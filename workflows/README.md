# n8n Workflows for Clara AI Automation

## Overview

This directory contains n8n workflow templates for automating the Clara AI pipeline.

**Note:** n8n workflows are optional. You can run everything via Python scripts without n8n.

## Workflows Available

### 1. `workflow_pipeline_a.json`
**Purpose:** Automate Pipeline A (Demo → v1)

**Trigger Options:**
- Manual trigger
- File watcher (new files in demo_calls/)
- Webhook (POST new transcript)
- Scheduled check

**Steps:**
1. Trigger receives transcript path or content
2. Execute Pipeline A Python script
3. Parse results
4. Send notification (optional)
5. Create task in tracker (optional)

### 2. `workflow_pipeline_b.json`
**Purpose:** Automate Pipeline B (Onboarding → v2)

**Trigger Options:**
- Manual trigger
- File watcher (new files in onboarding_calls/)
- Webhook (POST new transcript + account_id)

**Steps:**
1. Trigger receives transcript and account_id
2. Execute Pipeline B Python script
3. Parse results
4. Send notification (optional)
5. Update task in tracker (optional)

### 3. `workflow_batch.json`
**Purpose:** Batch process all transcripts

**Trigger Options:**
- Manual trigger
- Scheduled (e.g., daily at midnight)

**Steps:**
1. Execute batch processor
2. Parse summary report
3. Send summary notification
4. Archive processed files (optional)

## Setup Instructions

### Option 1: Run n8n with Docker (Recommended)

```bash
cd /Users/rahulmishra/Desktop/clara-onboarding-automation

# Start n8n
docker-compose up -d

# Access n8n
open http://localhost:5678
```

### Option 2: Run n8n Locally

```bash
# Install n8n globally
npm install -g n8n

# Start n8n
n8n start

# Access at http://localhost:5678
```

## Import Workflows

1. Open n8n at http://localhost:5678
2. Click **"Workflows"** in sidebar
3. Click **"Import from File"**
4. Select workflow JSON file
5. Update credential placeholders
6. Activate workflow

## Configuration Required

### 1. Python Execution Node
- **Command:** `/usr/bin/python3` or path to your venv python
- **Working Directory:** `/path/to/clara-onboarding-automation/scripts`

### 2. File Paths
- **Demo transcripts:** `/path/to/clara-onboarding-automation/data/demo_calls`
- **Onboarding transcripts:** `/path/to/clara-onboarding-automation/data/onboarding_calls`
- **Outputs:** `/path/to/clara-onboarding-automation/outputs`

### 3. Notifications (Optional)
- **Slack webhook:** For notifications
- **Email SMTP:** For email alerts
- **Discord webhook:** For Discord notifications

### 4. Task Tracker (Optional)
- **Asana API token:** For Asana integration
- **Trello API key + token:** For Trello integration

## Why n8n?

**Benefits:**
- 🔄 **Automation** - Process transcripts automatically
- 📊 **Monitoring** - Visual workflow execution logs
- 🔔 **Notifications** - Get alerted when processing completes
- 🔗 **Integrations** - Connect to 300+ services
- 🎨 **Visual** - No-code workflow builder

**When to use:**
- You want automatic processing of new transcripts
- You need to integrate with other tools (Slack, Asana, etc.)
- You want scheduled batch processing
- You want webhook endpoints for external systems

**When NOT to use:**
- You prefer running Python scripts manually
- You don't need automation or integrations
- You want simpler deployment

## Alternative: Python-Based Automation

If you prefer pure Python without n8n:

### File Watcher
```python
# scripts/file_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pipeline_a import process_demo_file

class TranscriptHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.txt'):
            process_demo_file(Path(event.src_path))

observer = Observer()
observer.schedule(TranscriptHandler(), path='data/demo_calls')
observer.start()
```

### Cron Job
```bash
# Run batch processor daily at 2 AM
0 2 * * * cd /path/to/scripts && python batch_process.py
```

## Workflow Templates

Since n8n workflows are JSON-based and contain many IDs/credentials, we provide **workflow blueprints** below instead of full JSON exports.

### Pipeline A Blueprint

**Nodes:**
1. **Manual Trigger** or **Webhook**
2. **Function Node** - Validate input
3. **Execute Command Node** - Run Pipeline A
   ```bash
   cd /path/to/scripts && python pipeline_a.py {{ $json.transcript_path }}
   ```
4. **IF Node** - Check if successful
5. **Slack/Email Node** - Send notification
6. **Asana Node** (optional) - Create task

### Pipeline B Blueprint

**Nodes:**
1. **Manual Trigger** or **Webhook**
2. **Function Node** - Validate input
3. **Execute Command Node** - Run Pipeline B
   ```bash
   cd /path/to/scripts && python pipeline_b.py {{ $json.transcript_path }} {{ $json.account_id }}
   ```
4. **IF Node** - Check if successful
5. **Slack/Email Node** - Send notification
6. **Asana Node** (optional) - Update task

## Manual Workflow Creation

### Step 1: Create New Workflow in n8n

1. Click **"+ New Workflow"**
2. Name it **"Clara - Pipeline A"**

### Step 2: Add Manual Trigger

1. Click **"+ Add Node"**
2. Search for **"Manual Trigger"**
3. Add it to canvas

### Step 3: Add Execute Command Node

1. Click **"+ Add Node"**
2. Search for **"Execute Command"**
3. Configure:
   - **Command:** `python3`
   - **Arguments:** `pipeline_a.py {{ $json.transcript_path }}`
   - **Working Directory:** `/path/to/clara-onboarding-automation/scripts`

### Step 4: Add Function Node (Parse Output)

1. Click **"+ Add Node"**
2. Search for **"Function"**
3. Add JavaScript to parse JSON output:
   ```javascript
   const output = items[0].json;
   const result = JSON.parse(output.stdout || '{}');
   return [{json: result}];
   ```

### Step 5: Add Conditional Logic

1. Click **"+ Add Node"**
2. Search for **"IF"**
3. Configure:
   - **Condition:** `{{ $json.status }} === 'success'`

### Step 6: Add Notification (Optional)

**For Success Branch:**
1. Click **"+ Add Node"** after IF true
2. Add **Slack** or **Email** node
3. Message: `✅ Pipeline A completed for {{ $json.account_id }}`

**For Failure Branch:**
1. Click **"+ Add Node"** after IF false
2. Add **Slack** or **Email** node
3. Message: `❌ Pipeline A failed: {{ $json.errors }}`

### Step 7: Save and Activate

1. Click **"Save"**
2. Toggle **"Active"** switch
3. Test with **"Execute Workflow"**

## Testing Workflows

### Test Pipeline A Workflow

1. Open workflow in n8n
2. Click **"Execute Workflow"**
3. Provide test input:
   ```json
   {
     "transcript_path": "/path/to/data/demo_calls/test_demo.txt"
   }
   ```
4. Watch execution in real-time
5. Check outputs in each node

### Test Pipeline B Workflow

1. Open workflow in n8n
2. Click **"Execute Workflow"**
3. Provide test input:
   ```json
   {
     "transcript_path": "/path/to/data/onboarding_calls/test_onboarding.txt",
     "account_id": "acme-fire-protection"
   }
   ```
4. Verify v2 outputs created

## Production Deployment

### Docker Compose (Recommended)

Already configured in `docker-compose.yml`:

```bash
# Start n8n
docker-compose up -d

# View logs
docker-compose logs -f n8n

# Stop
docker-compose down
```

### Environment Variables

Add to `.env`:
```bash
# n8n Configuration
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_HOST=localhost

# Webhook URL (if using webhooks)
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# Execution mode
EXECUTIONS_MODE=regular
```

## Security Considerations

1. **API Keys:** Store in n8n credentials, not in workflow JSON
2. **Webhooks:** Use authentication tokens
3. **File Access:** Restrict to specific directories
4. **Network:** Run n8n behind firewall for production

## Monitoring

### View Execution History

1. Go to **"Executions"** in n8n
2. See all workflow runs
3. Click to see detailed logs
4. Check execution time and success rate

### Set Up Alerts

1. Add **Error Trigger** workflow
2. Configure to notify on any workflow failure
3. Send to Slack/Email/PagerDuty

## Cost

**n8n is free and open-source!**

- ✅ Self-hosted: $0/month
- ✅ No execution limits
- ✅ Unlimited workflows
- ✅ All features included

*(Cloud version available at n8n.io if you prefer managed hosting)*

## Support

**n8n Documentation:** https://docs.n8n.io
**Community Forum:** https://community.n8n.io
**GitHub:** https://github.com/n8n-io/n8n

## Next Steps

1. ✅ Start n8n: `docker-compose up -d`
2. ✅ Access UI: http://localhost:5678
3. ✅ Create account (local only)
4. ✅ Build your first workflow using blueprints above
5. ✅ Test with sample transcripts
6. ✅ Activate for production use

---

**n8n is optional but recommended for automation at scale!**
