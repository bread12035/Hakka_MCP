## Purpose
Who may call the server and who may see the statistics.

## ADDED Requirements

### Requirement: API key authentication
The system MUST reject every MCP request that carries no API key or an unknown or revoked key, and SHALL derive the user id from the key.

#### Scenario: Missing API key rejected
- **GIVEN** a running server
- **WHEN** a client calls `route` without an API key
- **THEN** the request is rejected as unauthorized and no usage event is written

#### Scenario: Revoked key rejected
- **GIVEN** a key that the admin has revoked
- **WHEN** a client calls `route` with that key
- **THEN** the request is rejected as unauthorized

#### Scenario: User id comes from the key
- **GIVEN** a key issued to user `alice`
- **WHEN** a client calls `route` with that key and claims another user id
- **THEN** the usage event is recorded for `alice`

### Requirement: Admin authorization
The system SHALL allow `get_usage_stats` only for keys with the admin flag.

#### Scenario: Non-admin asks for statistics
- **GIVEN** a valid key without the admin flag
- **WHEN** the client calls `get_usage_stats`
- **THEN** the call fails as forbidden

### Requirement: Key management
The system SHALL provide CLI commands to issue, list and revoke keys, show a new key only once at issue time, and store only a hash of each key.

#### Scenario: Issue a key
- **GIVEN** the maintainer on the server host
- **WHEN** they issue a key for user `bob`
- **THEN** the command prints the key once and a request with that key is accepted as `bob`

#### Scenario: Stored key is not readable
- **GIVEN** an issued key
- **WHEN** the maintainer lists the keys
- **THEN** the list shows user ids, admin flags and status but not the key values
