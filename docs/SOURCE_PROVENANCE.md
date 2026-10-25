# Source provenance

## Original reference

- Author: Nana Janashia / TechWorld with Nana.
- Module: 14 — Automation with Python.
- Project: Capstone 6 — Website Monitoring and Recovery.
- Repository:
  https://gitlab.com/twn-devops-bootcamp/latest/14-automation-with-python/automation-projects
- Reference branch used: main.
- Inspected reference commit:
  fb3d2f537cb599e734ba6c24683b179bb8ae3840
- Earlier preserved commit:
  4bac3655ff774fd3c66876c641cb5fad7ad5ab08
- Relevant original source: monitor-website.py.

## Source scope

The imported reference contained eight Python lesson scripts:

- add-env-tags.py
- cleanup-snapshots.py
- create-vpc.py
- ec2-status-checks.py
- eks-status-checks.py
- monitor-website.py
- restore-volume.py
- volume-backups.py

Only monitor-website.py is used for this website-monitoring capstone.
The seven unrelated scripts were removed in the foundation milestone.
Their original contents remain available in the preserved Git history.

## Retained approach

- Requests-based HTTP validation.
- SMTP email notifications.
- Paramiko SSH application recovery.
- Linode SDK server reboot.
- schedule-based recurring checks.
- Nana's principal recovery function names.

## Adaptations

- Environment-based configuration.
- Dedicated named Docker container.
- Verified SSH host keys.
- Explicit HTTP, SSH and SMTP timeouts.
- Separate notification and recovery error handling.
- SSH recovery attempted before server reboot.
- Docker restart instead of Docker start.
- Post-recovery HTTP verification.
- Bounded recovery waiting.
- Per-outage suppression and in-memory recovery cooldown.
- Observation mode and explicit recovery option.
- Mocked unit tests and execution evidence.

## Development milestones

- Foundation implementation: 165447f.
- Foundation integration into develop: 7f0b3bc.
- Monitoring and recovery implementation: d358bfe.
- Monitoring and recovery integration into develop: f592d18.

Feature work was integrated into develop using --no-ff merges.
These commits identify development milestones, rather than establishing
the precise revision used for every subsequent cloud test.

## Current status

Implementation is complete. All eight mocked unit tests and local
validation checks passed.

The project operator confirms successful live HTTP checks, SMTP submission,
inbox delivery, SSH container recovery, Linode reboot recovery, changed
boot ID, restored HTTP 200 and scheduled checks.

The project operator also confirms completed resource deletion and
credential cleanup, with no project-associated paid resources remaining.

Detailed records:

- [Verification results](evidence/RESULTS.md).
- [Cleanup record](evidence/CLEANUP.md).

Runbook instructions and expected outputs describe reproduction steps;
execution records document actual outcomes.

## Attribution

Original upstream history and authorship are preserved.
Project adaptations are recorded in subsequent commits.
This document does not assert a new licence over upstream material.
