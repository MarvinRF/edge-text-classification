# 0001. Decision records

- Status: accepted (16/11/2026)

## Context
A benchmark is only as credible as the choices behind it: datasets, models, splits, thresholds. Those choices are easy to forget and easy to change quietly after seeing results.

## Decision
Every architecture or protocol decision becomes an ADR in this folder, numbered, with context, decision, consequences, and alternatives. Statuses: proposed, accepted, superseded. Changing a decision means a new ADR that points to the old one; accepted ADRs are not edited.

## Consequences
- Newcomers understand the design by reading the ADRs, without depending on conversations.
- A proposed decision states what is missing to close it, and in which milestone.

## Alternatives
- A single decision log file: simpler, but harder to link to and to supersede entry by entry.
