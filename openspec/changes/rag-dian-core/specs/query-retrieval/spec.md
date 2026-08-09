## Purpose

Answers a user's tax question by retrieving the most relevant indexed context and composing a cited response, so answers stay traceable to the underlying DIAN sources instead of the model's unsupported knowledge.

## ADDED Requirements

### Requirement: Query retrieves top-k relevant context
Given a natural-language question, the system SHALL retrieve the top-k most relevant chunks from the local index before composing any answer.

#### Scenario: In-corpus question
- **WHEN** a user asks a question covered by the corpus
- **THEN** the system retrieves relevant chunks and their source documents before generating a response

### Requirement: Every generated answer cites its sources
Any answer generated from retrieved context SHALL include the source document(s) it drew from, presented alongside the answer text.

#### Scenario: Answer with citation
- **WHEN** the system generates an answer using retrieved context
- **THEN** the response includes a `sources` list naming each source document used

### Requirement: Answer generation is instructed to use only retrieved context
The prompt sent to the language model SHALL constrain it to answer using only the retrieved context and to flag uncertainty rather than invent facts.

#### Scenario: Ambiguous or partial context
- **WHEN** retrieved context only partially covers the question
- **THEN** the generated answer reflects that partial coverage instead of filling gaps with unsupported claims
