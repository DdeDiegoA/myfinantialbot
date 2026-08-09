## 1. Corpus (corpus-ingestion)

- [ ] 1.1 Collect 8-15 public DIAN Estatuto Tributario fragments into `docs/*.md`
- [ ] 1.2 Write `SOURCES.md` mapping each fragment to its official DIAN/Estatuto URL

## 2. Ingestion pipeline (corpus-ingestion)

- [ ] 2.1 Write `ingest.py`: chunk `docs/*.md`, tag each chunk with its source document id
- [ ] 2.2 Embed chunks with `sentence-transformers/all-MiniLM-L6-v2` (CPU)
- [ ] 2.3 Build and persist local FAISS index
- [ ] 2.4 Verify reproducibility: run ingestion twice, confirm identical retrieval results for a fixed query

## 3. Provider abstraction (provider-config)

- [ ] 3.1 Write `llm.py` PROVIDERS table (openrouter, nvidia, anthropic, openai, custom)
- [ ] 3.2 Read `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` from `.env`, no hardcoded values
- [ ] 3.3 Write `.env.example` with `LLM_PROVIDER=nvidia`, `LLM_MODEL=deepseek-ai/deepseek-v4-flash`, and commented OpenRouter fallback line
- [ ] 3.4 Confirm `.env` (real keys) is in `.gitignore`

## 4. Query + anti-hallucination (query-retrieval, anti-hallucination)

- [ ] 4.1 Write `rag.py`: embed query, FAISS top-k retrieval
- [ ] 4.2 Implement relevance-threshold gate: below threshold → return exact string `"I don't have that information."`, skip LLM call
- [ ] 4.3 Implement above-threshold path: build prompt constraining LLM to retrieved context only, require `[doc]` citation per claim
- [ ] 4.4 Format output as answer text + `sources: [doc, snippet]`
- [ ] 4.5 Manually verify one in-corpus and one out-of-corpus query end-to-end

## 5. Eval harness (eval-harness)

- [ ] 5.1 Write `tests/qa.json`: ~20 questions, half in-corpus (expected answer + source doc), half out-of-corpus (expected refusal)
- [ ] 5.2 Write `eval.py` grounding check: answer tokens ⊆ retrieved-context tokens
- [ ] 5.3 Write `eval.py` citation check: cited `[doc]` must be among retrieved sources
- [ ] 5.4 Aggregate to a single /100 score, print reproducibly

## 6. Public endpoint (public-endpoint)

- [ ] 6.1 Write `serve.py` FastAPI app exposing `/ask` and `/health`, importing `rag.py` directly (no reimplementation)
- [ ] 6.2 Write Dockerfile exposing `:8000`
- [ ] 6.3 `dokku apps:create myfinancialbot`, add `dokku` git remote, `git push dokku main`
- [ ] 6.4 Apply nginx redirect-loop fix (`sed` + `nginx -s reload`)
- [ ] 6.5 Add `hooks/post-deploy` script that re-applies the nginx fix automatically on every `ps:rebuild`
- [ ] 6.6 Configure Cloudflare Tunnel hostname `myfinancialbot.decodgo.com` → `http://127.0.0.1:80`, as a Tunnel-type DNS record (not wildcard A record)
- [ ] 6.7 `dokku domains:add`, `dokku config:set LLM_API_KEY=...` (never in repo)
- [ ] 6.8 Verify `curl -sI myfinancialbot.decodgo.com` returns 200 and matches local CLI output for the same question

## 7. Documentation

- [ ] 7.1 Write README: architecture, provider decision (Nvidia default + OpenRouter fallback), sources, deploy guide, 2-command quickstart

## 8. Demo + submission

- [ ] 8.1 Record 30-60s GIF: local `python rag.py "..."` + `curl` to live endpoint, same result
- [ ] 8.2 Send submission email to wfbsocialmediamx@epam.com
- [ ] 8.3 `openspec archive rag-dian-core`
- [ ] 8.4 `graphify update .` to refresh the project's knowledge graph
