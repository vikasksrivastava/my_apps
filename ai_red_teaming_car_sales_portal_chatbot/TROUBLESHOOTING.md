# Troubleshooting Guide - Car Sales Portal Chatbot

This guide provides curl-based commands to test and troubleshoot all components of the application.

## Prerequisites

Make sure the application is running:
```bash
cd ai_red_teaming_car_sales_portal_chatbot
./setup.sh
```

Or manually:
```bash
source venv/bin/activate
python app.py
```

---

## 1. Health & Status Checks

### Check Application Health
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

Expected output:
```json
{
    "ok": true,
    "model": "qwen2.5:3b",
    "embed_model": "nomic-embed-text",
    "openai_base_url": "http://localhost:11434/v1"
}
```

### Check Ollama Status
```bash
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

### List Available Ollama Models
```bash
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=json.load(sys.stdin)['models']; print('\n'.join([m['name'] for m in models]))"
```

---

## 2. MCP Tools Testing

### List All Available MCP Tools
```bash
curl -s http://localhost:8000/api/tools | python3 -m json.tool
```

### Count Available Tools
```bash
curl -s http://localhost:8000/api/tools | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total tools: {d[\"count\"]}')"
```

### List Tool Names Only
```bash
curl -s http://localhost:8000/api/tools | python3 -c "import sys,json; tools=json.load(sys.stdin)['tools']; print('\n'.join([t['name'] for t in tools]))"
```

---

## 3. Inventory Search Tests

### Search All Inventory
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me all vehicles in stock"}'
```

### Search SUVs Under $35,000 with AWD
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me all SUVs under 35000 with AWD"}'
```

### Find Cheapest Car
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is your cheapest car?"}'
```

### Find Most Expensive Car
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is your most expensive vehicle?"}'
```

### Search by Body Type - Sedans
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What sedans do you have available?"}'
```

### Search by Body Type - Trucks
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me all trucks"}'
```

### Search Electric Vehicles
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"List all electric vehicles in stock"}'
```

### Search by Make - Toyota
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What Toyota models do you have?"}'
```

### Search by Mileage
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me vehicles with less than 20000 miles"}'
```

### Search by Price Range
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show vehicles between 25000 and 35000 dollars"}'
```

---

## 4. Vehicle Details Tests

### Get Vehicle Details by Stock ID
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me about vehicle CS1001"}'
```

### Get Features for Specific Vehicle
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What features does CS1003 have?"}'
```

### Check Vehicle Availability
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Is CS1005 still available?"}'
```

### Get Mileage Info
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the mileage on CS1002?"}'
```

---

## 5. Vehicle Comparison Tests

### Compare Two Vehicles
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Compare CS1002 and CS1005"}'
```

### Compare Multiple Vehicles
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Compare CS1001, CS1003, and CS1004"}'
```

### Compare All SUVs
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Compare all your SUVs"}'
```

### Which is Better
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Which is better: CS1002 or CS1006?"}'
```

---

## 6. Financing Calculator Tests

### Estimate Payment for Specific Vehicle
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Estimate payment for CS1003 with 5000 down for 72 months"}'
```

### Calculate Monthly Payment
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Calculate monthly payment for a 30000 dollar car"}'
```

### Get Financing Options
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What financing options do you offer?"}'
```

### Payment with Custom APR
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What would CS1001 cost per month with 3000 down at 5.9 APR for 60 months?"}'
```

### Simple Payment Query
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How much would CS1001 cost per month?"}'
```

---

## 7. Trade-In Estimate Tests

### Basic Trade-In Estimate
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Estimate trade-in for my 2019 Honda Civic with 45000 miles"}'
```

### Trade-In with Condition
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Trade-in value for a 2018 Ford F-150 in good condition with 60000 miles"}'
```

### Trade-In Different Vehicle
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is my 2020 Toyota Camry worth with 35000 miles?"}'
```

### Trade-In Policy Question
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do you evaluate trade-ins?"}'
```

---

## 8. Scheduling & Appointments Tests

### Schedule Test Drive
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Schedule a test drive for CS1001 next Tuesday at 2pm. My name is John Smith and email is john@example.com"}'
```

### Test Drive Request (General)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I want to test drive the Tesla Model 3"}'
```

### Weekend Test Drive
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can I schedule a test drive for this weekend?"}'
```

---

## 9. General Information Tests

### Business Hours - Showroom
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are your business hours?"}'
```

### Business Hours - Service
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are your service department hours?"}'
```

### Return Policy (RAG Test)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is your return policy?"}'
```

### Warranty Information (RAG Test)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Do you offer warranties?"}'
```

### EV Charging Info (RAG Test)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What EV charging options do you have?"}'
```

### Location Query (RAG Test)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Where are you located?"}'
```

---

## 10. Warranty Tests

### Get Warranty Summary
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What warranty coverage does CS1003 have?"}'
```

### Warranty for Older Vehicle
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me about warranty for CS1005"}'
```

---

## 11. Complex Query Tests

### AWD SUV with Fuel Economy
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I need an AWD SUV under 40k with good fuel economy"}'
```

### Family Car with Warranty
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Help me find a family car with the best warranty"}'
```

### Trade-In Plus Finance
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I am trading in my car and want to finance the rest"}'
```

