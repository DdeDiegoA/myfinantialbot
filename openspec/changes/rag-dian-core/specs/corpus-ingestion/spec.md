## Purpose

Turns the public DIAN tax-code source documents into a searchable local index so queries can retrieve grounded context without any external index service.

## ADDED Requirements

### Requirement: Corpus builds into a local vector index
The system SHALL process every document in the public corpus into a local vector index, running fully offline with no external API calls during ingestion.

#### Scenario: Fresh ingestion run
- **WHEN** the ingestion process runs against the corpus directory
- **THEN** a local vector index is produced covering every document in the corpus, with no network requests made

### Requirement: Each indexed chunk retains its source document
Every chunk in the index SHALL be traceable back to the specific source document it came from, so retrieval can cite it later.

#### Scenario: Chunk lookup after ingestion
- **WHEN** a chunk is retrieved from the index
- **THEN** the chunk's originating document identifier is available alongside it

### Requirement: Ingestion is reproducible
Running ingestion again on an unchanged corpus SHALL produce an index with equivalent retrieval behavior, so evaluators get consistent results across runs.

#### Scenario: Repeat ingestion
- **WHEN** ingestion runs twice on the same unmodified corpus
- **THEN** querying either resulting index for the same question returns the same source documents
