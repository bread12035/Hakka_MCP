## Purpose
The techniques, skills and config sets the router serves, and the rules that keep them valid.

## ADDED Requirements

### Requirement: Technique applicability
The system SHALL allow a technique in a config only for the clients its applicability matrix permits: pass-by-reference, caveman, skill-state and model-routing for both clients; ponytail-rules-only and code-graph for Claude Code only.

#### Scenario: Code-only technique in a Cowork config
- **GIVEN** a Cowork config that lists code-graph
- **WHEN** the server loads the configs
- **THEN** loading fails with an error that names the config and the technique

#### Scenario: Shared technique in both clients
- **GIVEN** a Claude Code config and a Cowork config that both list caveman
- **WHEN** the server loads the configs
- **THEN** both configs load

### Requirement: Config sets
The system SHALL resolve each pair of client and task type to exactly one config that names its skill set, a version, an expected saving percentage and an expected token saving per session.

#### Scenario: Config resolves for a known pair
- **GIVEN** a config for client `code` and task type `code-bugfix`
- **WHEN** the catalog is asked for that pair
- **THEN** it returns that config with its skills, version, percentage and token estimate

#### Scenario: Duplicate config for one pair
- **GIVEN** two configs for client `code` and task type `code-bugfix`
- **WHEN** the server loads the configs
- **THEN** loading fails with an error that names both files

### Requirement: Config validation
The system MUST refuse to start when any config or skill file is invalid, and SHALL report every problem found, not only the first.

#### Scenario: Config names a missing skill
- **GIVEN** a config that lists a skill id with no skill file
- **WHEN** the server starts
- **THEN** it exits with an error naming the config and the missing skill id

#### Scenario: Several invalid configs reported together
- **GIVEN** two configs that are each invalid
- **WHEN** the server starts
- **THEN** the error lists both problems

#### Scenario: Skill over the size limit
- **GIVEN** a skill whose text is larger than 4 KB
- **WHEN** the server starts
- **THEN** it exits with an error naming the skill and its size

### Requirement: Number provenance
The system MUST require every expected-saving number to carry a provenance of `measured`, `vendor-claim` or `estimate`, and SHALL accept an optional source link.

#### Scenario: Saving number without provenance
- **GIVEN** a config whose expected saving has no provenance
- **WHEN** the server loads the configs
- **THEN** loading fails with an error naming the config

### Requirement: Initial task types
The system SHALL ship configs for `cowork-poc`, `cowork-daily-data` and `cowork-doc` under Cowork, `code-feature`, `code-bugfix` and `code-explore` under Claude Code, and a `default` config for each client.

#### Scenario: Shipped catalog loads
- **GIVEN** the configs and skills shipped in the repo and draft serving enabled
- **WHEN** the server starts
- **THEN** it starts and lists the six task types plus one default per client

### Requirement: Skill approval status
The system MUST refuse to load a config that references a skill marked `draft` unless draft serving is enabled at startup, and SHALL mark each draft skill as draft in the `route` result.

#### Scenario: Config references a draft skill
- **GIVEN** a config that lists a skill marked `draft`
- **WHEN** the server loads the configs
- **THEN** loading fails with an error naming the config and the draft skill

#### Scenario: Draft skill served when enabled
- **GIVEN** a config that lists a skill marked `draft` and draft serving enabled
- **WHEN** a client calls `route` for that config
- **THEN** the result holds the skill text and marks it as draft
