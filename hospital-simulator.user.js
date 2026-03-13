// ==UserScript==
// @name         MedCare Hospital RUM Traffic Simulator
// @namespace    http://medcare.hospital.demo/
// @version      1.0
// @description  Simulates hospital staff workflow traffic for RUM demonstrations
// @author       RUM Demo
// @match        http://localhost:3001/*
// @match        http://127.0.0.1:3001/*
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
// STEP 3: Start the MedCare Hospital server
// -----------------------------------------
//   cd /path/to/rum_app
//   python3 hospital-server.py
//
// STEP 4: Open the hospital platform
// ----------------------------------
//   Navigate to: http://localhost:3001
//   The simulator will auto-start in 3 seconds
//
// ============================================================================
// SIMULATED HOSPITAL WORKFLOW (per cycle)
// ============================================================================
//
//   1.  View dashboard
//   2.  View patient record (Critical patient)     - 6s delay
//   3.  Order lab tests                            - 6s delay
//   4.  View another patient record                - 6s delay
//   5.  Prescribe medication                       - 6s delay
//   6.  Check lab results                          - 6s delay
//   7.  Perform ER triage                          - 6s delay
//   8.  Admit new patient                          - 6s delay
//   9.  Discharge ready patient                    - 6s delay
//   10. Schedule appointment                       - 6s delay
//   11. Repeat from step 1...
//
// ============================================================================
// CONSOLE API
// ============================================================================
//
//   hospitalSimulator.start()           // Start the simulation
//   hospitalSimulator.stop()            // Stop the simulation
//   hospitalSimulator.togglePause()     // Pause or resume
//   hospitalSimulator.getState()        // Get current state
//   hospitalSimulator.setConfig('loopDelay', 3000)  // Change settings
//
// ============================================================================

