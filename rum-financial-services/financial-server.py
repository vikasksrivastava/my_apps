#!/usr/bin/env python3
"""
SecureBank Financial Services - Customer Portal Server
A banking/financial services simulation server with intentionally slow routes for RUM demos.

Usage: python3 financial-server.py [port] [delay]
  port  - Server port (default: 3002)
  delay - Delay in seconds for slow routes (default: 6.0)

Examples:
  python3 financial-server.py              # port=3002, delay=6s
  python3 financial-server.py 8080         # port=8080, delay=6s
  python3 financial-server.py 8080 3       # port=8080, delay=3s

Environment variables:
  PORT  - Server port
  DELAY - Delay in seconds
"""

import http.server
import socketserver
import json
import time
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

# Port priority: command line arg > environment variable > default
if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
else:
    PORT = int(os.environ.get('PORT', 3002))

# Delay priority: command line arg > environment variable > default
if len(sys.argv) > 2:
    DEFAULT_DELAY = float(sys.argv[2])
else:
    DEFAULT_DELAY = float(os.environ.get('DELAY', 24.0))

# Configurable delays (in seconds) for critical financial operations
DELAYS = {
    # Account Management - Critical
    '/view-account-details': DEFAULT_DELAY,
    '/view-statements': DEFAULT_DELAY,
    '/update-profile': DEFAULT_DELAY,
    '/close-account': 19,

    # Transactions - Critical
    '/wire-transfer': 19,
    '/internal-transfer': DEFAULT_DELAY,
    '/pay-bill': DEFAULT_DELAY,
    '/view-transactions': DEFAULT_DELAY,

    # Investments - Critical
    '/view-portfolio': DEFAULT_DELAY,
    '/buy-stock': 19,
    '/sell-stock': 19,
    '/view-market-data': DEFAULT_DELAY,

    # Loans & Mortgages - Critical
    '/apply-loan': 19,
    '/view-loan-details': DEFAULT_DELAY,
    '/make-loan-payment': DEFAULT_DELAY,
    '/calculate-mortgage': DEFAULT_DELAY,

    # Cards & Payments - Critical
    '/view-card-details': DEFAULT_DELAY,
    '/report-lost-card': DEFAULT_DELAY,
    '/activate-card': DEFAULT_DELAY,
    '/dispute-transaction': DEFAULT_DELAY,

    # Security - Critical
    '/change-password': DEFAULT_DELAY,
    '/enable-2fa': DEFAULT_DELAY,
    '/fraud-alert': DEFAULT_DELAY,
    '/lock-account': DEFAULT_DELAY,
}

