# 0002. Acceptance criteria before measuring

- Status: proposed (16/11/2026). Closes when the team ratifies the values in `docs/acceptance_criteria.md`, before M1.

## Context
This project grew out of an industrial challenge where the deciding constraint (the model would not fit the device) was assumed, not measured. Criteria chosen after seeing results tend to bend toward the preferred option.

## Decision
- Acceptance criteria are written in `docs/acceptance_criteria.md` and frozen in `src/edgecls/criteria.py` (`AcceptanceCriteria`, a frozen dataclass validated at creation).
- They are merged before any experiment; the commit date is the evidence.
- Every result table reports, per path and device, which criteria it fails.
- Changing a value requires a new ADR stating the reason, and every affected result is re-evaluated.

## Consequences
- "Accepted" means the same thing in every milestone and on every device.
- Some paths may fail a criterion the team would have liked to relax; that is reported, not hidden.

## Alternatives
- Reporting metrics without thresholds: neutral, but it does not support a decision, which is the point of the project.
