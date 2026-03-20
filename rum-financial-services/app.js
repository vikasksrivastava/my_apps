// SecureBank Financial Services - Customer Portal JavaScript
// Banking/Financial services simulation for RUM demonstration

// State
let currentAccount = null;
let currentTradeType = 'buy';
let currentTransferType = 'internal';
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

function openTransferModal() {
  openModal('transferModal');
}

function openPayBillModal() {
  openModal('payBillModal');
}

function openInvestModal() {
  openModal('investModal');
}

function openLoanModal() {
  openModal('loanModal');
}

function openMortgageCalcModal() {
  openModal('mortgageCalcModal');
}

// ========================================
// Transfer Type Selection
// ========================================
function selectTransferType(type) {
  currentTransferType = type;
  document.querySelectorAll('.transfer-tab').forEach(tab => tab.classList.remove('active'));
  event.target.classList.add('active');

  const wireDetails = document.getElementById('wireDetails');
  if (type === 'wire') {
    wireDetails.style.display = 'block';
  } else {
    wireDetails.style.display = 'none';
  }
}

function selectTradeType(type) {
  currentTradeType = type;
  document.querySelectorAll('.trade-tab').forEach(tab => tab.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tradeButton').textContent = type === 'buy' ? 'Place Buy Order' : 'Place Sell Order';
}

// ========================================
// Account Actions - SLOW OPERATIONS
// ========================================

// View Account Details
async function viewAccountDetails(accountId, accountName) {
  showLoading(`Loading account details for ${accountName}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-account-details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accountId, accountName })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Account Details Retrieved',
      `Details for ${accountName} (${accountId}) loaded successfully.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to load account details. Please try again.');
  }
}

// View Statements
async function viewStatements(accountId, accountName) {
  showLoading(`Retrieving statements for ${accountName}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-statements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accountId, accountName })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Statements Retrieved',
      `Statements for ${accountName} are now available.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to retrieve statements. Please try again.');
  }
}

// View Transactions
async function viewTransactions(accountId, accountName) {
  showLoading(`Loading transactions for ${accountName}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accountId, accountName })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Transactions Retrieved',
      `Transaction history for ${accountName} loaded.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to load transactions. Please try again.');
  }
}

// Internal Transfer
async function internalTransfer(accountId, accountName) {
  currentAccount = { accountId, accountName };
  openTransferModal();
}

// Submit Transfer
async function submitTransfer() {
  closeModal('transferModal');
  const amount = document.getElementById('transferAmount').value || '0';
  const fromAccount = document.getElementById('transferFrom').value;
  const toAccount = document.getElementById('transferTo').value;

  const isWire = currentTransferType === 'wire' || toAccount === 'external';
  const endpoint = isWire ? '/wire-transfer' : '/internal-transfer';
  const transferType = isWire ? 'Wire Transfer' : 'Internal Transfer';

  showLoading(`Processing ${transferType} of $${amount}...`);

  const startTime = Date.now();
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: fromAccount,
        to: toAccount,
        amount: parseFloat(amount),
        type: transferType,
        memo: document.getElementById('transferMemo').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      `${transferType} Completed`,
      `$${parseFloat(amount).toFixed(2)} has been transferred successfully.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Transfer failed. Please try again.');
  }
}

// Pay Bill
function payBill(accountId, accountName) {
  currentAccount = { accountId, accountName };
  document.getElementById('billPayeeInfo').textContent = `Payee: ${accountName}`;
  openPayBillModal();
}

function payBillDirect(billId, payee, amount) {
  document.getElementById('billPayeeInfo').textContent = `Payee: ${payee}`;
  document.getElementById('billAmount').value = amount;
  currentAccount = { billId, payee };
  openPayBillModal();
}

async function submitBillPayment() {
  closeModal('payBillModal');
  const payee = currentAccount?.payee || 'Payee';
  const amount = document.getElementById('billAmount').value || '0';

  showLoading(`Processing payment to ${payee}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/pay-bill', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payee,
        amount: parseFloat(amount),
        fromAccount: document.getElementById('billFromAccount').value,
        date: document.getElementById('billDate').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Bill Payment Processed',
      `$${parseFloat(amount).toFixed(2)} payment to ${payee} completed.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Bill payment failed. Please try again.');
  }
}

// ========================================
// Investment Actions
// ========================================

// View Portfolio
async function viewPortfolio(accountId, accountName) {
  showLoading(`Loading portfolio for ${accountName}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-portfolio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accountId, accountName })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Portfolio Retrieved',
      `Investment portfolio for ${accountName} loaded.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to load portfolio. Please try again.');
  }
}

// View Market Data
async function viewMarketData() {
  showLoading('Fetching real-time market data...');

  const startTime = Date.now();
  try {
    const response = await fetch('/view-market-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Market Data Retrieved',
      'Real-time market data has been loaded.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to fetch market data. Please try again.');
  }
}

// Submit Trade (Buy/Sell Stock)
async function submitTrade() {
  closeModal('investModal');
  const symbol = document.getElementById('stockSymbol').value.toUpperCase() || 'AAPL';
  const shares = document.getElementById('stockShares').value || '0';
  const orderType = document.getElementById('orderType').value;

  const endpoint = currentTradeType === 'buy' ? '/buy-stock' : '/sell-stock';
  const action = currentTradeType === 'buy' ? 'Buy' : 'Sell';

  showLoading(`Executing ${action} order for ${shares} shares of ${symbol}...`);

  const startTime = Date.now();
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol,
        shares: parseInt(shares),
        orderType,
        limitPrice: document.getElementById('limitPrice').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      `${action} Order Executed`,
      `${action} order for ${shares} shares of ${symbol} completed.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Trade execution failed. Please try again.');
  }
}

