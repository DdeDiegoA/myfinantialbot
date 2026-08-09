## Purpose

Guarantees the system never presents a fabricated answer as fact — when retrieved context is too weak to support an answer, it says so explicitly instead of guessing, which is the core evaluation criterion of this challenge.

## ADDED Requirements

### Requirement: Low-relevance retrieval short-circuits to an explicit refusal
When the best-matching retrieved context scores below a defined relevance threshold, the system SHALL return a fixed refusal message instead of calling the language model.

#### Scenario: Out-of-corpus question
- **WHEN** a user asks a question with no adequately relevant match in the index
- **THEN** the system responds with "I don't have that information." and does not invoke the LLM

### Requirement: Above-threshold answers are always accompanied by sources
Any answer that is generated (not refused) SHALL be accompanied by the list of source documents backing it.

#### Scenario: Successful grounded answer
- **WHEN** retrieved context scores above the relevance threshold
- **THEN** the returned answer includes both the generated text and a non-empty sources list

### Requirement: Refusal wording is exact and consistent
The refusal response SHALL use the exact same wording every time it is triggered, so automated evaluation can match it deterministically.

#### Scenario: Repeated out-of-corpus queries
- **WHEN** two different out-of-corpus questions both fall below the relevance threshold
- **THEN** both responses use the identical refusal message text
