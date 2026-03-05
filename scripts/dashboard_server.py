"""
Simple dashboard server for viewing Clara AI outputs.
Serves the HTML dashboard and provides account data via API.
"""

import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from storage import AccountStorage
from logger import get_processing_logger

logger = get_processing_logger()

# Configuration
PORT = 8000
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for dashboard."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)
        self.storage = AccountStorage()

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # API endpoint for account data
        if parsed_path.path == '/api/accounts':
            self.serve_accounts_api()
        # API endpoint for specific account
        elif parsed_path.path.startswith('/api/account/'):
            account_id = parsed_path.path.split('/')[-1]
            self.serve_account_detail(account_id)
        # Serve static files
        else:
            super().do_GET()

    def serve_accounts_api(self):
        """Serve accounts data as JSON API."""
        try:
            # Get all accounts
            account_ids = self.storage.list_accounts()

            accounts_data = []
            for account_id in account_ids:
                try:
                    # Get account status
                    status = self.storage.get_account_status(account_id)

                    # Load metadata
                    metadata = self.storage.load_metadata(account_id) or {}

                    # Load latest memo (v2 if available, else v1)
                    memo = self.storage.load_v2_memo(account_id)
                    if not memo:
                        memo = self.storage.load_v1_memo(account_id)

                    company_name = memo.get('company_name', 'Unknown') if memo else 'Unknown'
                    unknowns_count = len(memo.get('questions_or_unknowns', [])) if memo else 0

                    account_data = {
                        'account_id': account_id,
                        'company_name': company_name,
                        'has_v1': status['has_v1_memo'],
                        'has_v1_agent': status['has_v1_agent'],
                        'has_v2': status['has_v2_memo'],
                        'has_v2_agent': status['has_v2_agent'],
                        'has_changelog': status['has_changelog'],
                        'unknowns_count': unknowns_count,
                        'processing_status': metadata.get('processing_status', 'unknown'),
                        'last_processed': metadata.get('last_processed', None)
                    }

                    accounts_data.append(account_data)

                except Exception as e:
                    logger.error(f"Error loading account {account_id}: {e}")
                    continue

            # Return JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                'accounts': accounts_data,
                'total': len(accounts_data),
                'v1_complete': sum(1 for a in accounts_data if a['has_v1']),
                'v2_complete': sum(1 for a in accounts_data if a['has_v2']),
                'fully_complete': sum(1 for a in accounts_data if a['has_v2_agent'] and a['has_changelog'])
            }

            self.wfile.write(json.dumps(response, indent=2).encode())

        except Exception as e:
            logger.error(f"Error serving accounts API: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def serve_account_detail(self, account_id):
        """Serve detailed account data."""
        try:
            # Load all data for the account
            v1_memo = self.storage.load_v1_memo(account_id)
            v2_memo = self.storage.load_v2_memo(account_id)
            v1_agent = self.storage.load_agent_spec(account_id, 'v1')
            v2_agent = self.storage.load_agent_spec(account_id, 'v2')
            changelog = self.storage.load_changelog(account_id)
            metadata = self.storage.load_metadata(account_id)

            account_detail = {
                'account_id': account_id,
                'v1_memo': v1_memo,
                'v2_memo': v2_memo,
                'v1_agent': v1_agent,
                'v2_agent': v2_agent,
                'changelog': changelog,
                'metadata': metadata
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(account_detail, indent=2).encode())

        except Exception as e:
            logger.error(f"Error serving account detail for {account_id}: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

    def log_message(self, format, *args):
        """Custom log message."""
        logger.info(f"Dashboard: {format % args}")


def start_dashboard_server(port=PORT):
    """Start the dashboard server."""
    try:
        # Ensure dashboard directory exists
        if not DASHBOARD_DIR.exists():
            logger.error(f"Dashboard directory not found: {DASHBOARD_DIR}")
            print(f"❌ Dashboard directory not found: {DASHBOARD_DIR}")
            return

        # Create server
        with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
            logger.info(f"Dashboard server starting on port {port}")
            print(f"\n{'='*60}")
            print(f"🚀 Clara AI Dashboard Server")
            print(f"{'='*60}")
            print(f"\nServer running at: http://localhost:{port}")
            print(f"Dashboard: http://localhost:{port}/index.html")
            print(f"API: http://localhost:{port}/api/accounts")
            print(f"\nPress Ctrl+C to stop the server\n")

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n\n✅ Server stopped")
                logger.info("Dashboard server stopped")

    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port {port} is already in use.")
            print(f"Try: python dashboard_server.py {port + 1}")
        else:
            logger.error(f"Error starting server: {e}")
            print(f"❌ Error starting server: {e}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    import sys

    # Get port from command line if provided
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT

    # Start server
    start_dashboard_server(port)
