const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Configurable delays (in milliseconds)
const DELAYS = {
  '/add-to-cart': 6000,
  '/buy': 6000,
  '/payment': 6000,
  '/checkout': 6000
};

// Middleware to serve static files
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path}`);
  next();
});

// Simulate slow response helper
const simulateSlowResponse = (delayMs) => {
  return new Promise(resolve => setTimeout(resolve, delayMs));
};

// Home page - fast
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Product page - fast
app.get('/product/:id', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Search - fast
app.get('/search', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ============================================
// SLOW BUSINESS-CRITICAL ROUTES (6000ms delay)
// ============================================

// Add to Cart - SLOW
app.post('/add-to-cart', async (req, res) => {
  console.log(`  ⏳ Simulating slow response (${DELAYS['/add-to-cart']}ms)...`);
  await simulateSlowResponse(DELAYS['/add-to-cart']);
  console.log(`  ✅ Add to cart completed`);
  res.json({
    success: true,
    message: 'Item added to cart',
    delay: DELAYS['/add-to-cart']
  });
});

// Add to Cart page view - SLOW
app.get('/add-to-cart', async (req, res) => {
  console.log(`  ⏳ Simulating slow page load (${DELAYS['/add-to-cart']}ms)...`);
  await simulateSlowResponse(DELAYS['/add-to-cart']);
  console.log(`  ✅ Add to cart page loaded`);
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Buy Now - SLOW
app.post('/buy', async (req, res) => {
  console.log(`  ⏳ Simulating slow response (${DELAYS['/buy']}ms)...`);
  await simulateSlowResponse(DELAYS['/buy']);
  console.log(`  ✅ Buy completed`);
  res.json({
    success: true,
    message: 'Purchase initiated',
    delay: DELAYS['/buy']
  });
});

// Buy page view - SLOW
app.get('/buy', async (req, res) => {
  console.log(`  ⏳ Simulating slow page load (${DELAYS['/buy']}ms)...`);
  await simulateSlowResponse(DELAYS['/buy']);
  console.log(`  ✅ Buy page loaded`);
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Payment - SLOW
app.post('/payment', async (req, res) => {
  console.log(`  ⏳ Simulating slow response (${DELAYS['/payment']}ms)...`);
  await simulateSlowResponse(DELAYS['/payment']);
  console.log(`  ✅ Payment processed`);
  res.json({
    success: true,
    message: 'Payment processed',
    delay: DELAYS['/payment']
  });
});

// Payment page view - SLOW
app.get('/payment', async (req, res) => {
  console.log(`  ⏳ Simulating slow page load (${DELAYS['/payment']}ms)...`);
  await simulateSlowResponse(DELAYS['/payment']);
  console.log(`  ✅ Payment page loaded`);
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Checkout - SLOW
app.post('/checkout', async (req, res) => {
  console.log(`  ⏳ Simulating slow response (${DELAYS['/checkout']}ms)...`);
  await simulateSlowResponse(DELAYS['/checkout']);
  console.log(`  ✅ Checkout completed`);
  res.json({
    success: true,
    message: 'Checkout completed',
    delay: DELAYS['/checkout']
  });
});

// Checkout page view - SLOW
app.get('/checkout', async (req, res) => {
  console.log(`  ⏳ Simulating slow page load (${DELAYS['/checkout']}ms)...`);
  await simulateSlowResponse(DELAYS['/checkout']);
  console.log(`  ✅ Checkout page loaded`);
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ============================================
// API endpoints for cart operations
// ============================================

app.get('/api/cart', (req, res) => {
  res.json({ items: [], total: 0 });
});

// Health check - always fast
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════════════════════════════╗
║           RUM Demo Store - E-commerce Simulator               ║
╠═══════════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:${PORT}                     ║
╠═══════════════════════════════════════════════════════════════╣
║  FAST ROUTES (normal response):                               ║
║    GET  /              - Home page                            ║
║    GET  /product/:id   - Product pages                        ║
║    GET  /search        - Search results                       ║
║    GET  /health        - Health check                         ║
╠═══════════════════════════════════════════════════════════════╣
║  SLOW ROUTES (${DELAYS['/buy']}ms delay - for RUM demo):                  ║
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
  `);
});
