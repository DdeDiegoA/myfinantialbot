# MyFinancialBot — DIAN RAG Assistant

Grounded RAG chatbot for Colombian DIAN tax (renta) declaration rules. Answers cite sources or refuses out-of-corpus questions — **no hallucination**, enforced in code, not prompts.

**Live:** `https://myfinancialbot.decodgo.com` (deployed on Mac Mini via Dokku + Cloudflare Tunnel)

---

## 1. Quick Start (Local)

### 1.1 Clone & Setup (2 min)

```bash
git clone https://github.com/DdeDiegoA/myfinantialbot.git
cd myfinantialbot

# Create venv + install all deps
make install

# Copy config template and fill in LLM credentials
cp .env.example .env
# Edit .env: set LLM_PROVIDER, LLM_MODEL, LLM_API_KEY
```

### 1.2 Build Index (1 min)

```bash
make ingest
# Output: "Indexed 39 chunks from 15 files"
```

### 1.3 Run CLI or API

**CLI (offline, free):**
```bash
.venv/bin/python rag.py "¿Quiénes deben declarar renta en 2025?"
# Output: Answer + APA-style sources block
```

**API (local endpoint):**
```bash
make up
# Starts uvicorn on http://localhost:8000

# In another terminal:
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuál es el valor de la UVT 2025?"}'
```

---

## 2. Setup Details

### 2.1 Requirements

- **Python:** 3.11+
- **OS:** macOS, Linux, or WSL (tested on Mac)
- **Disk:** ~500MB (corpus + index + Python env)
- **Network:** Only for LLM calls (embedding is CPU-only)

### 2.2 LLM Provider Config

Edit `.env` (copy from `.env.example`):

```ini
# Option 1: Nvidia (default, streaming, no 500 errors)
LLM_PROVIDER=nvidia
LLM_MODEL=nvidia/nemotron-3-nano-30b-a3b
LLM_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxx

# Option 2: OpenRouter (fallback if Nvidia has issues)
# LLM_PROVIDER=openrouter
# LLM_MODEL=deepseek/deepseek-chat
# LLM_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxx

# Option 3: Anthropic
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-5-sonnet-20241022
# LLM_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxx

# Option 4: OpenAI
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
# LLM_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxx
```

**Getting API keys:**
- Nvidia: https://build.nvidia.com/
- OpenRouter: https://openrouter.ai/
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/

---

## 3. Using the Code

### 3.1 CLI Only (No API)

```bash
# One-off question
.venv/bin/python rag.py "¿Cuál es el tope de patrimonio bruto?"

# With custom threshold (default 0.55)
RAG_THRESHOLD=0.5 .venv/bin/python rag.py "¿Qué es la UVT?"
```

**Output format:**
```
El tope de patrimonio bruto que obliga a declarar renta para el año gravable 2025 es de 4 500 UVT...

Fuentes:
- DIAN. (s.f.). Tope patrimonio bruto 2025. https://micrositios.dian.gov.co/...
- DIAN. (s.f.). Uvt que es y para que sirve. https://www.dian.gov.co/...
```

### 3.2 FastAPI Endpoint

**Start server:**
```bash
make up
# Or: .venv/bin/uvicorn serve:app --host 0.0.0.0 --port 8000
```

**Health check:**
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

**Ask question (POST):**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es el valor de la UVT para el año 2025?"
  }'
```

**Response:**
```json
{
  "answer": "El valor de la UVT para el año 2025 es $49.799 pesos colombianos.\n\nFuentes:\n- DIAN. (s.f.). Uvt 2025 valor. https://...",
  "sources": [
    {
      "source_url": "https://www.dian.gov.co/normatividad/...",
      "snippet": "# Valor de la UVT para el año 2025\n\n..."
    }
  ]
}
```

### 3.3 Python API (Programmatic)

```python
from rag import answer_question

result = answer_question("¿Quién está obligado a declarar renta?")
print(result["answer"])       # Full answer with sources
print(result["sources"])      # List of [{source_url, snippet}, ...]

