// TechMart E-commerce Demo - Client Side JavaScript
// This simulates an e-commerce site for RUM demonstration

// Cart State
let cart = [];
let timerInterval = null;

// DOM Elements
const cartOverlay = document.getElementById('cartOverlay');
const cartSidebar = document.getElementById('cartSidebar');
const cartItems = document.getElementById('cartItems');
const cartCount = document.getElementById('cartCount');
const cartTotal = document.getElementById('cartTotal');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const loadingTimer = document.getElementById('loadingTimer');
const successModal = document.getElementById('successModal');
const modalTitle = document.getElementById('modalTitle');
const modalMessage = document.getElementById('modalMessage');
const modalTiming = document.getElementById('modalTiming');

// Product Images Map (for cart display)
const productImages = {
  'laptop-pro': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=100&h=100&fit=crop',
  'watch-ultra': 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=100&h=100&fit=crop',
  'headphones-pro': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=100&h=100&fit=crop',
  'tablet-pro': 'https://images.unsplash.com/photo-1585298723682-7115561c51b7?w=100&h=100&fit=crop',
  'console-x': 'https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=100&h=100&fit=crop',
  'earbuds-pro': 'https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=100&h=100&fit=crop',
  'keyboard-rgb': 'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=100&h=100&fit=crop',
  'webcam-4k': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=100&h=100&fit=crop',
  'usbc-hub': 'https://images.unsplash.com/photo-1625723044792-44de16ccb4e9?w=100&h=100&fit=crop'
};

// Show Loading with Timer
function showLoading(message) {
  loadingMessage.textContent = message;
  loadingOverlay.classList.add('active');

  let startTime = Date.now();
  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    loadingTimer.textContent = elapsed + 's';
  }, 100);
}

