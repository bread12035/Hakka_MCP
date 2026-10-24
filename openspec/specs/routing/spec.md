# routing Specification

## Purpose
The `route` MCP tool that turns a client and task type into the skill texts to follow.

## Requirements

### Requirement: Route request
The system SHALL expose a `route` tool that takes `client`, `task_type`, `session_id` and `rationale`, lists the valid clients and task types as enums in its schema, and returns the config id, config version and the full text of every skill in the config.

#### Scenario: Route a known task
- **GIVEN** an authenticated user and a config for `code` and `code-feature`
- **WHEN** the user's client calls `route` with `code` and `code-feature`
- **THEN** the result holds that config's id, version and the full text of each of its skills

#### Scenario: Unknown client rejected
- **GIVEN** an authenticated user
- **WHEN** the client calls `route` with a client that is neither `code` nor `cowork`
- **THEN** the call fails with an error that lists the valid clients and no usage event is written

### Requirement: Fallback config
The system SHALL answer a task type with no config for that client with the client's `default` config, and SHALL mark the result and the usage event as a fallback.

#### Scenario: Unconfigured task type falls back
- **GIVEN** no config for client `cowork` and task type `code-bugfix`
- **WHEN** the client calls `route` with `cowork` and `code-bugfix`
- **THEN** the result holds the Cowork `default` config and says it is a fallback

### Requirement: Skill-state template
The system SHALL include the task type's default `status.json` template when the config contains skill-state, and SHALL use the caller's template instead when one is passed.

#### Scenario: Default status template returned
- **GIVEN** a config with skill-state and a default template for its task type
- **WHEN** the client calls `route` without a template
- **THEN** the result holds the default `status.json` template

#### Scenario: Caller template overrides default
- **GIVEN** a config with skill-state
- **WHEN** the client calls `route` with its own `status.json` template
- **THEN** the result holds the caller's template and not the default