(function() {
    'use strict';

    // ========================================
    // CONFIGURATION
    // ========================================
    const CONFIG = {
        enabled: true,
        loopDelay: 2000,
        loopPauseAfterCycle: 5000,
        randomizeDelays: true,
        maxRandomDelay: 1500,
        autoStart: true,
        logToConsole: true,
        showOverlay: true,
    };

    // Hospital workflow actions
    const ACTIONS = [
        { name: 'Review Dashboard', type: 'browse', duration: 3000 },
        { name: 'View Critical Patient Record', type: 'click', target: 'viewRecord-10045892' },
        { name: 'Order Lab Tests - Critical Patient', type: 'click', target: 'orderLab-10045892' },
        { name: 'Submit Lab Order', type: 'function', action: 'submitLabOrder' },
        { name: 'Review Monitoring Patient', type: 'click', target: 'viewRecord-10061234' },
        { name: 'Prescribe Medication', type: 'click', target: 'prescribe-10048721' },
        { name: 'Submit Prescription', type: 'function', action: 'submitPrescription' },
        { name: 'Check Lab Results', type: 'click', target: 'labResults-10033456' },
        { name: 'ER Triage Assessment', type: 'function', action: 'openTriage' },
        { name: 'Complete Triage', type: 'function', action: 'submitTriage' },
        { name: 'Admit New Patient', type: 'function', action: 'openAdmit' },
        { name: 'Submit Admission', type: 'function', action: 'submitAdmit' },
        { name: 'Discharge Patient', type: 'click', target: 'discharge-10057890' },
        { name: 'Schedule Follow-up', type: 'function', action: 'openSchedule' },
        { name: 'Submit Schedule', type: 'function', action: 'submitSchedule' },
        { name: 'View ICU Patient', type: 'click', target: 'viewRecord-10033456' },
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
        const prefix = `[Hospital Sim ${timestamp}]`;
        switch(type) {
            case 'error': console.error(prefix, message); break;
            case 'warn': console.warn(prefix, message); break;
            case 'success': console.log(`%c${prefix} ${message}`, 'color: #059669'); break;
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
        overlay.id = 'hospital-sim-overlay';
        overlay.innerHTML = `
            <style>
                #hospital-sim-overlay {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 100%);
                    color: white;
                    padding: 15px 20px;
                    border-radius: 12px;
                    font-family: 'Inter', -apple-system, sans-serif;
                    font-size: 13px;
                    z-index: 10000;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    min-width: 300px;
                    transition: all 0.3s ease;
                }
                #hospital-sim-overlay.minimized {
                    min-width: auto;
                    padding: 10px 15px;
                }
                #hospital-sim-overlay.minimized .sim-details { display: none; }
                #hospital-sim-overlay h4 {
                    margin: 0 0 10px 0;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    font-size: 14px;
                }
                #hospital-sim-overlay .sim-status {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-right: 8px;
                    animation: pulse 1.5s infinite;
                }
                #hospital-sim-overlay .sim-status.running { background: #10b981; }
                #hospital-sim-overlay .sim-status.paused { background: #f59e0b; animation: none; }
                #hospital-sim-overlay .sim-status.stopped { background: #ef4444; animation: none; }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                #hospital-sim-overlay .sim-details {
                    margin: 10px 0;
                    padding: 10px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 8px;
                }
                #hospital-sim-overlay .sim-row {
                    display: flex;
                    justify-content: space-between;
                    margin: 5px 0;
                }
                #hospital-sim-overlay .sim-label { opacity: 0.7; }
                #hospital-sim-overlay .sim-value { font-weight: 600; }
                #hospital-sim-overlay .sim-action {
                    background: rgba(59, 130, 246, 0.3);
                    padding: 8px;
                    border-radius: 6px;
                    margin-top: 10px;
                    text-align: center;
                    font-size: 12px;
                }
                #hospital-sim-overlay .sim-controls {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                }
                #hospital-sim-overlay button {
                    flex: 1;
                    padding: 8px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 12px;
                    transition: all 0.2s;
                }
                #hospital-sim-overlay .btn-start { background: #10b981; color: white; }
                #hospital-sim-overlay .btn-pause { background: #f59e0b; color: white; }
                #hospital-sim-overlay .btn-stop { background: #ef4444; color: white; }
                #hospital-sim-overlay .btn-minimize { background: rgba(255,255,255,0.2); color: white; }
                #hospital-sim-overlay button:hover { transform: scale(1.02); }
            </style>
            <h4>
                <span><span class="sim-status stopped" id="hsim-status-dot"></span>🏥 Hospital Workflow Sim</span>
                <button class="btn-minimize" onclick="window.hospitalSimulator.toggleMinimize()">_</button>
            </h4>
            <div class="sim-details">
                <div class="sim-row">
                    <span class="sim-label">Shift Cycles:</span>
                    <span class="sim-value" id="hsim-cycles">0</span>
                </div>
                <div class="sim-row">
                    <span class="sim-label">Actions:</span>
                    <span class="sim-value" id="hsim-actions">0</span>
                </div>
                <div class="sim-row">
                    <span class="sim-label">Shift Time:</span>
                    <span class="sim-value" id="hsim-runtime">00:00</span>
                </div>
                <div class="sim-action" id="hsim-current-action">
                    Ready to start shift...
                </div>
            </div>
            <div class="sim-controls">
                <button class="btn-start" id="hsim-btn-start" onclick="window.hospitalSimulator.start()">Start Shift</button>
                <button class="btn-pause" id="hsim-btn-pause" onclick="window.hospitalSimulator.togglePause()" style="display:none">Pause</button>
                <button class="btn-stop" id="hsim-btn-stop" onclick="window.hospitalSimulator.stop()" style="display:none">End Shift</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    function updateOverlay() {
        if (!CONFIG.showOverlay) return;

        const statusDot = document.getElementById('hsim-status-dot');
        const cyclesEl = document.getElementById('hsim-cycles');
        const actionsEl = document.getElementById('hsim-actions');
        const runtimeEl = document.getElementById('hsim-runtime');
        const btnStart = document.getElementById('hsim-btn-start');
        const btnPause = document.getElementById('hsim-btn-pause');
        const btnStop = document.getElementById('hsim-btn-stop');

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
        const el = document.getElementById('hsim-current-action');
        if (el) el.textContent = actionName;
        updateOverlay();
    }

    // ========================================
    // WAIT FUNCTIONS
    // ========================================
    async function waitForLoadingToComplete() {
        return new Promise(resolve => {
            const checkLoading = () => {
                const loadingOverlay = document.getElementById('loadingOverlay');
                if (loadingOverlay && loadingOverlay.classList.contains('active')) {
                    setTimeout(checkLoading, 500);
                } else {
                    resolve();
                }
            };
            setTimeout(checkLoading, 500);
        });
    }

    async function waitForModalAndClose(modalId = 'successModal') {
        return new Promise(resolve => {
            const checkModal = () => {
                const modal = document.getElementById(modalId);
                if (modal && modal.classList.contains('active')) {
                    setTimeout(() => {
                        if (typeof window.closeModal === 'function') {
                            window.closeModal(modalId);
                        } else {
                            modal.classList.remove('active');
                        }
                        setTimeout(resolve, 500);
                    }, 1000);
                } else {
                    setTimeout(checkModal, 200);
                }
            };
            setTimeout(checkModal, 100);
        });
    }

    // ========================================
    // ACTION HANDLERS
    // ========================================
    async function performAction(action) {
        if (!state.running || state.paused) return false;

        setCurrentAction(action.name);
        log(`Performing: ${action.name}`);

        switch (action.type) {
            case 'browse':
                await sleep(action.duration || 2000);
                break;

            case 'scroll':
                const scrollTarget = document.querySelector(action.target);
                if (scrollTarget) {
                    await smoothScrollTo(scrollTarget);
                    await sleep(action.duration || 1500);
                }
                break;

            case 'click':
                await handleClickAction(action.target);
                break;

            case 'function':
                await handleFunctionAction(action.action);
                break;
        }

        state.totalActions++;
        updateOverlay();
        return true;
    }

    async function handleClickAction(target) {
        // Parse target format: action-mrn
        const [actionType, mrn] = target.split('-');

        // Find patient name from card
        let patientName = 'Patient';
        const patientCards = document.querySelectorAll('.patient-card');
        for (const card of patientCards) {
            const mrnEl = card.querySelector('.patient-mrn');
            if (mrnEl && mrnEl.textContent.includes(mrn)) {
                const nameEl = card.querySelector('.patient-info h3');
                if (nameEl) patientName = nameEl.textContent;
                break;
            }
        }

        // Find and click appropriate button
        let button = null;

        switch (actionType) {
            case 'viewRecord':
                button = findButtonByAction('viewPatientRecord', mrn);
                break;
            case 'orderLab':
                button = findButtonByAction('orderLabTest', mrn);
                break;
            case 'prescribe':
                button = findButtonByAction('prescribeMedication', mrn);
                break;
            case 'labResults':
                button = findButtonByAction('viewLabResults', mrn);
                break;
            case 'discharge':
                button = findButtonByAction('dischargePatient', mrn);
                break;
            case 'triage':
                button = findButtonByAction('emergencyTriage', mrn);
                break;
        }

        if (button) {
            await smoothScrollTo(button);
            await sleep(300);
            button.click();
            await waitForLoadingToComplete();
            await waitForModalAndClose();
        } else {
            log(`Button not found for ${target}`, 'warn');
        }
    }

    function findButtonByAction(actionName, mrn) {
        const buttons = document.querySelectorAll('button');
        for (const btn of buttons) {
            const onclick = btn.getAttribute('onclick') || '';
            if (onclick.includes(actionName) && onclick.includes(mrn)) {
                return btn;
            }
        }
        return null;
    }

    async function handleFunctionAction(actionName) {
        switch (actionName) {
            case 'openTriage':
                if (typeof window.openTriageModal === 'function') {
                    window.openTriageModal();
                } else {
                    const triageModal = document.getElementById('triageModal');
                    if (triageModal) triageModal.classList.add('active');
                }
                await sleep(1000);
                break;

            case 'submitTriage':
                // Fill in triage form
                const triageHR = document.getElementById('triageHR');
                const triageBP = document.getElementById('triageBP');
                const triageSpO2 = document.getElementById('triageSpO2');
                if (triageHR) triageHR.value = '92';
                if (triageBP) triageBP.value = '138/85';
                if (triageSpO2) triageSpO2.value = '96';

                if (typeof window.submitTriage === 'function') {
                    window.submitTriage();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
                break;

            case 'openAdmit':
                if (typeof window.openAdmitModal === 'function') {
                    window.openAdmitModal();
                } else {
                    const admitModal = document.getElementById('admitModal');
                    if (admitModal) admitModal.classList.add('active');
                }
                await sleep(1000);
                break;

            case 'submitAdmit':
                // Fill in admit form
                const admitName = document.getElementById('admitName');
                const admitComplaint = document.getElementById('admitComplaint');
                if (admitName) admitName.value = 'Test Patient, Simulated';
                if (admitComplaint) admitComplaint.value = 'RUM Demo Admission';

                if (typeof window.submitAdmitPatient === 'function') {
                    window.submitAdmitPatient();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
                break;

            case 'openSchedule':
                if (typeof window.openScheduleModal === 'function') {
                    window.openScheduleModal();
                } else {
                    const scheduleModal = document.getElementById('scheduleModal');
                    if (scheduleModal) scheduleModal.classList.add('active');
                }
                await sleep(1000);
                break;

            case 'submitSchedule':
                const schedulePatient = document.getElementById('schedulePatient');
                if (schedulePatient) schedulePatient.value = 'Follow-up Patient';

                if (typeof window.submitSchedule === 'function') {
                    window.submitSchedule();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
                break;

            case 'submitLabOrder':
                if (typeof window.submitLabOrder === 'function') {
                    window.submitLabOrder();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
                break;

            case 'submitPrescription':
                const rxMed = document.getElementById('rxMedication');
                const rxDosage = document.getElementById('rxDosage');
                if (rxMed) rxMed.value = 'Amoxicillin';
                if (rxDosage) rxDosage.value = '500mg';

                if (typeof window.submitPrescription === 'function') {
                    window.submitPrescription();
                    await waitForLoadingToComplete();
                    await waitForModalAndClose();
                }
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

        log('Hospital workflow simulation started', 'success');
        updateOverlay();

        const runtimeInterval = setInterval(() => {
            if (state.running) updateOverlay();
        }, 1000);

        while (state.running) {
            while (state.paused && state.running) {
                await sleep(500);
            }

            if (!state.running) break;

            const action = ACTIONS[state.currentActionIndex];
            const success = await performAction(action);

            if (!success) continue;

            state.currentActionIndex++;

            if (state.currentActionIndex >= ACTIONS.length) {
                state.currentActionIndex = 0;
                state.cycleCount++;
                log(`Shift cycle ${state.cycleCount} completed`, 'success');
                setCurrentAction(`Cycle ${state.cycleCount} complete - brief break...`);
                await sleep(CONFIG.loopPauseAfterCycle);
            }

            await sleep(CONFIG.loopDelay);
        }

        clearInterval(runtimeInterval);
        log('Hospital workflow simulation stopped');
        setCurrentAction('Shift ended');
        updateOverlay();
    }

    // ========================================
    // PUBLIC API
    // ========================================
    window.hospitalSimulator = {
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
            const overlay = document.getElementById('hospital-sim-overlay');
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
        log('Hospital Workflow Simulator loaded');
        createOverlay();

        if (CONFIG.autoStart) {
            log('Auto-starting shift in 3 seconds...');
            setCurrentAction('Starting shift in 3 seconds...');
            setTimeout(() => {
                if (CONFIG.enabled) {
                    window.hospitalSimulator.start();
                }
            }, 3000);
        }
    }

    if (document.readyState === 'complete') {
        init();
    } else {
        window.addEventListener('load', init);
    }

})();