// Hide Loading
function hideLoading() {
  loadingOverlay.classList.remove('active');
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

// Show Success Modal
function showSuccess(title, message, timing) {
  modalTitle.textContent = title;
  modalMessage.textContent = message;
  modalTiming.textContent = timing ? `Response time: ${timing}` : '';
  successModal.classList.add('active');
}

// Close Modal
function closeModal() {
  successModal.classList.remove('active');
}

// Update Cart UI
function updateCartUI() {
  cartCount.textContent = cart.length;

  if (cart.length === 0) {
    cartItems.innerHTML = '<p class="empty-cart">Your cart is empty</p>';
    cartTotal.textContent = '$0.00';
    return;
  }

  let total = 0;
  cartItems.innerHTML = cart.map((item, index) => {
    total += item.price;
    return `
      <div class="cart-item">
        <img src="${productImages[item.id] || 'https://via.placeholder.com/80'}" alt="${item.name}" class="cart-item-image">
        <div class="cart-item-info">
          <div class="cart-item-title">${item.name}</div>
          <div class="cart-item-price">$${item.price.toFixed(2)}</div>
        </div>
        <button class="cart-item-remove" onclick="removeFromCart(${index})">&times;</button>
      </div>
    `;
  }).join('');

  cartTotal.textContent = '$' + total.toFixed(2);
}

// Show Cart
function showCart() {
  cartOverlay.classList.add('active');
  cartSidebar.classList.add('active');
}

// Hide Cart
function hideCart() {
  cartOverlay.classList.remove('active');
  cartSidebar.classList.remove('active');
}

// Remove from Cart
function removeFromCart(index) {
  cart.splice(index, 1);
  updateCartUI();
}

// Add to Cart - SLOW OPERATION
async function addToCart(productId, productName, price) {
  showLoading('Adding to cart...');

  const startTime = Date.now();

  try {
    const response = await fetch('/add-to-cart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ productId, productName, price })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

    hideLoading();

    // Add to local cart
    cart.push({ id: productId, name: productName, price });
    updateCartUI();

    showSuccess(
      'Added to Cart!',
      `${productName} has been added to your cart.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );

  } catch (error) {
    hideLoading();
    console.error('Error adding to cart:', error);
    alert('Failed to add item to cart. Please try again.');
  }
}

// Buy Now - SLOW OPERATION
async function buyNow(productId, productName, price) {
  showLoading('Processing purchase...');

  const startTime = Date.now();

  try {
    const response = await fetch('/buy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ productId, productName, price })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

    hideLoading();

    showSuccess(
      'Purchase Initiated!',
      `Your order for ${productName} is being processed.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );

  } catch (error) {
    hideLoading();
    console.error('Error processing purchase:', error);
    alert('Failed to process purchase. Please try again.');
  }
}

// Proceed to Checkout - SLOW OPERATION
async function proceedToCheckout() {
  if (cart.length === 0) {
    alert('Your cart is empty!');
    return;
  }

  hideCart();
  showLoading('Loading checkout...');

  const startTime = Date.now();

  try {
    const response = await fetch('/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ items: cart })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

    hideLoading();

    showSuccess(
      'Checkout Complete!',
      `Your order with ${cart.length} item(s) has been placed.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );

    // Clear cart after successful checkout
    cart = [];
    updateCartUI();

  } catch (error) {
    hideLoading();
    console.error('Error during checkout:', error);
    alert('Checkout failed. Please try again.');
  }
}

// Proceed to Payment - SLOW OPERATION
async function proceedToPayment() {
  if (cart.length === 0) {
    alert('Your cart is empty!');
    return;
  }

  hideCart();
  showLoading('Processing payment...');

  const startTime = Date.now();

  try {
    const response = await fetch('/payment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        items: cart,
        total: cart.reduce((sum, item) => sum + item.price, 0)
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);

    hideLoading();

    showSuccess(
      'Payment Processed!',
      `Payment of $${cart.reduce((sum, item) => sum + item.price, 0).toFixed(2)} completed.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );

    // Clear cart after successful payment
    cart = [];
    updateCartUI();

  } catch (error) {
    hideLoading();
    console.error('Error processing payment:', error);
    alert('Payment failed. Please try again.');
  }
}

// Search Handler
function handleSearch() {
  const query = document.getElementById('searchInput').value;
  if (query.trim()) {
    alert(`Search for: "${query}"\n\nNote: This is a demo site. Search functionality is simulated.`);
  }
}

// Scroll to Products
function scrollToProducts() {
  document.getElementById('products').scrollIntoView({ behavior: 'smooth' });
}

// Handle Enter key in search
document.getElementById('searchInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    handleSearch();
  }
});

// Close modal on overlay click
successModal.addEventListener('click', function(e) {
  if (e.target === successModal) {
    closeModal();
  }
});

// Log page load for RUM observation
console.log('TechMart Demo loaded at:', new Date().toISOString());
console.log('This site demonstrates RUM metrics. Watch for:');
console.log('  - LCP (Largest Contentful Paint)');
console.log('  - FCP (First Contentful Paint)');
console.log('  - TTFB (Time to First Byte)');
console.log('  - INP (Interaction to Next Paint)');
console.log('  - CLS (Cumulative Layout Shift)');
console.log('\nSlow routes (6000ms delay):');
console.log('  - /add-to-cart');
console.log('  - /buy');
console.log('  - /payment');
console.log('  - /checkout');

// Track Web Vitals if available
if (typeof PerformanceObserver !== 'undefined') {
  // LCP
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime.toFixed(2), 'ms');
    });
    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}

  // FCP
  try {
    const fcpObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          console.log('FCP:', entry.startTime.toFixed(2), 'ms');
        }
      }
    });
    fcpObserver.observe({ type: 'paint', buffered: true });
  } catch (e) {}

  // CLS
  try {
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          console.log('CLS update:', clsValue.toFixed(4));
        }
      }
    });
    clsObserver.observe({ type: 'layout-shift', buffered: true });
  } catch (e) {}
}
