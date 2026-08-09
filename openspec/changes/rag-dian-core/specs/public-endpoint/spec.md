## Purpose

Makes the RAG system reachable over the public internet at a stable URL, satisfying the challenge's Bonus B requirement for a live, evaluator-accessible demo without requiring GPU infrastructure.

## ADDED Requirements

### Requirement: Public endpoint answers the same questions as the local CLI
A question sent to the public HTTP endpoint SHALL produce an answer equivalent in content and citation behavior to the same question run through the local command-line tool.

#### Scenario: Parity check
- **WHEN** the same question is sent to the local CLI and to the public endpoint
- **THEN** both return an answer with the same source documents and the same refusal behavior for out-of-corpus questions

### Requirement: Endpoint exposes a health check
The system SHALL expose a health-check route that reports whether the service is reachable and ready to answer questions.

#### Scenario: Health probe
- **WHEN** the health-check route is requested
- **THEN** it responds successfully whenever the service is able to serve queries

### Requirement: Public host performs no local text generation
The publicly hosted service SHALL perform retrieval and outbound calls to the configured LLM provider only — it SHALL NOT run any local text-generation model.

#### Scenario: Resource profile check
- **WHEN** the public host serves a query
- **THEN** no local generation model is invoked; the answer text originates from the configured external provider
