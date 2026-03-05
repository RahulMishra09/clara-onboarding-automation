#!/usr/bin/env python3
"""
Setup Supabase schema using direct SQL execution.
"""

import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv('/Users/rahulmishra/Desktop/clara-onboarding-automation/.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("🗄️  Creating Supabase Database Schema")
print("=" * 70)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials not found in .env")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Parse Supabase URL to get connection string
    # Format: https://[project-ref].supabase.co
    project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
    
    # Supabase connection string
    conn_string = f"postgresql://postgres:{SUPABASE_KEY}@db.{project_ref}.supabase.co:5432/postgres"
    
    print(f"\n📌 Connecting to Supabase database...")
    conn = psycopg2.connect(conn_string, sslmode='require')
    cursor = conn.cursor()
    print("✅ Connected!")
    
    # SQL statements to create tables
    tables_sql = """
    -- Create conversations table
    CREATE TABLE IF NOT EXISTS public.conversations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        account_id TEXT NOT NULL,
        call_type TEXT NOT NULL,
        transcript TEXT NOT NULL,
        call_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
        duration_seconds INT,
        file_path TEXT,
        source_file TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    
    -- Create account_memos table
    CREATE TABLE IF NOT EXISTS public.account_memos (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        account_id TEXT NOT NULL,
        version TEXT NOT NULL,
        company_name TEXT,
        memo_data JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        UNIQUE(account_id, version)
    );
    
    -- Create agent_specs table
    CREATE TABLE IF NOT EXISTS public.agent_specs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        account_id TEXT NOT NULL,
        version TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        spec_data JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        UNIQUE(account_id, version)
    );
    
    -- Create changelogs table
    CREATE TABLE IF NOT EXISTS public.changelogs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        account_id TEXT NOT NULL,
        from_version TEXT NOT NULL,
        to_version TEXT NOT NULL,
        changelog_data JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    
    -- Create indices
    CREATE INDEX IF NOT EXISTS idx_conversations_account_id 
        ON public.conversations(account_id);
    CREATE INDEX IF NOT EXISTS idx_conversations_call_type 
        ON public.conversations(call_type);
    CREATE INDEX IF NOT EXISTS idx_account_memos_account_id 
        ON public.account_memos(account_id);
    CREATE INDEX IF NOT EXISTS idx_agent_specs_account_id 
        ON public.agent_specs(account_id);
    CREATE INDEX IF NOT EXISTS idx_changelogs_account_id 
        ON public.changelogs(account_id);
    """
    
    print("\n📝 Executing table creation SQL...")
    cursor.execute(tables_sql)
    conn.commit()
    print("✅ Tables created successfully!")
    
    # Verify tables were created
    print("\n✔️  Verifying tables...")
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    print(f"\n📊 Created tables in database:")
    for table in tables:
        print(f"   ✓ {table[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ SUPABASE SCHEMA SETUP COMPLETE!")
    print("=" * 70)
    print("\nYour database is ready for the Clara AI Automation Pipeline!")
    print("\nTables created:")
    print("  • conversations - Store call transcripts and metadata")
    print("  • account_memos - Store v1 and v2 account memos")
    print("  • agent_specs - Store agent specifications")
    print("  • changelogs - Track changes between versions")
    
except ImportError:
    print("⚠️  psycopg2 not installed. Installing...")
    os.system("pip install psycopg2-binary -q")
    print("✅ Installed. Please run this script again.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
