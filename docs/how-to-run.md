# How to Run

## Prerequisites

- Python 3.10+
- Docker + Docker Compose

---

## 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Start Kafka

```bash
docker compose up -d
```

Wait ~15 seconds for Kafka to be ready. You can verify with:

```bash
docker compose ps
# STATUS should be "healthy"
```

---

## 3. Start the agents

Open **three separate terminals** (all with the venv activated):

**Terminal 1 — Summarizer (A2A server on port 8001)**
```bash
source .venv/bin/activate
python agents/summarizer/main.py
```

**Terminal 2 — Classifier (A2A server on port 8002)**
```bash
source .venv/bin/activate
python agents/classifier/main.py
```

**Terminal 3 — Orchestrator (Kafka consumer)**
```bash
source .venv/bin/activate
python agents/orchestrator/main.py
# Output: [orchestrator] Listening on articles.raw ...
```

---

## 4. Trigger the pipeline

In a fourth terminal, publish a test article:

```bash
source .venv/bin/activate
python trigger.py "https://example.com/ai-news" \
  "OpenAI released a new model today. The model uses advanced machine learning algorithms. Researchers say the data shows improvement in reasoning tasks."
```

You should see in the Orchestrator terminal:
```
[orchestrator] Processing: https://example.com/ai-news
[orchestrator] Published — tags=['tech'], words=19
```

---

## 5. Observe the output

### Read the enriched articles topic
```bash
docker exec -it $(docker ps -q --filter "name=kafka") \
  kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic articles.enriched \
  --from-beginning
```

Expected output:
```json
{"url": "https://example.com/ai-news", "summary": "OpenAI released a new model today. The model uses advanced machine learning algorithms.", "word_count": 19, "tags": ["tech"]}
```

### Read the agent audit events
```bash
docker exec -it $(docker ps -q --filter "name=kafka") \
  kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic agent.events \
  --from-beginning
```

### Inspect Agent Cards (A2A discovery)
```bash
curl http://localhost:8001/.well-known/agent.json | python3 -m json.tool
curl http://localhost:8002/.well-known/agent.json | python3 -m json.tool
```

### Call an agent directly via A2A (bypassing Kafka)
```bash
curl -s -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-001",
    "input": { "text": "NASA launched a new satellite. Scientists are monitoring climate data from orbit." }
  }' | python3 -m json.tool
```

---

## 6. Tear down

```bash
docker compose down
```

---

## Environment Variables

All agents support configuration via environment variables:

| Variable | Default | Used by |
|---|---|---|
| `KAFKA_BOOTSTRAP` | `localhost:9092` | All agents, trigger.py |
| `SUMMARIZER_URL` | `http://localhost:8001` | Orchestrator |
| `CLASSIFIER_URL` | `http://localhost:8002` | Orchestrator |

Example with custom Kafka:
```bash
KAFKA_BOOTSTRAP=my-broker:9092 python agents/orchestrator/main.py
```

---

## Troubleshooting

**Orchestrator can't connect to Kafka**
- Ensure Kafka healthcheck passes: `docker compose ps`
- Verify port 9092 is free: `lsof -i :9092`

**A2A calls fail (Connection refused)**
- Make sure summarizer and classifier are running before starting the orchestrator
- Check the ports are not in use: `lsof -i :8001` / `lsof -i :8002`

**No messages in `articles.enriched`**
- Check the Orchestrator terminal for errors
- Try calling the agents directly with `curl` to verify they respond correctly