// ========================================
// Loan Actions
// ========================================

// View Loan Details
async function viewLoanDetails(loanId, loanName) {
  showLoading(`Loading loan details for ${loanName}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-loan-details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ loanId, loanName })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Loan Details Retrieved',
      `Details for ${loanName} loaded successfully.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to load loan details. Please try again.');
  }
}

// Make Loan Payment
async function makeLoanPayment(loanId, loanName) {
  showLoading(`Processing payment for ${loanName}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/make-loan-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ loanId, loanName, timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Payment Processed',
      `Payment for ${loanName} has been processed.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Payment failed. Please try again.');
  }
}

// Submit Loan Application
async function submitLoanApplication() {
  closeModal('loanModal');
  const loanType = document.getElementById('loanType').value;
  const amount = document.getElementById('loanAmount').value || '0';

  showLoading(`Submitting ${loanType} application...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/apply-loan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: loanType,
        amount: parseFloat(amount),
        term: document.getElementById('loanTerm').value,
        purpose: document.getElementById('loanPurpose').value,
        income: document.getElementById('annualIncome').value,
        employment: document.getElementById('employmentStatus').value
      })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Application Submitted',
      `Your ${loanType} application for $${parseFloat(amount).toLocaleString()} has been submitted. You will receive a decision within 2-3 business days.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Application submission failed. Please try again.');
  }
}

