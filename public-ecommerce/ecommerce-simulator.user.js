// ==UserScript==
// @name         TechMart RUM Traffic Simulator
// @namespace    http://techmart.demo/
// @version      1.0
// @description  Simulates real user traffic on TechMart demo site for RUM demonstrations
// @author       RUM Demo
// @match        *://*/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

// ============================================================================
// INSTALLATION & USAGE GUIDE
// ============================================================================
//
// STEP 1: Install a Userscript Manager in your browser
// -----------------------------------------------------
//   - Chrome:  Tampermonkey - https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo
//   - Firefox: Greasemonkey - https://addons.mozilla.org/en-US/firefox/addon/greasemonkey/
//              or Tampermonkey - https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/
//   - Edge:    Tampermonkey - https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd
//   - Safari:  Tampermonkey - https://apps.apple.com/app/tampermonkey/id1482490089
//
// STEP 2: Install this script
// ---------------------------
//   Option A: From file
//     1. Click on Tampermonkey/Greasemonkey icon in browser toolbar
//     2. Select "Create a new script..." or "Add new script"
//     3. Delete any default code
//     4. Copy and paste the entire contents of this file
//     5. Save (Ctrl+S / Cmd+S)
//
//   Option B: Direct install (if hosted)
//     1. Open this .user.js file URL in browser
//     2. Tampermonkey will auto-detect and prompt to install
//
// STEP 3: Start the TechMart demo server
// --------------------------------------
//   cd /path/to/rum_app
//   python3 ecommerce-server.py
//
// STEP 4: Open the demo site
// --------------------------
//   Navigate to: http://localhost:3000
//   The simulator will auto-start in 3 seconds
//
// ============================================================================
// FEATURES
// ============================================================================
//
//   - Auto-start:      Begins simulation automatically after 3 seconds
//   - Visual overlay:  Shows status, cycle count, actions performed, runtime
//   - Full user flow:  Browse -> Add to Cart -> Buy -> Payment -> Checkout
//   - Continuous loop: Repeats the entire flow indefinitely
//   - Controls:        Start/Pause/Stop buttons in the overlay panel
//   - Smart waits:     Waits for 6-second server delays before continuing
//
// ============================================================================
// SIMULATION FLOW (per cycle)
// ============================================================================
//
//   1.  Browse home page
//   2.  Scroll to products
//   3.  Add Laptop to cart         (triggers 6s delay)
//   4.  Add Headphones to cart     (triggers 6s delay)
//   5.  View deals section
//   6.  Add Keyboard to cart       (triggers 6s delay)
//   7.  Open cart -> Checkout      (triggers 6s delay)
//   8.  Buy Watch                  (triggers 6s delay)
//   9.  Add Tablet to cart         (triggers 6s delay)
//   10. Open cart -> Payment       (triggers 6s delay)
//   11. Repeat from step 1...
//
// ============================================================================
// CONSOLE API (for manual control)
// ============================================================================
//
//   rumSimulator.start()                    // Start the simulation
//   rumSimulator.stop()                     // Stop the simulation
//   rumSimulator.togglePause()              // Pause or resume
//   rumSimulator.getState()                 // Get current state object
//   rumSimulator.setConfig('loopDelay', 3000)   // Change delay between actions
//   rumSimulator.setConfig('autoStart', false)  // Disable auto-start
//
// ============================================================================
// CONFIGURATION OPTIONS (modify in CONFIG object below)
// ============================================================================
//
//   enabled:              true/false - Master toggle for simulation
//   loopDelay:            ms - Delay between actions (default: 2000)
//   loopPauseAfterCycle:  ms - Pause after completing full cycle (default: 5000)
//   randomizeDelays:      true/false - Add randomness to delays
//   maxRandomDelay:       ms - Max additional random delay (default: 1500)
//   autoStart:            true/false - Start automatically on page load
//   logToConsole:         true/false - Log actions to browser console
//   showOverlay:          true/false - Show visual status panel
//
// ============================================================================

