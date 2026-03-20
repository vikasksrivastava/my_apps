// MedCare Hospital - Clinical Workstation JavaScript
// Hospital EHR simulation for RUM demonstration

// State
let currentPatient = null;
let timerInterval = null;

// DOM Elements
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const loadingTimer = document.getElementById('loadingTimer');

// ========================================
// Loading & Timer Functions
// ========================================
function showLoading(message) {
  loadingMessage.textContent = message;
  loadingOverlay.classList.add('active');

  let startTime = Date.now();
  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    loadingTimer.textContent = elapsed + 's';
  }, 100);
}

function hideLoading() {
  loadingOverlay.classList.remove('active');
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function showSuccess(title, message, timing) {
  document.getElementById('successTitle').textContent = title;
  document.getElementById('successMessage').textContent = message;
  document.getElementById('successTiming').textContent = timing ? `Response time: ${timing}` : '';
  document.getElementById('successModal').classList.add('active');
}

// ========================================
// Modal Functions
// ========================================
function openModal(modalId) {
  document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

function openAdmitModal() {
  openModal('admitModal');
}

function openLabOrderModal() {
  openModal('labOrderModal');
}

function openPrescribeModal() {
  openModal('prescribeModal');
}

function openTriageModal() {
  document.getElementById('triagePatientInfo').textContent = 'New ER Patient';
  openModal('triageModal');
}

function openScheduleModal() {
  openModal('scheduleModal');
}

// ========================================
// Patient Actions - SLOW OPERATIONS
// ========================================

// Admit Patient
async function submitAdmitPatient() {
  const name = document.getElementById('admitName').value || 'New Patient';
  closeModal('admitModal');
  showLoading('Admitting patient to hospital system...');

  const startTime = Date.now();
  try {
    const response = await fetch('/admit-patient', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        unit: document.getElementById('admitUnit').value,
        priority: document.getElementById('admitPriority').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Patient Admitted',
      `${name} has been admitted to ${document.getElementById('admitUnit').value}.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to admit patient. Please try again.');
  }
}

// Discharge Patient
async function dischargePatient(mrn, name) {
  showLoading(`Processing discharge for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/discharge-patient', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mrn, name })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Patient Discharged',
      `${name} (MRN: ${mrn}) has been discharged successfully.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to discharge patient. Please try again.');
  }
}

// View Patient Record
async function viewPatientRecord(mrn, name) {
  showLoading(`Loading medical record for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-patient-record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mrn, name })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Record Retrieved',
      `Medical record for ${name} (MRN: ${mrn}) loaded successfully.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to load patient record. Please try again.');
  }
}

// Update Patient Record
async function updatePatientRecord(mrn, name) {
  showLoading(`Updating record for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/update-patient-record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mrn, name, timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Record Updated',
      `Medical record for ${name} has been updated.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to update patient record. Please try again.');
  }
}

// Order Lab Test
function orderLabTest(mrn, name) {
  currentPatient = { mrn, name };
  document.getElementById('labPatientInfo').textContent = `Patient: ${name} (MRN: ${mrn})`;
  openModal('labOrderModal');
}

async function submitLabOrder() {
  closeModal('labOrderModal');
  const name = currentPatient?.name || 'Patient';
  const mrn = currentPatient?.mrn || 'Unknown';

  showLoading(`Submitting lab orders for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/order-lab-test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mrn,
        name,
        priority: document.getElementById('labPriority').value,
        tests: ['CBC', 'CMP']
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Lab Orders Submitted',
      `Lab tests ordered for ${name}. Priority: ${document.getElementById('labPriority').value}`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to submit lab orders. Please try again.');
  }
}

// View Lab Results
async function viewLabResults(mrn, name) {
  showLoading(`Retrieving lab results for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-lab-results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mrn, name })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Lab Results Retrieved',
      `Lab results for ${name} (MRN: ${mrn}) are now available.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to retrieve lab results. Please try again.');
  }
}

// Prescribe Medication
function prescribeMedication(mrn, name) {
  currentPatient = { mrn, name };
  document.getElementById('prescribePatientInfo').textContent = `Patient: ${name} (MRN: ${mrn})`;
  openModal('prescribeModal');
}

async function submitPrescription() {
  closeModal('prescribeModal');
  const name = currentPatient?.name || 'Patient';
  const mrn = currentPatient?.mrn || 'Unknown';
  const medication = document.getElementById('rxMedication').value || 'Medication';

  showLoading(`Prescribing ${medication} for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/prescribe-medication', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mrn,
        name,
        medication,
        dosage: document.getElementById('rxDosage').value,
        route: document.getElementById('rxRoute').value,
        frequency: document.getElementById('rxFrequency').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Medication Prescribed',
      `${medication} prescribed for ${name}.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to prescribe medication. Please try again.');
  }
}

// Emergency Triage
function emergencyTriage(mrn, name) {
  currentPatient = { mrn, name };
  document.getElementById('triagePatientInfo').textContent = `Patient: ${name} (MRN: ${mrn})`;
  openModal('triageModal');
}

async function submitTriage() {
  closeModal('triageModal');
  const name = currentPatient?.name || 'ER Patient';
  const mrn = currentPatient?.mrn || 'New';
  const level = document.getElementById('triageLevel').value;

  showLoading(`Completing triage assessment for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/emergency-triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mrn,
        name,
        triageLevel: level,
        vitals: {
          hr: document.getElementById('triageHR').value,
          bp: document.getElementById('triageBP').value,
          spo2: document.getElementById('triageSpO2').value,
          temp: document.getElementById('triageTemp').value
        }
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Triage Complete',
      `${name} triaged as ESI-${level}.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to complete triage. Please try again.');
  }
}

// Code Blue
async function handleCodeBlue() {
  showLoading('ACTIVATING CODE BLUE RESPONSE TEAM...');

  const startTime = Date.now();
  try {
    const response = await fetch('/code-blue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location: 'ICU-205',
        timestamp: new Date().toISOString()
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'CODE BLUE ACTIVATED',
      'Code Blue team has been alerted. Response team en route.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to activate Code Blue. Call manually!');
  }
}

// Schedule Appointment
async function submitSchedule() {
  closeModal('scheduleModal');
  const patient = document.getElementById('schedulePatient').value || 'Patient';

  showLoading(`Scheduling appointment for ${patient}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/schedule-appointment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient,
        type: document.getElementById('scheduleType').value,
        date: document.getElementById('scheduleDate').value,
        time: document.getElementById('scheduleTime').value,
        provider: document.getElementById('scheduleProvider').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Appointment Scheduled',
      `Appointment scheduled for ${patient}.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to schedule appointment. Please try again.');
  }
}

// Schedule Surgery
async function scheduleSurgery(mrn, name) {
  showLoading(`Scheduling surgery for ${name}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/schedule-surgery', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mrn, name })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Surgery Scheduled',
      `Surgery has been scheduled for ${name}.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to schedule surgery. Please try again.');
  }
}

// ========================================
// Navigation
// ========================================
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', function() {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    this.classList.add('active');
  });
});

// ========================================
// Console Logging for RUM
// ========================================
console.log('MedCare Hospital EHR loaded at:', new Date().toISOString());
console.log('This system demonstrates RUM metrics for healthcare applications.');
console.log('\nSlow routes (6000ms delay) - Critical Healthcare Operations:');
console.log('  Patient Management:');
console.log('    - /admit-patient');
console.log('    - /discharge-patient');
console.log('    - /transfer-patient');
console.log('  Medical Records:');
console.log('    - /view-patient-record');
console.log('    - /update-patient-record');
console.log('  Orders & Prescriptions:');
console.log('    - /order-lab-test');
console.log('    - /prescribe-medication');
console.log('    - /view-lab-results');
console.log('  Emergency:');
console.log('    - /emergency-triage');
console.log('    - /code-blue');
console.log('  Scheduling:');
console.log('    - /schedule-appointment');
console.log('    - /schedule-surgery');

// Track Web Vitals
if (typeof PerformanceObserver !== 'undefined') {
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime.toFixed(2), 'ms');
    });
    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}

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
}