# Refusal case (out of corpus)
result = answer_question("¿Cuál es la capital de Francia?")
print(result["answer"])  # "I don't have that information."
print(result["sources"]) # []
```

---

## 4. Deploying to Production

### 4.1 Mac Mini VPS (Dokku)

**Prerequisites:**
- Mac Mini with Dokku installed
- Cloudflare Tunnel configured
- LLM API key

**Deploy:**

```bash
# 1. On your local machine, add dokku remote
git remote add dokku dokku@decodgo.com:myfinancialbot
git push dokku main

# 2. Or, on the Mac Mini directly:
ssh macmini
dokku apps:create myfinancialbot
cd /path/to/repo && git push /home/dokku/myfinancialbot main

# 3. Set environment variables
dokku config:set myfinancialbot \
  LLM_PROVIDER=nvidia \
  LLM_MODEL="nvidia/nemotron-3-nano-30b-a3b" \
  LLM_API_KEY="nvapi-xxxxxxx"

# 4. Rebuild
dokku ps:rebuild myfinancialbot

# 5. Add domain
dokku domains:add myfinancialbot myfinancialbot.decodgo.com
```

**Access:**
```bash
# Locally on Mac Mini
curl http://127.0.0.1:8000/health

# Via Cloudflare Tunnel (public)
curl https://myfinancialbot.decodgo.com/health
```

**See also:** `/Users/diegoarenas/vault/Mac-Mini-VPS-deploy-guide.md` for detailed Dokku + Nginx + CF Tunnel setup.

### 4.2 Docker

```bash
# Build image
docker build -t myfinancialbot:latest .

# Run with env vars
docker run -d \
  -p 8000:5000 \
  -e LLM_PROVIDER=nvidia \
  -e LLM_MODEL="nvidia/nemotron-3-nano-30b-a3b" \
  -e LLM_API_KEY="nvapi-xxxxxxx" \
  myfinancialbot:latest

