# Website Monitoring and Recovery

A Python automation capstone based on Nana Janashia's
TechWorld with Nana Module 14 project.

## Goal and scope

Monitor an HTTP website, send an outage notification, recover its
Docker container through SSH, and request a Linode API reboot when
SSH cannot establish a network connection.

The project uses one Ubuntu application server and an external Python
monitor running on the operator's Mac.

## Architecture

- Control machine: Python monitor on macOS.
- HTTP checks: Requests.
- Notifications: SMTP with STARTTLS.
- Application recovery: Paramiko SSH and Docker restart.
- Server recovery: Linode API through linode-api4.
- Scheduling: schedule.
- Application: Nginx in Docker on Ubuntu 24.04.
- Configuration: Environment variables loaded through python-dotenv.

## Implementation

The implementation retains Nana's send_notification, restart_container,
restart_server_and_container and monitor_application function structure.

Adaptations include environment-based configuration, explicit timeouts,
verified SSH host keys, separate notification and recovery error handling,
post-recovery HTTP checks, bounded recovery waiting, outage suppression
and an in-memory recovery cooldown.

Observation mode checks availability and sends outage notifications.
Automatic recovery requires the --recover option.

## Verification

All eight mocked unit tests and local validation checks passed.
Confirms successful live HTTP checks,
email delivery, SSH container recovery, Linode reboot recovery,
changed boot ID, restored HTTP 200 and recurring scheduled checks.

See [verification results](docs/evidence/RESULTS.md) for the detailed record.

Mocked tests validate program behavior separately from live cloud execution.

## Limitations

- The monitor requires the Mac to remain awake, connected and running.
- SSH unavailability does not conclusively prove server failure.
- Recovery state and cooldown are held in memory and reset on process restart.
- An unresolved outage receives one recovery attempt per process.
- Restarting a container does not repair incorrect application configuration.
- HTTP 200 verifies basic endpoint availability.
- The disposable lab uses root SSH with a dedicated local key.
- Persistent deployment of the monitor is outside this capstone's scope.

## Cleanup

All dedicated lab resources were removed, lab credentials were revoked,
and no project-associated paid resources remain.

See the [cleanup record](docs/evidence/CLEANUP.md).

## Reproduction

See the [standalone runbook](docs/RUNBOOK.md) for setup, full source
snapshots, deployment, verification, troubleshooting and cleanup.

## Attribution

Original educational reference:
https://gitlab.com/twn-devops-bootcamp/latest/14-automation-with-python/automation-projects

Inspected reference commit:
fb3d2f537cb599e734ba6c24683b179bb8ae3840

Original author: Nana Janashia / TechWorld with Nana.

Original upstream history and authorship are preserved.
See [source provenance](docs/SOURCE_PROVENANCE.md).
