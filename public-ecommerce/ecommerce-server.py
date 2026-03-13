#!/usr/bin/env python3
"""
TechMart - RUM Demo E-commerce Server
A simple HTTP server with intentionally slow routes for Real User Monitoring demos.

Usage: python3 ecommerce-server.py [port]
Default port: 3000
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
    PORT = int(os.environ.get('PORT', 3000))

# Configurable delays (in seconds)
DELAYS = {
    '/add-to-cart': 6.0,
    '/buy': 6.0,
    '/payment': 6.0,
    '/checkout': 6.0,
}

# Directory containing static files
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class RUMDemoHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler with slow routes for RUM demonstration."""

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
                'timestamp': datetime.now().isoformat()
            })
            return

        # Slow routes (page views)
        if path in DELAYS:
            self.simulate_slow_response(path)
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # API routes
        if path == '/api/cart':
            self.send_json_response({'items': [], 'total': 0})
            return

        # Root path
        if path == '/' or path == '/index.html':
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # Product pages
        if path.startswith('/product/'):
            self.send_html_file(os.path.join(STATIC_DIR, 'index.html'))
            return

        # Search
        if path == '/search':
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
                '/add-to-cart': 'Item added to cart',
                '/buy': 'Purchase initiated',
                '/payment': 'Payment processed',
                '/checkout': 'Checkout completed',
            }

            self.send_json_response({
                'success': True,
                'message': response_messages.get(path, 'Operation completed'),
                'delay': delay_ms
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
╔═══════════════════════════════════════════════════════════════╗
║           RUM Demo Store - E-commerce Simulator               ║
╠═══════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{PORT}                     ║
╠═══════════════════════════════════════════════════════════════╣
║  FAST ROUTES (normal response):                               ║
║    GET  /              - Home page                            ║
║    GET  /product/:id   - Product pages                        ║
║    GET  /search        - Search results                       ║
║    GET  /health        - Health check                         ║
╠═══════════════════════════════════════════════════════════════╣
║  SLOW ROUTES (6000ms delay - for RUM demo):                   ║
║    GET/POST  /add-to-cart  - Add item to cart                 ║
║    GET/POST  /buy          - Buy now                          ║
║    GET/POST  /payment      - Payment processing               ║
║    GET/POST  /checkout     - Checkout flow                    ║
╠═══════════════════════════════════════════════════════════════╣
║  RUM Metrics to observe:                                      ║
║    - LCP  (Largest Contentful Paint)                          ║
║    - FCP  (First Contentful Paint)                            ║
║    - TTFB (Time to First Byte) - affected by delays           ║
║    - INP  (Interaction to Next Paint)                         ║
║    - CLS  (Cumulative Layout Shift)                           ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def main():
    """Start the server."""
    # Allow socket reuse
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), RUMDemoHandler) as httpd:
        print_banner()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