# Directory containing static files
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class FinancialHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler with slow routes for financial services RUM demonstration."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, _format, *args):
        """Custom logging with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {args[0]}")

    def send_json_response(self, data, status=200):
        """Send a JSON response."""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)

    def send_html_file(self, filepath):
        """Send an HTML file."""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, 'File not found')

    def simulate_slow_response(self, path):
        """Simulate a slow response if path is in DELAYS."""
        if path in DELAYS:
            delay = DELAYS[path]
            print(f"  ⏳ Simulating slow response ({delay}s)...")
            time.sleep(delay)
            print(f"  ✅ Response completed for {path}")
            return delay
        return 0

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Health check - always fast
        if path == '/health':
            self.send_json_response({
                'status': 'ok',
                'system': 'SecureBank Financial Services',
                'timestamp': datetime.now().isoformat()
            })
            return

        # Slow routes (page views)
        if path in DELAYS:
            self.simulate_slow_response(path)
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # API routes - fast
        if path == '/api/accounts':
            self.send_json_response({
                'accounts': [
                    {'id': 'CHK-001', 'type': 'Checking', 'balance': 12547.82},
                    {'id': 'SAV-001', 'type': 'Savings', 'balance': 45230.15},
                    {'id': 'INV-001', 'type': 'Investment', 'balance': 127845.50}
                ],
                'count': 3
            })
            return

        if path == '/api/dashboard':
            self.send_json_response({
                'totalAssets': 185623.47,
                'pendingTransactions': 3,
                'monthlySpending': 4520.33,
                'investmentGain': 2.34,
                'creditScore': 782,
                'alerts': 2
            })
            return

        # Root path
        if path == '/' or path == '/index.html':
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # Account pages
        if path.startswith('/account/'):
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # Fall back to static file serving
        super().do_GET()

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            _data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            _data = {}

        # Handle slow routes
        if path in DELAYS:
            delay = self.simulate_slow_response(path)
            delay_ms = int(delay * 1000)

            response_messages = {
                # Account Management
                '/view-account-details': 'Account details retrieved',
                '/view-statements': 'Statements retrieved',
                '/update-profile': 'Profile updated successfully',
                '/close-account': 'Account closure initiated',

                # Transactions
                '/wire-transfer': 'Wire transfer initiated successfully',
                '/internal-transfer': 'Transfer completed successfully',
                '/pay-bill': 'Bill payment processed',
                '/view-transactions': 'Transaction history retrieved',

                # Investments
                '/view-portfolio': 'Portfolio data retrieved',
                '/buy-stock': 'Stock purchase order executed',
                '/sell-stock': 'Stock sell order executed',
                '/view-market-data': 'Market data retrieved',

                # Loans
                '/apply-loan': 'Loan application submitted',
                '/view-loan-details': 'Loan details retrieved',
                '/make-loan-payment': 'Loan payment processed',
                '/calculate-mortgage': 'Mortgage calculation completed',

                # Cards
                '/view-card-details': 'Card details retrieved',
                '/report-lost-card': 'Lost card reported - card blocked',
                '/activate-card': 'Card activated successfully',
                '/dispute-transaction': 'Dispute filed successfully',

                # Security
                '/change-password': 'Password changed successfully',
                '/enable-2fa': 'Two-factor authentication enabled',
                '/fraud-alert': 'Fraud alert processed',
                '/lock-account': 'Account locked for security',
            }

            self.send_json_response({
                'success': True,
                'message': response_messages.get(path, 'Operation completed'),
                'delay': delay_ms,
                'timestamp': datetime.now().isoformat()
            })
            return

        # Unknown POST endpoint
        self.send_json_response({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def print_banner():
    """Print startup banner."""
    print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║           SecureBank Financial Services - Customer Portal             ║
║                    (RUM Demonstration System)                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{PORT}                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║  FAST ROUTES (normal response):                                       ║
║    GET  /                 - Dashboard                                 ║
║    GET  /account/:id      - Account overview                          ║
║    GET  /api/accounts     - Account list                              ║
║    GET  /api/dashboard    - Dashboard stats                           ║
║    GET  /health           - Health check                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║  SLOW ROUTES ({int(DEFAULT_DELAY * 1000)}ms delay - Critical Financial Operations):       ║
║                                                                       ║
║  Account Management:                                                  ║
║    POST /view-account-details  - View account details                 ║
║    POST /view-statements       - View statements                      ║
║    POST /update-profile        - Update profile                       ║
║    POST /close-account         - Close account (19s)                  ║
║                                                                       ║
║  Transactions:                                                        ║
║    POST /wire-transfer         - Wire transfer (19s)                  ║
║    POST /internal-transfer     - Internal transfer                    ║
║    POST /pay-bill              - Pay bill                             ║
║    POST /view-transactions     - View transactions                    ║
║                                                                       ║
║  Investments:                                                         ║
║    POST /view-portfolio        - View portfolio                       ║
║    POST /buy-stock             - Buy stock (19s)                      ║
║    POST /sell-stock            - Sell stock (19s)                     ║
║    POST /view-market-data      - View market data                     ║
║                                                                       ║
║  Loans & Mortgages:                                                   ║
║    POST /apply-loan            - Apply for loan (19s)                 ║
║    POST /view-loan-details     - View loan details                    ║
║    POST /make-loan-payment     - Make loan payment                    ║
║    POST /calculate-mortgage    - Calculate mortgage                   ║
║                                                                       ║
║  Cards & Payments:                                                    ║
║    POST /view-card-details     - View card details                    ║
║    POST /report-lost-card      - Report lost card                     ║
║    POST /activate-card         - Activate new card                    ║
║    POST /dispute-transaction   - Dispute transaction                  ║
║                                                                       ║
║  Security:                                                            ║
║    POST /change-password       - Change password                      ║
║    POST /enable-2fa            - Enable 2FA                           ║
║    POST /fraud-alert           - Report fraud                         ║
║    POST /lock-account          - Lock account                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  RUM Metrics to observe:                                              ║
║    - TTFB (Time to First Byte) - Critical for financial users         ║
║    - LCP  (Largest Contentful Paint)                                  ║
║    - INP  (Interaction to Next Paint) - Response to clicks            ║
║    - FCP  (First Contentful Paint)                                    ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


def main():
    """Start the server."""
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), FinancialHandler) as httpd:
        print_banner()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down financial services server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