# Test
curl http://localhost:8000/health
```

---

## 5. Architecture

### Data Flow

```
                     ingest.py (offline, run once)
  docs/dian/*.md  ──chunk──▶  MiniLM embed (CPU)  ──▶  index.faiss + chunks.json

                     rag.py / serve.py (per query)
  question ──▶ MiniLM embed ──▶ FAISS top-k search ──▶ score
                                                          │
                                        ┌─────────────────┴──────────────────┐
                                        │                                    │
                                score < 0.55                        score >= 0.55
                                        │                                    │
                                        ▼                                    ▼
                         "I don't have that information."   LLM: answer from context only
                              (zero cost)                            │
                                                                     ▼
                                                     Nvidia/OpenRouter/Anthropic/OpenAI
                                                                     │
                                                                     ▼
                                                  {answer, sources: [source_file...]}
```

### Files

```
docs/dian/                  Corpus: 16 DIAN markdown files (16 chunks → 39 with heading context)
docs/dian/SOURCES.md        Metadata: source URL per document

ingest.py                   Build index: chunk + embed + FAISS (one-time, ~1min)
rag.py                      RAG core: retrieve → threshold gate → LLM call
llm.py                      LLM abstraction: provider-agnostic client (streaming for Nvidia)
serve.py                    FastAPI wrapper: /health, /ask endpoints
eval.py                     Test harness: 25 Q&A cases, outputs /100 score

.env.example                Config template (LLM provider, model, API key)
requirements.txt            Python deps: sentence-transformers, faiss, fastapi, openai, requests, ...
Makefile                    Automation: make install, make ingest, make up

tests/qa.json               Benchmark QA pairs (25 test cases)
index.faiss                 FAISS vector index (gitignored, built by ingest.py)
chunks.json                 Chunk metadata + text (gitignored, built by ingest.py)
```

---

## 6. Anti-Hallucination Gate

Two-layer system:

1. **Similarity threshold** (RELEVANCE_THRESHOLD = 0.55): If best match scores below 0.55, return "I don't have that information." immediately (zero LLM cost).

2. **System prompt** (in `rag.py`): LLM instructed to refuse partial coverage; optional sentinel refusal `NO_INFO` token converted to standard refusal text.

**Effect:** Out-of-corpus questions never reach the LLM; in-corpus but under-covered questions are refused by the LLM itself.

---

## 7. Corpus & Sources

### Topics Covered

- **UVT (Unidad de Valor Tributario):** Official 2025 value ($49,799 COP), how it's used, historical context
- **Filing obligations (6 conditions):** Gross income, patrimonio bruto, credit card spending, bank deposits, total purchases, VAT status
- **Thresholds & exemptions:** Per-condition UVT cutoffs (all ~1,400 UVT except patrimonio bruto at 4,500)
- **Renta filing calendar:** Deadline schedule by last 2 cédula digits (August–October 2026 for AG 2025)
- **Wealth tax (impuesto al patrimonio):** 2026 changes per Decreto Legislativo 1474

### Full Source List

See `docs/dian/SOURCES.md`:
- Resolutions from DIAN (official gazette URLs)
- Microsite: https://micrositios.dian.gov.co/renta-personas-naturales-ag-2025/
- Estatuto Tributario (Art. 261): https://estatuto.co/261

### Adding New Docs

1. Save `.md` file to `docs/dian/`
2. Add source URL to `docs/dian/SOURCES.md`
3. Run `make ingest` to rebuild index
4. Test with `rag.py`

---

## 8. Testing & Evaluation

### Run Eval Harness

```bash
.venv/bin/python eval.py
# Output: "Accuracy: 97.8/100"
```

Tests 25 QA pairs (16 in-corpus, 9 out-of-corpus) against grounding, citation, and refusal criteria.

### Manual QA

```bash
.venv/bin/python rag.py "¿Cuál es el valor de la UVT para el año 2025?"
# Expected: $49,799 + DIAN source

.venv/bin/python rag.py "¿Quién ganó el Oscar este año?"
# Expected: "I don't have that information."
```

---

## 9. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `KeyError: 'LLM_PROVIDER'` | Missing `.env` | `cp .env.example .env` + fill in keys |
| `ModuleNotFoundError: sentence_transformers` | Venv not active | `.venv/bin/python rag.py "..."` or activate venv |
| Nvidia timeout (60s) | Raw POST without streaming | Already fixed in llm.py (uses OpenAI client + stream=True) |
| API returns 500 | LLM provider unreachable | Check API key + network; switch to OpenRouter in `.env` |
| "Welcome to nginx!" (dokku) | Nginx config issue | Apply nginx fix: `sed -i 's|return 301.*|proxy_pass http://...|'` |
| CF Tunnel timeout | Tunnel not running | `sudo systemctl restart cloudflared` on Mac Mini |

---

## 10. Design Decisions

- **Streaming LLM calls:** Nvidia endpoint hangs without streaming; using OpenAI SDK with `stream=True`
- **APA-style sources:** No inline citations; consolidated `Fuentes:` block at end of answer
- **Local embedding:** No hosted vector DB; FAISS on CPU is fast enough for ~40 chunks
- **Double anti-hallucination:** Threshold gate + system prompt = no false positives in 25 test cases
- **Config-driven providers:** Single `llm.py` handles Nvidia/OpenRouter/Anthropic/OpenAI/custom

---

## 11. Project Info

- **Challenge:** Reto 3 EPAM "IA con Criterio" (Bonus B: public endpoint)
- **Eval Metric:** No hallucination (enforced in code, not prompts)
- **Score:** 97.8/100 on 23-case validation suite; 94.0% on 25-case suite post-2026 corpus update
- **License:** Internal (EPAM Reto)
- **Contact:** diegoarenas111@gmail.com

---

## Quick Reference

```bash
# Local: install + run
make install && make up

# CLI only
.venv/bin/python rag.py "YOUR_QUESTION_HERE"

# API only
make up                # starts on :8000

# Re-index corpus
make ingest

# Test
.venv/bin/python eval.py

# Deploy to dokku
git push dokku main

# Access deployed API
curl https://myfinancialbot.decodgo.com/ask \
  -d '{"question":"..."}'
```
