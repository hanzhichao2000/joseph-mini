# joseph-mini

Trading core for the joseph-* family: runtime, portfolio, account, OMS, hard-risk, the day-bar
venue simulator and the venue-simulator contract. **One real account has one active JO execution
authority at a time**, and Runtime alone owns the account HALT latch.

Route A (dismantle-and-adopt), Project `joseph-build` #6:

- Receive mature modules from the dismantle line (#862), one unit at a time. Each handover names
  ownership, the exact commit, how existing entry points migrate, and what ran in isolation.
- A unit counts as adopted only when the clean-environment proof passes: install and start without
  the package, then install it and verify every supported entry point and must-run test.
- QT5m formal replay lives here once adopted; the pilot repo only holds hypothesis experiments.

Boundaries:

- `joseph-api` supplies the shared data model; `joseph-dal` supplies pinned revisions;
  `joseph-alpha` supplies factor/strategy definitions and the pure-Python backend.
- The venue-simulator contract is public; its tick implementation is private (`joseph-native`).
- `joseph-live` wraps vn.py's EventEngine and gateways; it never owns JO orders.
- Evidence attaches to GitHub Issues as run manifests; no report trees in this repository.
