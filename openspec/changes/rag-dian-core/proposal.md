## Why

Reto 3 EPAM ("IA con Criterio") pide un RAG punta-a-punta sobre declaración de renta DIAN-Colombia, clonable en 2 comandos, con cero respuestas inventadas y fuentes citadas. Sin specs versionadas, el diseño del anti-hallucination contract y de la abstracción de provider quedarían implícitos en el código — riesgo alto en un reto donde "criterio" (no alucinar) es el criterio de evaluación central. Este proposal fija el contrato ANTES de codear.

## What Changes

- Nuevo pipeline de ingesta: chunking de docs públicos DIAN → embeddings locales (CPU) → índice FAISS.
- Nuevo flujo de query: embed pregunta → top-k FAISS → umbral de score → respuesta citada o rechazo explícito.
- Nueva abstracción de LLM provider (`llm.py`): tabla de providers (openrouter/nvidia/anthropic/openai/custom), configurada 100% por `.env`, sin keys hardcodeadas.
- Nuevo eval harness (Bonus A): QA set con casos dentro/fuera del corpus, scoring de grounding y citación.
- Nuevo endpoint público (Bonus B): FastAPI `/ask` `/health` servido en Mac Mini VPS vía Dokku + Cloudflare Tunnel, reusando el patrón ya validado en el proyecto `linko`.

## Capabilities

### New Capabilities
- `corpus-ingestion`: chunking de fragmentos DIAN, embedding con `sentence-transformers/all-MiniLM-L6-v2`, construcción de índice FAISS local, offline.
- `query-retrieval`: dado un query, recupera contexto top-k y arma prompt con instrucción de citar `[doc]` por cada claim.
- `provider-config`: selección de LLM provider/modelo/API key vía `.env`, sin hardcode, con Nvidia como default documentado (riesgo bug 500) y OpenRouter como fallback listo.
- `anti-hallucination`: contrato de umbral de score — bajo umbral responde `"I don't have that information."` sin llamar al LLM; sobre umbral, respuesta debe incluir `sources:`.
- `eval-harness`: `tests/qa.json` (~20 preguntas mitad dentro/mitad fuera del corpus) + `eval.py` con métricas de grounding (tokens de respuesta ⊆ contexto) y presencia de citación, output score /100.
- `public-endpoint`: servicio FastAPI de solo retrieval+LLM-passthrough (cero GPU) desplegado en Mac Mini VPS, expuesto en `myfinancialbot.decodgo.com`.

### Modified Capabilities
(ninguna — proyecto nuevo, sin specs previas)

## Impact

- Código nuevo: `ingest.py`, `rag.py`, `llm.py`, `serve.py`, `eval.py`, `.env.example`, `docs/*.md`, `tests/qa.json`.
- Infra: Mac Mini VPS (Dokku app `myfinancialbot`, nginx fix, CF Tunnel hostname, DNS tipo Tunnel).
- Dependencias externas: proveedor LLM elegido por quien clona (ninguna key en el repo).
- Sin impacto en sistemas existentes — proyecto greenfield.
