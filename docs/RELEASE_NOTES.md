# Release notes

## Implementation

- Scheduled HTTP website checks using Requests
- SMTP outage notifications
- SSH-based Docker application recovery
- Linode API server reboot when SSH cannot connect
- Post-recovery HTTP verification
- Environment-based configuration and verified SSH host keys
- Per-outage suppression and in-memory recovery cooldown

## Validation

Actual results and tested source commit:
[evidence/RESULTS.md](evidence/RESULTS.md)

## Cleanup

Actual resource and credential cleanup:
[evidence/CLEANUP.md](evidence/CLEANUP.md)

## Limitations

The monitor runs on the operator's Mac.
Network failure can resemble server failure.
Recovery state is not persisted across process restarts.
This release does not add Jenkins, AWS, EKS or snapshot automation.

## Attribution

Based on Nana Janashia's Module 14 website-monitoring reference.
See SOURCE_PROVENANCE.md.