### Total Cost Query
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the total cost of CS1003 including tax and fees?"}'
```

---

## 12. Ollama Direct API Tests

### Test Embedding Generation
```bash
curl -s http://localhost:11434/api/embeddings \
  -d '{
    "model": "nomic-embed-text",
    "prompt": "What SUVs do you have?"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Embedding dimensions: {len(d[\"embedding\"])}')"
```

### Test LLM Chat Completion
```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 50
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"
```

### Check Model Info
```bash
curl -s http://localhost:11434/api/show \
  -d '{"name": "qwen2.5:3b"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Model: {d.get(\"modelfile\", \"N/A\")[:200]}...')"
```

---

## 13. Streaming Endpoint Tests

### Test Streaming Chat (verbose output)
```bash
curl -s -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"What is your cheapest car?"}' \
  --no-buffer | head -50
```

### Test Streaming with Full Pipeline
```bash
curl -s -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Compare CS1002 and CS1005"}' \
  --no-buffer | grep "event:" | head -20
```

---

## 14. Error Handling Tests

### Invalid Stock ID
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me about vehicle CS9999"}'
```

### Empty Message
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":""}'
```

### Invalid JSON
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

---

## 15. Performance & Load Tests

### Measure Response Time
```bash
time curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is your cheapest car?"}' > /dev/null
```

### Sequential Requests
```bash
for i in {1..5}; do
  echo "Request $i:"
  time curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"Business hours?"}' > /dev/null
  echo "---"
done
```

---

## 16. Data Verification

### Check Inventory JSON Directly
```bash
cat data/inventory.json | python3 -m json.tool | head -50
```

### Count Vehicles in Inventory
```bash
cat data/inventory.json | python3 -c "import sys,json; print(f'Total vehicles: {len(json.load(sys.stdin))}')"
```

### List All Stock IDs
```bash
cat data/inventory.json | python3 -c "import sys,json; vehicles=json.load(sys.stdin); print('\n'.join([v['stock_id'] for v in vehicles]))"
```

### Check Appointments
```bash
cat data/appointments.json 2>/dev/null | python3 -m json.tool || echo "No appointments yet"
```

### Check Leads
```bash
cat data/leads.json 2>/dev/null | python3 -m json.tool || echo "No leads yet"
```

---

## 17. ChromaDB Verification

### Check ChromaDB Directory Exists
```bash
ls -la chroma_db/
```

### Re-ingest Documents
```bash
rm -rf chroma_db && python ingest.py
```

---

## 18. Full System Test Script

Run all critical tests at once:

```bash
#!/bin/bash
echo "=== Car Sales Portal - System Test ==="

echo -e "\n[1] Health Check..."
curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d['ok'] else 'FAIL')"

echo -e "\n[2] MCP Tools Count..."
curl -s http://localhost:8000/api/tools | python3 -c "import sys,json; print(f'{json.load(sys.stdin)[\"count\"]} tools available')"

echo -e "\n[3] Inventory Search..."
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"Show me SUVs under 35000 with AWD"}' | python3 -c "import sys,json; r=json.load(sys.stdin)['reply']; print('PASS' if 'CR-V' in r or 'X3' in r else 'FAIL')"

echo -e "\n[4] Cheapest Car..."
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"What is your cheapest car?"}' | python3 -c "import sys,json; r=json.load(sys.stdin)['reply']; print('PASS' if 'Camry' in r or '27,995' in r else 'FAIL')"

echo -e "\n[5] Business Hours..."
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"What are your business hours?"}' | python3 -c "import sys,json; r=json.load(sys.stdin)['reply']; print('PASS' if 'Monday' in r or '9:00' in r else 'FAIL')"

echo -e "\n[6] Trade-In Estimate..."
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"Estimate trade-in for 2019 Honda Civic with 45000 miles"}' | python3 -c "import sys,json; r=json.load(sys.stdin)['reply']; print('PASS' if '$' in r else 'FAIL')"

echo -e "\n[7] Vehicle Details..."
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"Tell me about CS1001"}' | python3 -c "import sys,json; r=json.load(sys.stdin)['reply']; print('PASS' if 'Camry' in r or 'Toyota' in r else 'FAIL')"

echo -e "\n[8] Vehicle Comparison..."
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"Compare CS1002 and CS1005"}' | python3 -c "import sys,json; r=json.load(sys.stdin)['reply']; print('PASS' if 'CR-V' in r or 'BMW' in r else 'FAIL')"

echo -e "\n=== Test Complete ==="
```

---

## Quick Reference - Stock IDs

| Stock ID | Vehicle | Price | Type |
|----------|---------|-------|------|
| CS1001 | 2023 Toyota Camry SE | $27,995 | Sedan |
| CS1002 | 2022 Honda CR-V EX | $29,450 | SUV/AWD |
| CS1003 | 2024 Tesla Model 3 LR | $38,990 | Sedan/EV |
| CS1004 | 2021 Ford F-150 XLT | $34,995 | Truck/4WD |
| CS1005 | 2020 BMW X3 xDrive30i | $31,995 | SUV/AWD |
| CS1006 | 2024 Hyundai Ioniq 5 | $41,250 | SUV/EV |
| CS1007 | 2023 Chevy Tahoe LT | $52,990 | SUV/4WD |
| CS1008 | 2022 Lexus ES 350 | $35,990 | Sedan |

---

## Common Issues & Solutions

### Issue: "Connection refused"
```bash
# Check if app is running
lsof -i:8000

# Check if Ollama is running
curl -s http://localhost:11434/api/tags
```

### Issue: "Model not found"
```bash
# Pull required models
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

### Issue: "No RAG context found"
```bash
# Re-run ingestion
python ingest.py
```

### Issue: Port already in use
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: MCP tools not loading
```bash
# Check MCP server directly
python mcp_server.py &
# Should output: "Running MCP server..."
```

---

## Environment Variables

```bash
# Override defaults
export CHAT_MODEL="llama3:8b"
export EMBED_MODEL="nomic-embed-text"
export OPENAI_BASE_URL="http://localhost:11434/v1"
```

---

*Generated for AI Red Teaming - Car Sales Portal Chatbot*
