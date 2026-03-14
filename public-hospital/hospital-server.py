#!/usr/bin/env python3
"""
MedCare Hospital - Internal Platform Server
A hospital EHR/workflow simulation server with intentionally slow routes for RUM demos.

Usage: python3 hospital-server.py [port] [delay]
  port  - Server port (default: 3001)
  delay - Delay in seconds for slow routes (default: 6.0)

Examples:
  python3 hospital-server.py              # port=3001, delay=6s
  python3 hospital-server.py 8080         # port=8080, delay=6s
  python3 hospital-server.py 8080 3       # port=8080, delay=3s

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
    PORT = int(os.environ.get('PORT', 3001))

# Delay priority: command line arg > environment variable > default
if len(sys.argv) > 2:
    DEFAULT_DELAY = float(sys.argv[2])
else:
    DEFAULT_DELAY = float(os.environ.get('DELAY', 6.0))

# Configurable delays (in seconds) for critical healthcare operations
DELAYS = {
    # Patient Management - Critical
    '/admit-patient': 19,
    '/discharge-patient': DEFAULT_DELAY,
    '/transfer-patient': DEFAULT_DELAY,

    # Medical Records - Critical
    '/view-patient-record': DEFAULT_DELAY,
    '/update-patient-record': DEFAULT_DELAY,

    # Orders & Prescriptions - Critical
    '/order-lab-test': DEFAULT_DELAY,
    '/prescribe-medication': DEFAULT_DELAY,
    '/view-lab-results': DEFAULT_DELAY,

    # Emergency & Triage - Critical
    '/emergency-triage': DEFAULT_DELAY,
    '/code-blue': DEFAULT_DELAY,

    # Scheduling - Important
    '/schedule-appointment': DEFAULT_DELAY,
    '/schedule-surgery': DEFAULT_DELAY,
}

# Directory containing static files
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class HospitalHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler with slow routes for hospital RUM demonstration."""

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
                'system': 'MedCare Hospital EHR',
                'timestamp': datetime.now().isoformat()
            })
            return

        # Slow routes (page views)
        if path in DELAYS:
            self.simulate_slow_response(path)
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # API routes - fast
        if path == '/api/patients':
            self.send_json_response({'patients': [], 'count': 0})
            return

        if path == '/api/dashboard':
            self.send_json_response({
                'totalPatients': 147,
                'inER': 23,
                'inICU': 12,
                'pendingDischarges': 8,
                'pendingLabResults': 34
            })
            return

        # Root path
        if path == '/' or path == '/index.html':
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # Patient pages
        if path.startswith('/patient/'):
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
                '/admit-patient': 'Patient admitted successfully',
                '/discharge-patient': 'Patient discharged successfully',
                '/transfer-patient': 'Patient transferred successfully',
                '/view-patient-record': 'Patient record retrieved',
                '/update-patient-record': 'Patient record updated',
                '/order-lab-test': 'Lab test ordered successfully',
                '/prescribe-medication': 'Medication prescribed successfully',
                '/view-lab-results': 'Lab results retrieved',
                '/emergency-triage': 'Triage assessment completed',
                '/code-blue': 'Code Blue team alerted',
                '/schedule-appointment': 'Appointment scheduled',
                '/schedule-surgery': 'Surgery scheduled',
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
║             MedCare Hospital - Internal Platform Server               ║
║                    (RUM Demonstration System)                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{PORT}                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║  FAST ROUTES (normal response):                                       ║
║    GET  /                 - Dashboard                                 ║
║    GET  /patient/:id      - Patient overview                          ║
║    GET  /api/patients     - Patient list                              ║
║    GET  /api/dashboard    - Dashboard stats                           ║
║    GET  /health           - Health check                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║  SLOW ROUTES ({int(DEFAULT_DELAY * 1000)}ms delay - Critical Healthcare Operations):        ║
║                                                                       ║
║  Patient Management:                                                  ║
║    POST /admit-patient       - Admit new patient                      ║
║    POST /discharge-patient   - Discharge patient                      ║
║    POST /transfer-patient    - Transfer patient                       ║
║                                                                       ║
║  Medical Records:                                                     ║
║    POST /view-patient-record   - View patient record                  ║
║    POST /update-patient-record - Update patient record                ║
║                                                                       ║
║  Orders & Prescriptions:                                              ║
║    POST /order-lab-test        - Order lab test                       ║
║    POST /prescribe-medication  - Prescribe medication                 ║
║    POST /view-lab-results      - View lab results                     ║
║                                                                       ║
║  Emergency:                                                           ║
║    POST /emergency-triage  - ER triage assessment                     ║
║    POST /code-blue         - Code Blue alert                          ║
║                                                                       ║
║  Scheduling:                                                          ║
║    POST /schedule-appointment  - Schedule appointment                 ║
║    POST /schedule-surgery      - Schedule surgery                     ║
╠═══════════════════════════════════════════════════════════════════════╣
║  RUM Metrics to observe:                                              ║
║    - TTFB (Time to First Byte) - Critical for healthcare staff        ║
║    - LCP  (Largest Contentful Paint)                                  ║
║    - INP  (Interaction to Next Paint) - Response to clicks            ║
║    - FCP  (First Contentful Paint)                                    ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


def main():
    """Start the server."""
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), HospitalHandler) as httpd:
        print_banner()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down hospital server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