(function() {
    'use strict';

    // ========================================
    // CONFIGURATION
    // ========================================
    const CONFIG = {
        enabled: true,                    // Toggle simulation on/off
        loopDelay: 2000,                  // Delay between actions (ms)
        loopPauseAfterCycle: 5000,        // Pause after completing a full cycle (ms)
        randomizeDelays: true,            // Add randomness to delays
        maxRandomDelay: 1500,             // Max additional random delay (ms)
        autoStart: true,                  // Start simulation automatically
        logToConsole: true,               // Log actions to console
        showOverlay: true,                // Show status overlay on page
        simulateScrolling: true,          // Simulate page scrolling
        simulateMouseMovement: true,      // Simulate mouse movements
    };

    // Actions to perform in sequence
    const ACTIONS = [
        { name: 'Browse Home', type: 'browse', duration: 3000 },
        { name: 'View Product 1', type: 'scroll', target: '.product-card:nth-child(1)', duration: 2000 },
        { name: 'Add to Cart - Laptop', type: 'click', target: 'addToCart-laptop-pro' },
        { name: 'Browse More', type: 'scroll', target: '.product-card:nth-child(3)', duration: 2000 },
        { name: 'Add to Cart - Headphones', type: 'click', target: 'addToCart-headphones-pro' },
        { name: 'View Deals', type: 'scroll', target: '.deals-section', duration: 2000 },
        { name: 'Add Deal Item', type: 'click', target: 'addToCart-keyboard-rgb' },
        { name: 'Open Cart', type: 'function', action: 'openCart' },
        { name: 'Proceed to Checkout', type: 'function', action: 'checkout' },
        { name: 'Browse Again', type: 'scroll', target: '.hero', duration: 2000 },
        { name: 'Buy Now - Watch', type: 'click', target: 'buyNow-watch-ultra' },
        { name: 'Add Another Item', type: 'click', target: 'addToCart-tablet-pro' },
        { name: 'Open Cart Again', type: 'function', action: 'openCart' },
        { name: 'Go to Payment', type: 'function', action: 'payment' },
    ];

    // ========================================
    // STATE
    // ========================================
    let state = {
        running: false,
        paused: false,
        currentActionIndex: 0,
        cycleCount: 0,
        totalActions: 0,
        startTime: null,
    };

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================
    function log(message, type = 'info') {
        if (!CONFIG.logToConsole) return;
        const timestamp = new Date().toLocaleTimeString();
        const prefix = `[RUM Simulator ${timestamp}]`;
        switch(type) {
            case 'error': console.error(prefix, message); break;
            case 'warn': console.warn(prefix, message); break;
            case 'success': console.log(`%c${prefix} ${message}`, 'color: #27ae60'); break;
            default: console.log(prefix, message);
        }
    }

    function getRandomDelay() {
        if (!CONFIG.randomizeDelays) return 0;
        return Math.floor(Math.random() * CONFIG.maxRandomDelay);
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms + getRandomDelay()));
    }

    function simulateMouseMove(element) {
        if (!CONFIG.simulateMouseMovement || !element) return;
        const rect = element.getBoundingClientRect();
        const event = new MouseEvent('mouseover', {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: rect.left + rect.width / 2,
            clientY: rect.top + rect.height / 2
        });
        element.dispatchEvent(event);
    }

    function smoothScrollTo(element) {
        if (!element) return Promise.resolve();
        return new Promise(resolve => {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(resolve, 500);
        });
    }

    // ========================================
    // STATUS OVERLAY
    // ========================================
    function createOverlay() {
        if (!CONFIG.showOverlay) return;

        const overlay = document.createElement('div');
        overlay.id = 'rum-simulator-overlay';
        overlay.innerHTML = `
            <style>
                #rum-simulator-overlay {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: white;
                    padding: 15px 20px;
                    border-radius: 12px;
                    font-family: 'Inter', -apple-system, sans-serif;
                    font-size: 13px;
                    z-index: 10000;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    min-width: 280px;
                    transition: all 0.3s ease;
                }
                #rum-simulator-overlay.minimized {
                    min-width: auto;
                    padding: 10px 15px;
                }
                #rum-simulator-overlay.minimized .sim-details { display: none; }
                #rum-simulator-overlay h4 {
                    margin: 0 0 10px 0;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    font-size: 14px;
                }
                #rum-simulator-overlay .sim-status {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-right: 8px;
                    animation: pulse 1.5s infinite;
                }
                #rum-simulator-overlay .sim-status.running { background: #27ae60; }
                #rum-simulator-overlay .sim-status.paused { background: #f39c12; animation: none; }
                #rum-simulator-overlay .sim-status.stopped { background: #e74c3c; animation: none; }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                #rum-simulator-overlay .sim-details {
                    margin: 10px 0;
                    padding: 10px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 8px;
                }
                #rum-simulator-overlay .sim-row {
                    display: flex;
                    justify-content: space-between;
                    margin: 5px 0;
                }
                #rum-simulator-overlay .sim-label { opacity: 0.7; }
                #rum-simulator-overlay .sim-value { font-weight: 600; }
                #rum-simulator-overlay .sim-action {
                    background: rgba(102, 126, 234, 0.3);
                    padding: 8px;
                    border-radius: 6px;
                    margin-top: 10px;
                    text-align: center;
                }
                #rum-simulator-overlay .sim-controls {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                }
                #rum-simulator-overlay button {
                    flex: 1;
                    padding: 8px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 12px;
                    transition: all 0.2s;
                }
                #rum-simulator-overlay .btn-start { background: #27ae60; color: white; }
                #rum-simulator-overlay .btn-pause { background: #f39c12; color: white; }
                #rum-simulator-overlay .btn-stop { background: #e74c3c; color: white; }
                #rum-simulator-overlay .btn-minimize { background: rgba(255,255,255,0.2); color: white; }
                #rum-simulator-overlay button:hover { transform: scale(1.02); }
            </style>
            <h4>
                <span><span class="sim-status stopped" id="sim-status-dot"></span>RUM Traffic Simulator</span>
                <button class="btn-minimize" onclick="window.rumSimulator.toggleMinimize()">_</button>
            </h4>
            <div class="sim-details">
                <div class="sim-row">
                    <span class="sim-label">Cycles:</span>
                    <span class="sim-value" id="sim-cycles">0</span>
                </div>
                <div class="sim-row">
                    <span class="sim-label">Actions:</span>
                    <span class="sim-value" id="sim-actions">0</span>
                </div>
                <div class="sim-row">
                    <span class="sim-label">Runtime:</span>
                    <span class="sim-value" id="sim-runtime">00:00</span>
                </div>
                <div class="sim-action" id="sim-current-action">
                    Ready to start...
                </div>
            </div>
            <div class="sim-controls">
                <button class="btn-start" id="sim-btn-start" onclick="window.rumSimulator.start()">Start</button>
                <button class="btn-pause" id="sim-btn-pause" onclick="window.rumSimulator.togglePause()" style="display:none">Pause</button>
                <button class="btn-stop" id="sim-btn-stop" onclick="window.rumSimulator.stop()" style="display:none">Stop</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    function updateOverlay() {
        if (!CONFIG.showOverlay) return;

        const statusDot = document.getElementById('sim-status-dot');
        const cyclesEl = document.getElementById('sim-cycles');
        const actionsEl = document.getElementById('sim-actions');
        const runtimeEl = document.getElementById('sim-runtime');
        const btnStart = document.getElementById('sim-btn-start');
        const btnPause = document.getElementById('sim-btn-pause');
        const btnStop = document.getElementById('sim-btn-stop');

        if (statusDot) {
            statusDot.className = 'sim-status ' + (state.running ? (state.paused ? 'paused' : 'running') : 'stopped');
        }
        if (cyclesEl) cyclesEl.textContent = state.cycleCount;
        if (actionsEl) actionsEl.textContent = state.totalActions;
        if (runtimeEl && state.startTime) {
            const elapsed = Math.floor((Date.now() - state.startTime) / 1000);
            const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const secs = (elapsed % 60).toString().padStart(2, '0');
            runtimeEl.textContent = `${mins}:${secs}`;
        }

        if (btnStart && btnPause && btnStop) {
            if (state.running) {
                btnStart.style.display = 'none';
                btnPause.style.display = 'block';
                btnStop.style.display = 'block';
                btnPause.textContent = state.paused ? 'Resume' : 'Pause';
            } else {
                btnStart.style.display = 'block';
                btnPause.style.display = 'none';
                btnStop.style.display = 'none';
            }
        }
    }

    function setCurrentAction(actionName) {
        const el = document.getElementById('sim-current-action');
        if (el) el.textContent = actionName;
        updateOverlay();
    }

    // ========================================
    // ACTION HANDLERS
    // ========================================
    async function waitForLoadingToComplete() {
        // Wait for loading overlay to appear and disappear
        return new Promise(resolve => {
            const checkLoading = () => {
                const loadingOverlay = document.getElementById('loadingOverlay');
                if (loadingOverlay && loadingOverlay.classList.contains('active')) {
                    // Still loading, check again
                    setTimeout(checkLoading, 500);
                } else {
                    // Loading complete
                    resolve();
                }
            };
            // Start checking after a small delay to let loading start
            setTimeout(checkLoading, 500);
        });
    }

    async function waitForModalAndClose() {
        // Wait for success modal and close it
        return new Promise(resolve => {
            const checkModal = () => {
                const modal = document.getElementById('successModal');
                if (modal && modal.classList.contains('active')) {
                    // Modal is showing, close it after a brief view
                    setTimeout(() => {
                        if (typeof window.closeModal === 'function') {
                            window.closeModal();
                        } else {
                            modal.classList.remove('active');
                        }
                        setTimeout(resolve, 500);
                    }, 1000);
                } else {
                    // Keep checking
                    setTimeout(checkModal, 200);
                }
            };
            setTimeout(checkModal, 100);
        });
    }

    async function performAction(action) {
        if (!state.running || state.paused) return false;

        setCurrentAction(action.name);
        log(`Performing: ${action.name}`);

        switch (action.type) {
            case 'browse':
                // Just wait and simulate browsing
                await sleep(action.duration || 2000);
                break;

            case 'scroll':
                // Scroll to an element
                const scrollTarget = document.querySelector(action.target);
                if (scrollTarget) {
                    simulateMouseMove(scrollTarget);
                    await smoothScrollTo(scrollTarget);
                    await sleep(action.duration || 1500);
                }
                break;

            case 'click':
                // Find and click a button
                let button = null;
                if (action.target.startsWith('addToCart-')) {
                    const productId = action.target.replace('addToCart-', '');
                    button = findAddToCartButton(productId);
                } else if (action.target.startsWith('buyNow-')) {
                    const productId = action.target.replace('buyNow-', '');
                    button = findBuyNowButton(productId);
                }

                if (button) {
                    simulateMouseMove(button);
                    await smoothScrollTo(button);
                    await sleep(500);
                    button.click();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                } else {
                    log(`Button not found: ${action.target}`, 'warn');
                }
                break;

            case 'function':
                // Call a specific function
                await handleFunctionAction(action.action);
                break;
        }

        state.totalActions++;
        updateOverlay();
        return true;
    }

    function findAddToCartButton(productId) {
        const buttons = document.querySelectorAll('.btn-primary');
        for (const btn of buttons) {
            const onclick = btn.getAttribute('onclick') || '';
            if (onclick.includes('addToCart') && onclick.includes(productId)) {
                return btn;
            }
        }
        // Fallback: find any Add to Cart button
        return document.querySelector('.product-card .btn-primary');
    }

    function findBuyNowButton(productId) {
        const buttons = document.querySelectorAll('.btn-secondary');
        for (const btn of buttons) {
            const onclick = btn.getAttribute('onclick') || '';
            if (onclick.includes('buyNow') && onclick.includes(productId)) {
                return btn;
            }
        }
        // Fallback: find any Buy Now button
        return document.querySelector('.product-card .btn-secondary');
    }

    async function handleFunctionAction(actionName) {
        switch (actionName) {
            case 'openCart':
                if (typeof window.showCart === 'function') {
                    window.showCart();
                } else {
                    document.getElementById('cartSidebar')?.classList.add('active');
                    document.getElementById('cartOverlay')?.classList.add('active');
                }
                await sleep(1500);
                break;

            case 'checkout':
                // Make sure cart is open and has items
                if (typeof window.proceedToCheckout === 'function') {
                    window.proceedToCheckout();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
                break;

            case 'payment':
                if (typeof window.proceedToPayment === 'function') {
                    window.proceedToPayment();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
                break;

            case 'closeCart':
                if (typeof window.hideCart === 'function') {
                    window.hideCart();
                } else {
                    document.getElementById('cartSidebar')?.classList.remove('active');
                    document.getElementById('cartOverlay')?.classList.remove('active');
                }
                await sleep(500);
                break;
        }
    }

    // ========================================
    // MAIN SIMULATION LOOP
    // ========================================
    async function runSimulation() {
        state.running = true;
        state.startTime = Date.now();
        state.currentActionIndex = 0;
        state.cycleCount = 0;
        state.totalActions = 0;

        log('Simulation started', 'success');
        updateOverlay();

        // Runtime update interval
        const runtimeInterval = setInterval(() => {
            if (state.running) updateOverlay();
        }, 1000);

        while (state.running) {
            // Check if paused
            while (state.paused && state.running) {
                await sleep(500);
            }

            if (!state.running) break;

            // Get current action
            const action = ACTIONS[state.currentActionIndex];

            // Perform action
            const success = await performAction(action);

            if (!success) continue;

            // Move to next action
            state.currentActionIndex++;

            // Check if cycle complete
            if (state.currentActionIndex >= ACTIONS.length) {
                state.currentActionIndex = 0;
                state.cycleCount++;
                log(`Cycle ${state.cycleCount} completed`, 'success');
                setCurrentAction(`Cycle ${state.cycleCount} complete - pausing...`);
                await sleep(CONFIG.loopPauseAfterCycle);
            }

            // Delay between actions
            await sleep(CONFIG.loopDelay);
        }

        clearInterval(runtimeInterval);
        log('Simulation stopped');
        setCurrentAction('Stopped');
        updateOverlay();
    }

    // ========================================
    // PUBLIC API
    // ========================================
    window.rumSimulator = {
        start: function() {
            if (state.running) return;
            runSimulation();
        },

        stop: function() {
            state.running = false;
            state.paused = false;
            updateOverlay();
        },

        togglePause: function() {
            if (!state.running) return;
            state.paused = !state.paused;
            log(state.paused ? 'Simulation paused' : 'Simulation resumed');
            setCurrentAction(state.paused ? 'Paused' : 'Resuming...');
            updateOverlay();
        },

        toggleMinimize: function() {
            const overlay = document.getElementById('rum-simulator-overlay');
            if (overlay) {
                overlay.classList.toggle('minimized');
            }
        },

        getState: function() {
            return { ...state };
        },

        setConfig: function(key, value) {
            if (key in CONFIG) {
                CONFIG[key] = value;
                log(`Config updated: ${key} = ${value}`);
            }
        }
    };

    // ========================================
    // INITIALIZATION
    // ========================================
    function init() {
        log('RUM Traffic Simulator loaded');
        createOverlay();

        if (CONFIG.autoStart) {
            log('Auto-starting in 3 seconds...');
            setCurrentAction('Auto-starting in 3 seconds...');
            setTimeout(() => {
                if (CONFIG.enabled) {
                    window.rumSimulator.start();
                }
            }, 3000);
        }
    }

    // Wait for page to be fully loaded
    if (document.readyState === 'complete') {
        init();
    } else {
        window.addEventListener('load', init);
    }

})();
