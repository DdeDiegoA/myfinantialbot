## Purpose

Lets whoever clones the repo choose their own LLM provider, model, and API key through configuration alone, so the project runs against the evaluator's own account with no code changes and no hardcoded credentials.

## ADDED Requirements

### Requirement: Provider, model, and key are set via configuration only
The system SHALL read the LLM provider, model, and API key exclusively from environment configuration, never from source code.

#### Scenario: Fresh clone with no code changes
- **WHEN** a user clones the repo and sets provider/model/key in their local environment file
- **THEN** the system uses those values without requiring any source edit

### Requirement: No credential ships in the repository
The repository SHALL NOT contain any real API key or credential; only a documented example configuration with placeholder values.

#### Scenario: Repo audit
- **WHEN** the repository contents are inspected for secrets
- **THEN** no functioning API key is found anywhere in tracked files

### Requirement: Multiple providers are supported through the same interface
The system SHALL support switching between at least the following providers by configuration alone: OpenRouter, Nvidia, Anthropic, OpenAI, and a custom OpenAI-compatible endpoint.

#### Scenario: Switching provider
- **WHEN** the configured provider value changes from one supported provider to another
- **THEN** subsequent queries route to the newly configured provider without code changes
