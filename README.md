# RUM Demo Applications

Two demo applications for Real User Monitoring (RUM) demonstrations with intentionally slow routes to observe performance metrics.

## Project Structure

```
my_apps/
├── package.json
├── public-ecommerce/          # E-commerce demo (TechMart)
│   ├── ecommerce-server.js    # Node.js server
│   ├── ecommerce-server.py    # Python server
│   ├── ecommerce-simulator.user.js  # Browser automation script
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── public-hospital/           # Hospital EHR demo (MedCare)
    ├── hospital-server.py     # Python server
    ├── hospital-simulator.user.js   # Browser automation script
    ├── index.html
    ├── styles.css
    └── app.js
```

## Quick Start

### E-commerce Demo (TechMart)

```bash
# Using Node.js
node public-ecommerce/ecommerce-server.js 3000

# Using Python
python3 public-ecommerce/ecommerce-server.py 3000
```

Then open: http://localhost:3000

### Hospital Demo (MedCare)

```bash
python3 public-hospital/hospital-server.py 3001
```

Then open: http://localhost:3001

### Using npm scripts

```bash
npm install                    # Install dependencies (for Node.js server)
npm start                      # E-commerce (Node.js) on port 3000
npm run start:ecommerce        # E-commerce (Node.js) on port 3000
npm run start:ecommerce:py     # E-commerce (Python) on port 3000
npm run start:hospital         # Hospital (Python) on port 3001
```

## Configuration

### Custom Port and Delay

All servers support custom port and delay via command line arguments:

```bash
# Usage: server [port] [delay_in_seconds/ms]

# Python servers (delay in seconds)
python3 public-ecommerce/ecommerce-server.py 3000 6      # port=3000, delay=6s
python3 public-ecommerce/ecommerce-server.py 8080 3      # port=8080, delay=3s
python3 public-hospital/hospital-server.py 3001 10       # port=3001, delay=10s

# Node.js server (delay in milliseconds)
node public-ecommerce/ecommerce-server.js 3000 6000      # port=3000, delay=6000ms
node public-ecommerce/ecommerce-server.js 8080 3000      # port=8080, delay=3000ms
```

### Environment Variables

You can also use environment variables:

```bash
# Python
PORT=3000 DELAY=6 python3 public-ecommerce/ecommerce-server.py

# Node.js
PORT=3000 DELAY=6000 node public-ecommerce/ecommerce-server.js
```

**Priority:** Command line args > Environment variables > Defaults

## Slow Routes (configurable delay, default 6 seconds)

### E-commerce
| Route | Description |
|-------|-------------|
| POST /add-to-cart | Add item to cart |
| POST /buy | Buy now |
| POST /payment | Payment processing |
| POST /checkout | Checkout flow |

### Hospital
| Route | Description |
|-------|-------------|
| POST /admit-patient | Admit new patient |
| POST /discharge-patient | Discharge patient |
| POST /transfer-patient | Transfer patient |
| POST /view-patient-record | View patient record |
| POST /update-patient-record | Update patient record |
| POST /order-lab-test | Order lab test |
| POST /prescribe-medication | Prescribe medication |
| POST /view-lab-results | View lab results |
| POST /emergency-triage | ER triage assessment |
| POST /code-blue | Code Blue alert |
| POST /schedule-appointment | Schedule appointment |
| POST /schedule-surgery | Schedule surgery |

## Browser Simulators (Userscripts)

Automated traffic simulators that run in the browser using Tampermonkey/Greasemonkey.

### Installation

1. Install [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Create a new script and paste the contents of:
   - `public-ecommerce/ecommerce-simulator.user.js` for e-commerce
   - `public-hospital/hospital-simulator.user.js` for hospital
3. Save and enable the script
4. Navigate to the demo site - simulator auto-starts in 3 seconds

### Console API

```javascript
// E-commerce simulator
rumSimulator.start()
rumSimulator.stop()
rumSimulator.togglePause()
rumSimulator.getState()
rumSimulator.setConfig('loopDelay', 3000)

// Hospital simulator
hospitalSimulator.start()
hospitalSimulator.stop()
hospitalSimulator.togglePause()
hospitalSimulator.getState()
hospitalSimulator.setConfig('loopDelay', 3000)
```

## RUM Metrics to Observe

- **TTFB** (Time to First Byte) - Affected by slow routes
- **LCP** (Largest Contentful Paint)
- **FCP** (First Contentful Paint)
- **INP** (Interaction to Next Paint) - Response to clicks
- **CLS** (Cumulative Layout Shift)

## Disclaimer

These demo applications are created by **Vikas Srivastava** for demonstration and educational purposes only. "TechMart" and "MedCare Hospital" are fictional entities. All product names, patient data, medical records, prices, and other information displayed are entirely fictitious. Any resemblance to actual companies, products, persons, or medical institutions is purely coincidental.

**Copyright © 2024 Vikas Srivastava. All rights reserved.**
