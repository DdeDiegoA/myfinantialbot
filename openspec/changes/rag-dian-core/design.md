## Context

Greenfield project, no existing code. See proposal.md - Why. Two hard constraints from the plan: (1) zero GPU, CPU-only for anything running on the Mac Mini 2012, (2) LLM provider/model/key fully configurable by whoever clones — never hardcoded.

## Goals / Non-Goals

**Goals:**
- CLI (`rag.py`) and public HTTP service (`serve.py`) share the same retrieval + anti-hallucination logic, so behavior is identical local vs. live (see `public-endpoint` spec, Parity check).
- Provider abstraction stays small (~30 lines) — a dict of base URLs plus one OpenAI-compatible HTTP call, not a plugin framework.

**Non-Goals:**
- No vector DB service (Pinecone/Weaviate/etc.) — FAISS local index file is sufficient at 8-15 documents and keeps the "2 commands, no infra" promise.
- No fine-tuning or local LLM inference — all generation goes through a remote provider API.
- No auth/rate-limiting on the public endpoint — out of scope for a demo challenge; not a production service.

## Decisions

**FAISS + sentence-transformers for retrieval, not a hosted vector DB.**
Corpus is 8-15 small public documents. A hosted vector DB adds a network dependency and signup step for the evaluator, breaking "clone and run in 2 commands." FAISS index is a local file, `all-MiniLM-L6-v2` runs on CPU in milliseconds at this corpus size.

**Relevance threshold on FAISS score gates LLM calls (anti-hallucination spec).**
Alternative considered: always call the LLM and let the prompt instruct it to say "I don't know." Rejected — an LLM asked to judge its own uncertainty is exactly the failure mode this challenge penalizes. A deterministic score threshold checked in code before any LLM call is a hard guarantee, not a prompt-level suggestion.

**`llm.py` provider table is a plain dict, not a class hierarchy.**
Every supported provider (OpenRouter, Nvidia, Anthropic, OpenAI, custom) is OpenAI-chat-completions-compatible or close enough to normalize with one thin wrapper. A dict of `{provider: {base_url}}` plus one function that reads `LLM_PROVIDER`/`LLM_MODEL`/`LLM_API_KEY` from `.env` is enough — no need for a provider interface/factory for 4-5 near-identical HTTP shapes.

**Default demo provider: Nvidia (`deepseek-ai/deepseek-v4-flash`), not OpenRouter.**
User-confirmed choice despite a known bug (Nvidia's direct `/v1/chat/completions` endpoint returned HTTP 500 in prior testing). Rationale: Nvidia's cost/latency (~10.3s, P4) was already benchmarked and preferred. Mitigation: `.env.example` ships OpenRouter (`deepseek/deepseek-chat`) as a documented one-line fallback — swapping `LLM_PROVIDER` requires no code change, so the risk is contained to a config edit, not a rewrite.

**`serve.py` (Bonus B host) does retrieval only, never generation.**
The Mac Mini 2012 has no GPU and is not the reliability-critical path for challenge scoring (base 200 > Bonus A 30 > Bonus B 30). Keeping it retrieval-only plus one outbound HTTPS call to the LLM provider means its resource profile is trivial — a bug there can't corrupt answer quality, only availability.

**Deploy pattern reused verbatim from `linko` (same Mac Mini VPS).**
Alternative considered: design deploy fresh. Rejected — `linko`'s Dokku + Cloudflare Tunnel setup on this exact machine already has documented, resolved incidents (nginx redirect-loop, wildcard DNS bypass, storage mount loss). Reusing the pattern, including the `post-deploy` hook that re-applies the nginx fix automatically, converts known failure modes into non-issues instead of rediscovering them.

## Risks / Trade-offs

- [Nvidia endpoint HTTP 500 bug resurfaces during the live demo] → `.env` on the Mac Mini can be repointed to `LLM_PROVIDER=openrouter` in one `dokku config:set`, no redeploy of code needed.
- [FAISS index rebuilt incorrectly loses chunk→document traceability] → `corpus-ingestion` spec requires every chunk carry its source document id; `eval.py` citation check (eval-harness spec) catches regressions automatically.
- [Mac Mini `ps:rebuild` regenerates nginx.conf and drops the redirect fix] → `post-deploy` hook re-applies the sed automatically on every rebuild (see linko precedent), removing the manual-repeat risk called out in the original brief.
- [Public endpoint and local CLI drift apart in behavior over time] → both share the same `rag.py` retrieval/anti-hallucination module; `serve.py` imports it rather than reimplementing query logic.

## Migration Plan
N/A — greenfield project, no existing system to migrate from or roll back to.
