## Purpose

Provides reproducible, numeric evidence that the system is grounded and citing correctly, satisfying the challenge's Bonus A requirement for automated evaluation rather than manual spot-checks.

## ADDED Requirements

### Requirement: QA set covers in-corpus and out-of-corpus questions
The evaluation question set SHALL contain both questions answerable from the corpus and questions deliberately outside it, in roughly equal proportion.

#### Scenario: QA set composition
- **WHEN** the QA set is loaded
- **THEN** it contains at least one expected-answer case per indexed topic area and at least an equal number of expected-refusal cases

### Requirement: Evaluation scores grounding automatically
For each in-corpus QA case, the evaluator SHALL check whether the generated answer's content is supported by the retrieved context, without manual review.

#### Scenario: Grounded answer scored
- **WHEN** the evaluator runs against an in-corpus question
- **THEN** it reports a pass/fail grounding result for that question based on the retrieved context

### Requirement: Evaluation scores citation presence
For each in-corpus QA case, the evaluator SHALL check that the returned sources reference documents that were actually retrieved.

#### Scenario: Citation check
- **WHEN** the evaluator inspects a generated answer's sources list
- **THEN** it flags any cited document that was not among the retrieved context

### Requirement: Evaluation produces a single reproducible score
Running the evaluator SHALL produce one overall numeric score summarizing grounding and citation results across the full QA set.

#### Scenario: Full evaluation run
- **WHEN** the evaluator runs against the complete QA set
- **THEN** it outputs one aggregate score, and re-running it on an unchanged system produces the same score
