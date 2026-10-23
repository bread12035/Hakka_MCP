# Delta spec template

File: `openspec/changes/<name>/specs/<domain>/spec.md`. One file per domain. English.

Sections are `## ADDED Requirements`, `## MODIFIED Requirements` and `## REMOVED Requirements`. Use only the ones you need. `## Purpose` is optional and used only when the domain is new: one line on what the domain covers.

```markdown
## Purpose
<One line. Only for a new domain.>

## ADDED Requirements

### Requirement: <Unique requirement name>
The system SHALL <observable behavior in one sentence>.

#### Scenario: <Unique scenario name>
- **GIVEN** <starting state>
- **WHEN** <action or event>
- **THEN** <observable result>

#### Scenario: <Another scenario, for example a failure case>
- **GIVEN** ...
- **WHEN** ...
- **THEN** ...

## MODIFIED Requirements

### Requirement: <Name of an existing requirement, spelled exactly>
The system SHALL <the new full text>.

#### Scenario: <Every scenario of the requirement, old and new. This block replaces the old one>
- **WHEN** ...
- **THEN** ...

## REMOVED Requirements

### Requirement: <Name of an existing requirement>
**Reason**: <why it goes>
```

Rules:

- A requirement uses SHALL or MUST. Each has at least one scenario.
- A MODIFIED block replaces the whole requirement. Copy the old scenarios you keep.
- Requirement names are unique in the domain. Scenario names are unique in the change. Two scenario names that give the same snake_case name are an error.
- A scenario describes behavior a user or caller can see, not an internal step.
- The test for a scenario is `test_<scenario name in snake_case>`. Example: "Wrong password" gives `test_wrong_password`.