// Calculate Mortgage
async function calculateMortgage() {
  const homePrice = parseFloat(document.getElementById('homePrice').value) || 0;
  const downPayment = parseFloat(document.getElementById('downPayment').value) || 0;
  const rate = parseFloat(document.getElementById('interestRate').value) || 0;
  const termYears = parseInt(document.getElementById('mortgageTerm').value) || 30;

  showLoading('Calculating mortgage details...');

  const startTime = Date.now();
  try {
    const response = await fetch('/calculate-mortgage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ homePrice, downPayment, rate, termYears })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    // Calculate mortgage locally for display
    const principal = homePrice - downPayment;
    const monthlyRate = rate / 100 / 12;
    const numPayments = termYears * 12;

    let monthlyPayment;
    if (monthlyRate === 0) {
      monthlyPayment = principal / numPayments;
    } else {
      monthlyPayment = principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / (Math.pow(1 + monthlyRate, numPayments) - 1);
    }

    const totalCost = monthlyPayment * numPayments;
    const totalInterest = totalCost - principal;

    document.getElementById('monthlyPayment').textContent = '$' + monthlyPayment.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    document.getElementById('totalInterest').textContent = '$' + totalInterest.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    document.getElementById('totalCost').textContent = '$' + totalCost.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

    showSuccess(
      'Calculation Complete',
      `Monthly payment: $${monthlyPayment.toFixed(2)}`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Calculation failed. Please try again.');
  }
}

// ========================================
// Card Actions
// ========================================

// View Card Details
async function viewCardDetails(cardId, cardName) {
  currentAccount = { cardId, cardName };
  showLoading(`Loading card details...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/view-card-details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cardId, cardName })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Card Details Retrieved',
      `Details for ${cardName || 'your card'} loaded.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to load card details. Please try again.');
  }
}

// Activate Card
async function activateCard() {
  closeModal('cardModal');
  showLoading('Activating your new card...');

  const startTime = Date.now();
  try {
    const response = await fetch('/activate-card', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Card Activated',
      'Your new card has been activated and is ready to use.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Card activation failed. Please try again.');
  }
}

// Report Lost Card
async function reportLostCard() {
  closeModal('cardModal');
  showLoading('Reporting lost card and blocking transactions...');

  const startTime = Date.now();
  try {
    const response = await fetch('/report-lost-card', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Card Blocked',
      'Your card has been reported lost/stolen and blocked. A replacement card will be mailed to you.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to report lost card. Please call customer service.');
  }
}

// Dispute Transaction
async function disputeTransaction(txnId, merchant) {
  showLoading(`Filing dispute for ${merchant || 'transaction'}...`);

  const startTime = Date.now();
  try {
    const response = await fetch('/dispute-transaction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ txnId, merchant, timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Dispute Filed',
      `Your dispute for ${merchant || 'this transaction'} has been filed. You will receive a response within 10 business days.`,
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to file dispute. Please try again.');
  }
}

// ========================================
// Security Actions
// ========================================

// Change Password
async function changePassword() {
  closeModal('securityModal');
  showLoading('Updating your password...');

  const startTime = Date.now();
  try {
    const response = await fetch('/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Password Changed',
      'Your password has been updated successfully.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Password change failed. Please try again.');
  }
}

// Enable 2FA
async function enable2FA() {
  closeModal('securityModal');
  showLoading('Enabling two-factor authentication...');

  const startTime = Date.now();
  try {
    const response = await fetch('/enable-2fa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      '2FA Enabled',
      'Two-factor authentication has been enabled for your account.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to enable 2FA. Please try again.');
  }
}

// Lock Account
async function lockAccount() {
  closeModal('securityModal');
  showLoading('Locking your account...');

  const startTime = Date.now();
  try {
    const response = await fetch('/lock-account', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'Account Locked',
      'Your account has been locked. Contact customer service to unlock.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to lock account. Please try again.');
  }
}

// Fraud Alert
async function handleFraudAlert() {
  showLoading('Processing fraud alert...');

  const startTime = Date.now();
  try {
    const response = await fetch('/fraud-alert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: new Date().toISOString() })
    });

    const data = await response.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    hideLoading();

    showSuccess(
      'FRAUD ALERT PROCESSED',
      'Our fraud prevention team has been notified. Your accounts are being monitored.',
      `${elapsed} seconds (Server delay: ${data.delay}ms)`
    );
  } catch (error) {
    hideLoading();
    alert('Failed to process fraud alert. Please call 1-800-SECURE.');
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
console.log('SecureBank Financial Services loaded at:', new Date().toISOString());
console.log('This system demonstrates RUM metrics for financial applications.');
console.log('\nSlow routes (6000-19000ms delay) - Critical Financial Operations:');
console.log('  Account Management:');
console.log('    - /view-account-details');
console.log('    - /view-statements');
console.log('    - /update-profile');
console.log('    - /close-account (19s)');
console.log('  Transactions:');
console.log('    - /wire-transfer (19s)');
console.log('    - /internal-transfer');
console.log('    - /pay-bill');
console.log('    - /view-transactions');
console.log('  Investments:');
console.log('    - /view-portfolio');
console.log('    - /buy-stock (19s)');
console.log('    - /sell-stock (19s)');
console.log('    - /view-market-data');
console.log('  Loans & Mortgages:');
console.log('    - /apply-loan (19s)');
console.log('    - /view-loan-details');
console.log('    - /make-loan-payment');
console.log('    - /calculate-mortgage');
console.log('  Cards & Payments:');
console.log('    - /view-card-details');
console.log('    - /report-lost-card');
console.log('    - /activate-card');
console.log('    - /dispute-transaction');
console.log('  Security:');
console.log('    - /change-password');
console.log('    - /enable-2fa');
console.log('    - /fraud-alert');
console.log('    - /lock-account');

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
