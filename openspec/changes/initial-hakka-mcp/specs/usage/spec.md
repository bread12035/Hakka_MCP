## Purpose
Usage events and the estimated savings derived from them.

## ADDED Requirements

### Requirement: Record usage event
The system SHALL write one usage event per successful `route` call with the user id, client, task type, config id, session id, fallback flag, rationale and timestamp.

#### Scenario: Successful route writes an event
- **GIVEN** an authenticated user
- **WHEN** the user's client calls `route` successfully
- **THEN** the usage store holds one new event for that user, client, task type and config

### Requirement: Session deduplication
The system SHALL count the estimated saving at most once per user, session id and config, while still recording every call.

#### Scenario: Repeated route in one session counted once
- **GIVEN** a user who called `route` for one config in session `s1`
- **WHEN** the same user calls `route` again for the same config in session `s1`
- **THEN** the statistics count one saving for that session and two calls

#### Scenario: Different config in the same session counted separately
- **GIVEN** a user who called `route` for config A in session `s1`
- **WHEN** the same user calls `route` for config B in session `s1`
- **THEN** the statistics count one saving for config A and one for config B

### Requirement: Estimate snapshot
The system SHALL store the config version, expected saving percentage, expected token saving and their provenance on each usage event as they were at call time.

#### Scenario: Recalibration keeps history
- **GIVEN** a usage event recorded while a config estimated 1000 tokens saved
- **WHEN** the config is changed to estimate 500 tokens and the server restarts
- **THEN** the statistics still count 1000 tokens for the old event

#### Scenario: Recompute with current estimates
- **GIVEN** the same old event and the new estimate of 500 tokens
- **WHEN** the admin asks for statistics recomputed with current estimates
- **THEN** the statistics count 500 tokens for the old event

### Requirement: Privacy of rationale
The system MUST NOT store the user's prompt, and SHALL truncate the rationale to 200 characters before storing it.

#### Scenario: Long rationale truncated
- **GIVEN** an authenticated user
- **WHEN** the client calls `route` with a rationale of 500 characters
- **THEN** the stored event holds the first 200 characters of the rationale

### Requirement: Usage statistics
The system SHALL report distinct users, calls, counted sessions, estimated tokens saved and estimated weighted USD saved, in total and grouped by client, task type or config, separated by provenance, through a CLI report and an admin-only `get_usage_stats` tool.

#### Scenario: Statistics grouped by task type
- **GIVEN** events from two users across two task types
- **WHEN** the admin asks for statistics grouped by task type
- **THEN** each task type row shows its distinct users, calls and estimated savings

#### Scenario: Savings split by provenance
- **GIVEN** events for one config whose estimate is `measured` and one whose estimate is `vendor-claim`
- **WHEN** the admin asks for total statistics
- **THEN** the measured and vendor-claim savings are reported separately

#### Scenario: CLI report as CSV
- **GIVEN** recorded events
- **WHEN** the maintainer runs the report command with CSV output
- **THEN** it prints a CSV with one row per group and a header row

#### Scenario: Empty usage store
- **GIVEN** no events
- **WHEN** the admin asks for statistics
- **THEN** the report shows zero users, zero calls and zero savings
