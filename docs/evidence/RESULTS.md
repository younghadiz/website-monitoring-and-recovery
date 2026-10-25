# Verification results

## Outcome

Website monitoring and recovery checks completed successfully.
Local validation is supported by recorded terminal output.
Live execution outcomes below are confirmed.

## Local validation

- Validation session date: 2026-10-24.
- Implementation commit: `d358bfe` — feat: implement website monitoring email alerts and recovery.
- Implementation integration commit: `f592d18`.
- Python environment: Python 3.12.
- Installed dependency versions: [requirements.lock](../../requirements.lock).
- Python compilation: Passed.
- Unit tests: All 8 mocked tests passed.
- Dependency consistency: Passed; no broken requirements found.
- Shell syntax checks: Passed.
- Git whitespace validation: Passed.
- Implementation branch and develop pushed to GitHub and GitLab: Passed.

The commits above identify the implementation milestone. The precise
source revision used for cloud testing is identified by the captured
tested-source-commit evidence when available.

## Behavior verified through mocked tests

- HTTP 200 is classified as healthy.
- HTTP 503 is classified as unhealthy.
- HTTP request timeout is classified as unhealthy.
- Email failure does not prevent container recovery.
- Unavailable SSH triggers server recovery.
- SSH authentication failure does not trigger a server reboot.
- Observation mode does not attempt recovery.
- A continuing outage does not repeatedly send notifications or attempt recovery.

Mocked tests validate program behavior separately from live execution.

## Live execution — operator-confirmed results

- Healthy deployed website returned HTTP 200: Passed.
- Deliberate HTTP 503 response detected: Passed.
- Outage notification submitted successfully through SMTP: Passed.
- Notification received in the recipient inbox: Passed.
- Stopped Docker container recovered through SSH: Passed.
- Container recovery completed without a server reboot: Passed.
- SSH-unavailable experiment triggered a Linode API reboot: Passed.
- Boot ID changed after the reboot: Passed.
- SSH access returned after reboot: Passed.
- Python restarted the application container after reboot: Passed.
- Post-recovery HTTP 200 verified: Passed.
- Immediate check and at least two recurring scheduled checks observed: Passed.

## Cleanup

Cleanup completed. All dedicated lab resources were removed,
lab credentials were revoked, and no project-associated paid
resources remain.

See the [cleanup record](CLEANUP.md).
