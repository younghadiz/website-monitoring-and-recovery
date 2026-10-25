# Website Monitoring and Recovery — Complete Implementation Runbook

## 1. Purpose

This is the complete, standalone implementation guide for the Website Monitoring
and Recovery capstone. It contains the full source inline, at the stage where
each file is created, followed by deployment, experiments, troubleshooting,
evidence preservation, cleanup, final documentation and release commands.
No separate source generator is required to read or reproduce this guide.

**Existing completed project:** save this document as `docs/RUNBOOK.md` on your
`docs/final-runbook` branch. Review the documentation and release sections;
do not repeat cloud provisioning, outage injection or credential setup merely
to save this runbook. The numbered sequence is for a fresh reproduction.

## 2. Project requirements

1. Monitor a website and identify HTTP failures or connection failures.
2. Send email notifications when the application is unhealthy.
3. Recover the application container through SSH.
4. Reboot the dedicated server through the Linode API when SSH cannot connect,
   then restart the application and verify availability.
5. Schedule recurring checks.

These are the five capabilities used throughout this project. The original
assignment screenshots are not reproduced here. Jenkins, AWS, EKS and snapshot
automation are outside this implementation's scope.

## 3. Source and implementation boundaries

Educational reference: Nana Janashia / TechWorld with Nana, Module 14:
https://gitlab.com/twn-devops-bootcamp/latest/14-automation-with-python/automation-projects

Upstream baseline: `fb3d2f537cb599e734ba6c24683b179bb8ae3840`.
The nine implementation files below were retrieved from GitHub `develop` at
`0869fcd7e86ade03b8775a73c2fea57d3373e644` for this runbook. That reference identifies
the documentation source snapshot, not an independently established cloud-test revision.

Original history is retained. The monitor keeps Nana's principal function
structure and libraries, with configuration, host-key verification, timeouts,
post-recovery checks and outage suppression adapted for this lab.

## 4. Architecture

| Component | Location | Responsibility |
| --- | --- | --- |
| Python monitor | Operator's Mac | Check HTTP, send alerts, orchestrate recovery and schedule checks |
| SMTP server | Gmail | Accept authenticated STARTTLS outage notifications |
| Paramiko/OpenSSH | Mac to application server | Restart the named Docker container over verified SSH |
| Linode API | External control plane | Reboot the dedicated server when SSH cannot connect |
| Docker and Nginx | Ubuntu 24.04 Linode | Serve HTTP on host port 8080 |
| Dedicated firewall | Linode | Permit TCP 22/8080 only from the operator's IPv4 /32 |

## 5. Cost, security and Git principles

Prepare source and validate locally before creating the chargeable server.
Collect execution evidence before deletion. Delete the instance and paid
add-ons after verification; powering off alone is not the cleanup criterion.

Use a dedicated key, verified host fingerprint, dedicated API token and app
password. Never commit `.env`, private keys or raw logs. This lab uses root
SSH for the disposable server; it is not a general production access design.

GitHub (`origin`) is primary; GitLab (`gitlab`) is the mirror. Preserve staged
milestones through `feature/* → develop → main`, with `--no-ff` integrations.
Write the final README and runbook after verification and cloud cleanup.

## 6. Recorded development environment

| Item | Recorded value |
| --- | --- |
| Control machine | macOS, user's Mac |
| Interactive shell | Zsh; operational runbook commands use Bash |
| Python | 3.12 family, shown in installation output |
| Server operating system | Ubuntu 24.04 lab target |
| Dependencies | Full pinned requirements.lock below |
| Application image | nginx:stable-alpine; capture actual deployed digest per execution |
| Local tests | Eight mocked unit tests passed in shared output |

Do not substitute the earlier Kubernetes capstone's tool versions or results
for this project's evidence. Exact OS patch versions and cloud-test timestamp
are not invented here.

## 7. Scope, prerequisites and execution locations

This guide reproduces Nana Janashia's Module 14 website-monitoring capstone.
The monitor runs externally on a Mac; Nginx runs in Docker on a dedicated
Ubuntu 24.04 Linode. There is no Jenkins pipeline in this project.

Mac prerequisites: Git, Python 3.11 or newer, OpenSSH and curl. Python 3.12
was used for the recorded local validation. A Linode account, GitHub/GitLab
repositories and a Gmail account supporting app passwords are needed for
live reproduction.

The completed run's results and cleanup records are in docs/evidence.
Instructions and expected results are separate from execution proof.
A new reproduction must record its own tested revision and outcomes.

**Mac Terminal:** enter Bash once before following the operational steps:

```bash
bash
```

Keep this session open so exported infrastructure variables persist.
Do not paste `set -euo pipefail` into interactive Zsh. Strict shell options
belong inside scripts or separate Bash blocks. Check each command's result
before continuing after an error.

Each source file is provided in full at its implementation stage. Follow the
sequence rather than creating later-stage files before clean-tree checks.

## 8. Repository setup

Choose one route. Existing-release reproduction does not require new
implementation commits. Fresh development uses empty destination remotes.

### 2.1 Fresh development preserving upstream history

**Mac Terminal:** these destination URLs belong to the original project.
For a new independent reproduction, replace them with your own empty
GitHub/GitLab repositories. Do not push a fresh baseline over an existing
completed project.

```bash
mkdir -p "$HOME/Documents/tech-workspace/devops-capstone-projects"
cd "$HOME/Documents/tech-workspace/devops-capstone-projects"
```

Run the guarded import in a child Bash process:

```bash
bash <<'IMPORT'
set -euo pipefail
test ! -e website-monitoring-and-recovery
git clone https://gitlab.com/twn-devops-bootcamp/latest/14-automation-with-python/automation-projects.git website-monitoring-and-recovery
cd website-monitoring-and-recovery
git remote rename origin upstream
git cat-file -e fb3d2f537cb599e734ba6c24683b179bb8ae3840^{commit}
git switch -C main fb3d2f537cb599e734ba6c24683b179bb8ae3840
git branch --unset-upstream || true
git remote add origin git@github.com:younghadiz/website-monitoring-and-recovery.git
git remote add gitlab git@gitlab.com:devops-engineering-projects/website-monitoring-and-recovery.git
git push -u origin main
git push gitlab main
git switch -c develop
git push -u origin develop
git push gitlab develop
git switch -c feature/project-foundation
IMPORT
```

Only after successful import:

```bash
cd website-monitoring-and-recovery
```

If the folder already exists, inspect `git status`, `git remote -v` and
`git log --oneline --all` there. Do not delete it or repeat the import
blindly. Preserve Nana's original history and authorship.

### 2.2 Existing release

**Mac Terminal:** in a parent directory without an existing destination:

```bash
git clone git@github.com:younghadiz/website-monitoring-and-recovery.git
cd website-monitoring-and-recovery
git remote add gitlab git@gitlab.com:devops-engineering-projects/website-monitoring-and-recovery.git
git fetch origin --tags
git tag --list
```

Inspect the intended tag using `git show TAG`, then check out that actual
tag using `git switch --detach TAG`. TAG denotes the real tag you selected,
not a literal command argument. Skip development milestone commits in
section 3; install dependencies and run validation only. To record a new
execution, create a new branch from the selected release without modifying
its existing tag or recreating historical implementation commits.

## 9. Local implementation and staged Git workflow

### 3.1 Foundation

**Mac Terminal, fresh-development route:** create the foundation files below.

#### File: `.gitignore`

**Execution location:** Mac Terminal, repository root.

Excludes local credentials, virtual environments, bytecode and private evidence. The public .env.example remains tracked.

<!-- SOURCE:.gitignore -->
```bash
cat > .gitignore <<'CAPSTONE_28557EB7A320A3C8'
.venv/
__pycache__/
*.py[cod]
.env
.env.*
!.env.example
.private/
*.log
.DS_Store
CAPSTONE_28557EB7A320A3C8
```
<!-- END_SOURCE:.gitignore -->

#### File: `.env.example`

**Execution location:** Mac Terminal, repository root.

Defines the configuration contract. Its example values are replaced by the interactive setup later; real credentials are never embedded in this runbook.

<!-- SOURCE:.env.example -->
```bash
cat > .env.example <<'CAPSTONE_2C4754A1F5BFF00C'
WEBSITE_URL=http://YOUR_SERVER_IPV4:8080/
SSH_HOST=YOUR_SERVER_IPV4
SSH_USERNAME=root
SSH_KEY_PATH=/absolute/path/to/your/dedicated/private/key
SSH_KNOWN_HOSTS=/absolute/path/to/your/dedicated/known_hosts
CONTAINER_NAME=capstone-nginx
LINODE_ID=YOUR_NUMERIC_LINODE_ID
LINODE_TOKEN=
EMAIL_ADDRESS=
EMAIL_PASSWORD=
EMAIL_RECIPIENT=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
CHECK_INTERVAL_SECONDS=300
RECOVERY_TIMEOUT_SECONDS=240
RECOVERY_COOLDOWN_SECONDS=900
CAPSTONE_2C4754A1F5BFF00C
```
<!-- END_SOURCE:.env.example -->

#### File: `requirements.in`

**Execution location:** Mac Terminal, repository root.

Declares the five direct libraries using compatibility ranges.

<!-- SOURCE:requirements.in -->
```bash
cat > requirements.in <<'CAPSTONE_7F7341FF1DE4BBEF'
requests>=2.32,<3
paramiko>=3.5,<5
linode-api4>=5,<6
schedule>=1.2,<2
python-dotenv>=1,<2
CAPSTONE_7F7341FF1DE4BBEF
```
<!-- END_SOURCE:requirements.in -->

#### File: `requirements.lock`

**Execution location:** Mac Terminal, repository root.

Pins the dependency set from this implementation. Install it for reproduction rather than resolving requirements.in again.

<!-- SOURCE:requirements.lock -->
```bash
cat > requirements.lock <<'CAPSTONE_582B0BFACA1C5467'
bcrypt==5.0.0
certifi==2026.10.23
cffi==2.1.1
charset-normalizer==3.5.2
cryptography==50.0.2
Deprecated==3.0.0
idna==3.20
invoke==3.0.3
linode_api4==5.48.0
paramiko==4.0.0
polling==0.3.2
pycparser==3.12
PyNaCl==1.6.2
python-dotenv==1.2.4
requests==2.34.2
schedule==1.2.2
urllib3==2.8.0
wrapt==2.5.1
CAPSTONE_582B0BFACA1C5467
```
<!-- END_SOURCE:requirements.lock -->

#### File: `scripts/git-milestone.sh`

**Execution location:** Mac Terminal, repository root.

Reviews changes, asks for commit confirmation, pushes both remotes, and merges into develop. Its initial check requires an empty staging area: the foundation uses explicit Git commands below because git rm has already staged deletions.

<!-- SOURCE:scripts/git-milestone.sh -->
```bash
mkdir -p scripts
cat > scripts/git-milestone.sh <<'CAPSTONE_4D3AE26DD389870A'
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
    echo "Usage: bash scripts/git-milestone.sh BRANCH MESSAGE FILE..."
    exit 2
fi

expected_branch="$1"
message="$2"
shift 2

test "$(git branch --show-current)" = "$expected_branch"
git diff --cached --quiet
git diff --check

git add -- "$@"
git diff --cached --check
git diff --cached --stat
git diff --cached

read -r -p "Review complete. Type commit to continue: " answer
test "$answer" = "commit"

git commit -m "$message"
test -z "$(git status --porcelain)"

git push -u origin "$expected_branch"
git push gitlab "$expected_branch"

git switch develop
test -z "$(git status --porcelain)"
git pull --ff-only origin develop

git merge --no-ff "$expected_branch" \
  -m "merge: integrate ${expected_branch}"

git push origin develop
git push gitlab develop

test -z "$(git status --porcelain)"
git status --short --branch
CAPSTONE_4D3AE26DD389870A
chmod +x scripts/git-milestone.sh
```
<!-- END_SOURCE:scripts/git-milestone.sh -->


Remove the seven unrelated lesson scripts; their history remains intact:

```bash
git rm add-env-tags.py cleanup-snapshots.py create-vpc.py ec2-status-checks.py eks-status-checks.py restore-volume.py volume-backups.py
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip check
bash -n scripts/git-milestone.sh
```

The seven deletions are already staged. Use explicit Git commands for this
foundation milestone: the helper's empty-index guard would otherwise stop.
Review the staged diff for credentials before committing.

```bash
git add .gitignore .env.example requirements.in requirements.lock scripts/git-milestone.sh
git diff --cached --check
git diff --cached --stat
git diff --cached
```

After reviewing the diff, commit and integrate:

```bash
bash <<'FOUNDATION'
set -euo pipefail
test "$(git branch --show-current)" = feature/project-foundation
git commit -m "chore: establish website recovery project foundation"
test -z "$(git status --porcelain)"
git push -u origin feature/project-foundation
git push gitlab feature/project-foundation
git switch develop
git pull --ff-only origin develop
git merge --no-ff feature/project-foundation -m "merge: integrate project foundation"
git push origin develop
git push gitlab develop
FOUNDATION
```

Expected: clean develop, with the feature branch and merge pushed to both
remotes. If a command fails after a partial push, inspect status and history
and finish the remaining operation; do not recreate completed commits.

### 3.2 Monitoring implementation

**Mac Terminal:**

```bash
bash <<'BRANCH'
set -euo pipefail
test "$(git branch --show-current)" = develop
test -z "$(git status --porcelain)"
git switch -c feature/monitoring-and-recovery
BRANCH
```


#### File: `monitor-website.py`

**Execution location:** Mac Terminal, repository root.

Requests performs HTTP checks; SMTP sends notifications independently of recovery; Paramiko restarts Docker; the Linode SDK reboots only for classified SSH connection failures. Observation is default; --recover enables changes. Global outage/cooldown state resets when the process restarts.

<!-- SOURCE:monitor-website.py -->
```bash
cat > monitor-website.py <<'CAPSTONE_93859DF6DCE439CA'
import argparse
import logging
import os
import shlex
import socket
import smtplib
import ssl
import time
from email.message import EmailMessage
from pathlib import Path

import linode_api4
import paramiko
import requests
import schedule
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().with_name(".env"))

WEBSITE_URL = os.environ.get("WEBSITE_URL", "")
SSH_HOST = os.environ.get("SSH_HOST", "")
SSH_USERNAME = os.environ.get("SSH_USERNAME", "root")
SSH_KEY_PATH = os.path.expanduser(os.environ.get("SSH_KEY_PATH", ""))
SSH_KNOWN_HOSTS = os.path.expanduser(
    os.environ.get("SSH_KNOWN_HOSTS", "")
)
CONTAINER_NAME = os.environ.get("CONTAINER_NAME", "capstone-nginx")
LINODE_ID = os.environ.get("LINODE_ID", "")
LINODE_TOKEN = os.environ.get("LINODE_TOKEN", "")

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", EMAIL_ADDRESS)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

CHECK_INTERVAL_SECONDS = int(
    os.environ.get("CHECK_INTERVAL_SECONDS", "300")
)
RECOVERY_TIMEOUT_SECONDS = int(
    os.environ.get("RECOVERY_TIMEOUT_SECONDS", "240")
)
RECOVERY_COOLDOWN_SECONDS = int(
    os.environ.get("RECOVERY_COOLDOWN_SECONDS", "900")
)

logger = logging.getLogger("website-monitor")

outage_handled = False
last_recovery_at = float("-inf")


class ServerUnavailable(Exception):
    """SSH could not establish a network connection."""


def check_application():
    try:
        response = requests.get(
            WEBSITE_URL,
            timeout=(3, 5),
            allow_redirects=False,
        )
        try:
            status = response.status_code
        finally:
            response.close()

        if status == 200:
            return True, "HTTP 200"

        return False, f"HTTP {status}"

    except requests.RequestException as error:
        return False, f"HTTP request failed: {type(error).__name__}"


def send_notification(email_msg):
    message = EmailMessage()
    message["Subject"] = "SITE DOWN - DevOps capstone"
    message["From"] = EMAIL_ADDRESS
    message["To"] = EMAIL_RECIPIENT
    message.set_content(email_msg)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ssl.create_default_context())
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(message)

    logger.info("Email notification submitted to SMTP server")


def restart_container():
    logger.info("Attempting application recovery through SSH")

    ssh = paramiko.SSHClient()
    ssh.load_host_keys(SSH_KNOWN_HOSTS)
    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

    try:
        try:
            ssh.connect(
                hostname=SSH_HOST,
                username=SSH_USERNAME,
                key_filename=SSH_KEY_PATH,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
        except (
            paramiko.ssh_exception.NoValidConnectionsError,
            socket.timeout,
            TimeoutError,
        ) as error:
            raise ServerUnavailable(
                "SSH network connection unavailable"
            ) from error

        command = (
            "docker restart --time 10 "
            + shlex.quote(CONTAINER_NAME)
        )

        stdin, stdout, stderr = ssh.exec_command(
            command,
            timeout=30,
        )
        stdin.close()

        output = stdout.read().decode().strip()
        error_output = stderr.read().decode().strip()
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            raise RuntimeError(
                f"Docker restart failed with exit status {exit_status}"
            )

        if error_output:
            logger.warning("Docker command wrote to stderr")

        logger.info("Docker restart completed: %s", output)

    finally:
        ssh.close()


def wait_for_application(timeout_seconds):
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        healthy, detail = check_application()

        if healthy:
            logger.info("Recovery verified: %s", detail)
            return True

        logger.info("Waiting for application: %s", detail)
        time.sleep(5)

    return False


def restart_server_and_container():
    logger.warning("Requesting reboot through the Linode API")

    client = linode_api4.LinodeClient(
        LINODE_TOKEN,
        timeout=20,
    )
    server = client.load(
        linode_api4.Instance,
        int(LINODE_ID),
    )
    server.reboot()

    deadline = time.monotonic() + RECOVERY_TIMEOUT_SECONDS
    time.sleep(10)

    while time.monotonic() < deadline:
        try:
            restart_container()
        except ServerUnavailable:
            logger.info("SSH is not ready after reboot")
            time.sleep(10)
            continue
        except Exception as error:
            raise RuntimeError(
                "SSH/application recovery failed after reboot: "
                + type(error).__name__
            ) from error

        remaining = max(1, int(deadline - time.monotonic()))

        if wait_for_application(remaining):
            return

        raise RuntimeError("Application did not recover after reboot")

    raise TimeoutError("Server recovery exceeded its waiting period")


def monitor_application(recover=False):
    global outage_handled
    global last_recovery_at

    healthy, detail = check_application()

    if healthy:
        if outage_handled:
            logger.info("Outage ended")
        outage_handled = False
        logger.info("Application is running successfully: %s", detail)
        return True

    logger.warning("Application down: %s", detail)

    if outage_handled:
        logger.warning(
            "Outage already handled; waiting for recovery or manual action"
        )
        return False

    outage_handled = True

    try:
        send_notification(detail)
    except Exception as error:
        logger.error(
            "Email notification failed: %s",
            type(error).__name__,
        )

    if not recover:
        logger.warning("Recovery disabled; observation mode")
        return False

    now = time.monotonic()

    if now - last_recovery_at < RECOVERY_COOLDOWN_SECONDS:
        logger.warning("Recovery suppressed by cooldown")
        return False

    last_recovery_at = now

    try:
        try:
            restart_container()
        except ServerUnavailable:
            restart_server_and_container()
        else:
            if not wait_for_application(60):
                raise RuntimeError(
                    "Application is still unhealthy after container restart"
                )

    except Exception as error:
        logger.error("Recovery failed: %s", type(error).__name__)
        return False

    outage_handled = False
    return True


def validate_configuration(recover):
    required = {
        "WEBSITE_URL": WEBSITE_URL,
        "EMAIL_ADDRESS": EMAIL_ADDRESS,
        "EMAIL_PASSWORD": EMAIL_PASSWORD,
        "EMAIL_RECIPIENT": EMAIL_RECIPIENT,
    }

    if recover:
        required.update({
            "SSH_HOST": SSH_HOST,
            "SSH_KEY_PATH": SSH_KEY_PATH,
            "SSH_KNOWN_HOSTS": SSH_KNOWN_HOSTS,
            "LINODE_ID": LINODE_ID,
            "LINODE_TOKEN": LINODE_TOKEN,
        })

    missing = [name for name, value in required.items() if not value]

    if missing:
        raise ValueError(
            "Missing configuration: " + ", ".join(missing)
        )

    if not WEBSITE_URL.startswith(("http://", "https://")):
        raise ValueError("WEBSITE_URL must use http:// or https://")

    if CHECK_INTERVAL_SECONDS < 10:
        raise ValueError("CHECK_INTERVAL_SECONDS must be at least 10")

    if RECOVERY_TIMEOUT_SECONDS < 30:
        raise ValueError("RECOVERY_TIMEOUT_SECONDS must be at least 30")

    if RECOVERY_COOLDOWN_SECONDS < 60:
        raise ValueError("RECOVERY_COOLDOWN_SECONDS must be at least 60")

    if recover:
        if not LINODE_ID.isdigit():
            raise ValueError("LINODE_ID must be numeric")

        for name, value in (
            ("SSH_KEY_PATH", SSH_KEY_PATH),
            ("SSH_KNOWN_HOSTS", SSH_KNOWN_HOSTS),
        ):
            if not Path(value).is_file():
                raise ValueError(f"{name} must reference an existing file")


def main():
    parser = argparse.ArgumentParser(
        description="Nana-aligned website monitoring and recovery"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one check and exit",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Enable Docker recovery and Linode reboot",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)sZ %(levelname)s %(message)s",
    )
    logging.Formatter.converter = time.gmtime

    validate_configuration(args.recover)

    logger.info(
        "Monitor starting; automatic recovery=%s",
        args.recover,
    )

    if args.once:
        return 0 if monitor_application(args.recover) else 1

    monitor_application(args.recover)

    schedule.every(CHECK_INTERVAL_SECONDS).seconds.do(
        monitor_application,
        recover=args.recover,
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by operator")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
CAPSTONE_93859DF6DCE439CA
```
<!-- END_SOURCE:monitor-website.py -->

#### File: `tests/test_monitor.py`

**Execution location:** Mac Terminal, repository root.

These eight tests mock network and recovery calls. They verify decisions and suppression without sending email, connecting to SSH or rebooting infrastructure.

<!-- SOURCE:tests/test_monitor.py -->
```bash
mkdir -p tests
cat > tests/test_monitor.py <<'CAPSTONE_7CF2E99C691AEB7D'
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import paramiko
import requests


SCRIPT = Path(__file__).resolve().parents[1] / "monitor-website.py"
SPEC = importlib.util.spec_from_file_location("monitor_website", SCRIPT)
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class MonitorTests(unittest.TestCase):
    def setUp(self):
        monitor.outage_handled = False
        monitor.last_recovery_at = float("-inf")

    def test_http_200_is_healthy(self):
        response = Mock(status_code=200)

        with patch.object(
            monitor.requests, "get", return_value=response
        ) as get:
            self.assertEqual(
                monitor.check_application(),
                (True, "HTTP 200"),
            )

        get.assert_called_once_with(
            monitor.WEBSITE_URL,
            timeout=(3, 5),
            allow_redirects=False,
        )
        response.close.assert_called_once()

    def test_http_503_is_unhealthy(self):
        with patch.object(
            monitor.requests,
            "get",
            return_value=Mock(status_code=503),
        ):
            self.assertEqual(
                monitor.check_application(),
                (False, "HTTP 503"),
            )

    def test_request_timeout_is_unhealthy(self):
        with patch.object(
            monitor.requests,
            "get",
            side_effect=requests.Timeout(),
        ):
            healthy, detail = monitor.check_application()

        self.assertFalse(healthy)
        self.assertIn("Timeout", detail)

    def test_email_failure_does_not_prevent_container_recovery(self):
        with (
            patch.object(
                monitor,
                "check_application",
                return_value=(False, "HTTP 503"),
            ),
            patch.object(
                monitor,
                "send_notification",
                side_effect=RuntimeError("SMTP unavailable"),
            ),
            patch.object(monitor, "restart_container") as restart,
            patch.object(
                monitor,
                "wait_for_application",
                return_value=True,
            ),
            patch.object(
                monitor,
                "restart_server_and_container",
            ) as reboot,
        ):
            self.assertTrue(monitor.monitor_application(recover=True))

        restart.assert_called_once()
        reboot.assert_not_called()

    def test_unreachable_ssh_uses_server_recovery(self):
        with (
            patch.object(
                monitor,
                "check_application",
                return_value=(False, "connection failure"),
            ),
            patch.object(monitor, "send_notification"),
            patch.object(
                monitor,
                "restart_container",
                side_effect=monitor.ServerUnavailable(),
            ),
            patch.object(
                monitor,
                "restart_server_and_container",
            ) as reboot,
        ):
            self.assertTrue(monitor.monitor_application(recover=True))

        reboot.assert_called_once()

    def test_authentication_failure_does_not_reboot(self):
        with (
            patch.object(
                monitor,
                "check_application",
                return_value=(False, "HTTP 503"),
            ),
            patch.object(monitor, "send_notification"),
            patch.object(
                monitor,
                "restart_container",
                side_effect=paramiko.AuthenticationException(),
            ),
            patch.object(
                monitor,
                "restart_server_and_container",
            ) as reboot,
        ):
            self.assertFalse(monitor.monitor_application(recover=True))

        reboot.assert_not_called()

    def test_observation_mode_does_not_recover(self):
        with (
            patch.object(
                monitor,
                "check_application",
                return_value=(False, "HTTP 503"),
            ),
            patch.object(monitor, "send_notification"),
            patch.object(monitor, "restart_container") as restart,
            patch.object(
                monitor,
                "restart_server_and_container",
            ) as reboot,
        ):
            self.assertFalse(monitor.monitor_application(recover=False))

        restart.assert_not_called()
        reboot.assert_not_called()

    def test_continuing_outage_is_not_repeatedly_handled(self):
        with (
            patch.object(
                monitor,
                "check_application",
                return_value=(False, "HTTP 503"),
            ),
            patch.object(monitor, "send_notification") as notify,
            patch.object(
                monitor,
                "restart_container",
                side_effect=RuntimeError("Docker failure"),
            ) as restart,
        ):
            self.assertFalse(monitor.monitor_application(recover=True))
            self.assertFalse(monitor.monitor_application(recover=True))

        notify.assert_called_once()
        restart.assert_called_once()


if __name__ == "__main__":
    unittest.main()
CAPSTONE_7CF2E99C691AEB7D
```
<!-- END_SOURCE:tests/test_monitor.py -->

#### File: `scripts/check.sh`

**Execution location:** Mac Terminal, repository root.

Compiles the monitor, runs unit tests and dependency checks, validates shell syntax and checks whitespace.

<!-- SOURCE:scripts/check.sh -->
```bash
mkdir -p scripts
cat > scripts/check.sh <<'CAPSTONE_42259D31CFD4EA7D'
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

.venv/bin/python -m py_compile monitor-website.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check

bash -n scripts/git-milestone.sh
bash -n scripts/check.sh

if [ -f scripts/server-setup.sh ]; then
    bash -n scripts/server-setup.sh
fi

git diff --check
CAPSTONE_42259D31CFD4EA7D
chmod +x scripts/check.sh
```
<!-- END_SOURCE:scripts/check.sh -->

Validate and integrate the implementation:

```bash
bash scripts/check.sh
bash scripts/git-milestone.sh feature/monitoring-and-recovery \
  "feat: implement website monitoring email alerts and recovery" \
  monitor-website.py tests/test_monitor.py scripts/check.sh
```

Acceptance: compilation, eight mocked unit tests, dependency consistency,
shell syntax and whitespace checks pass. Mock failure messages are expected
in tests deliberately exercising failures; the overall test result must be OK.

The monitor treats exactly HTTP 200 as healthy and does not follow redirects.
A request failure or other status produces an outage. Notification errors are
logged separately so they do not block recovery. Authentication errors and
host-key rejection do not trigger the Linode reboot path. The recovery wait
uses a monotonic deadline, but individual calls and sleeps can extend elapsed
time beyond that deadline. It is not a strict end-to-end timeout guarantee.

### 3.3 Container-host setup

**Mac Terminal:**

```bash
bash <<'BRANCH'
set -euo pipefail
test "$(git branch --show-current)" = develop
test -z "$(git status --porcelain)"
git switch -c feature/container-host
BRANCH
```


#### File: `scripts/server-setup.sh`

**Execution location:** Mac Terminal, repository root.

Checks root and Ubuntu 24.04, installs Docker from Docker’s Ubuntu repository, enables boot services, refuses to replace an existing lab container, and starts Nginx without an automatic restart policy.

<!-- SOURCE:scripts/server-setup.sh -->
```bash
mkdir -p scripts
cat > scripts/server-setup.sh <<'CAPSTONE_E0C3666EA19AA919'
#!/usr/bin/env bash
set -euo pipefail

test "$(id -u)" -eq 0

. /etc/os-release
test "$ID" = "ubuntu"
test "$VERSION_ID" = "24.04"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl

install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

chmod a+r /etc/apt/keyrings/docker.asc

architecture="$(dpkg --print-architecture)"

cat > /etc/apt/sources.list.d/docker.sources <<DOCKER_SOURCE
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $architecture
Signed-By: /etc/apt/keyrings/docker.asc
DOCKER_SOURCE

apt-get update

apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

systemctl enable --now docker
systemctl enable ssh.socket

if docker container inspect capstone-nginx >/dev/null 2>&1; then
    echo "capstone-nginx already exists; inspect it instead of replacing it"
    exit 1
fi

docker pull nginx:stable-alpine

docker run -d \
  --name capstone-nginx \
  --restart=no \
  -p 8080:80 \
  nginx:stable-alpine

docker inspect \
  --format '{{.State.Status}} {{.Config.Image}}' \
  capstone-nginx

curl --fail --silent --show-error http://127.0.0.1:8080/

docker image inspect nginx:stable-alpine \
  --format '{{json .RepoDigests}}'

docker version
CAPSTONE_E0C3666EA19AA919
chmod +x scripts/server-setup.sh
```
<!-- END_SOURCE:scripts/server-setup.sh -->

Validate locally and integrate before provisioning:

```bash
bash scripts/check.sh
bash scripts/git-milestone.sh feature/container-host \
  "feat: add reproducible Docker application host setup" \
  scripts/server-setup.sh
```

### 3.4 Existing-release validation

**Mac Terminal, existing-release route only:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
bash scripts/check.sh
```

Infrastructure is provisioned only after local preparation and validation.

## 10. Provision and bootstrap the application server

**Mac Terminal:** create a dedicated lab key only when these paths are absent.

```bash
export SSH_KEY="$HOME/.ssh/capstone-website-monitor"
export KNOWN_HOSTS="$HOME/.ssh/capstone-website-monitor-known-hosts"
```

```bash
bash <<'KEY'
set -euo pipefail
test ! -e "$SSH_KEY"
test ! -e "$SSH_KEY.pub"
test ! -e "$KNOWN_HOSTS"
ssh-keygen -t ed25519 -f "$SSH_KEY" -C website-monitoring-capstone -N ""
chmod 600 "$SSH_KEY"
cat "$SSH_KEY.pub"
KEY
```

Find the Mac's current public IPv4:

```bash
curl -4 --fail --silent --show-error https://api.ipify.org
```

**Linode Cloud Manager:**

1. Create one Ubuntu 24.04 instance named capstone-website-monitor.
2. Select a suitable small shared CPU plan; inspect the displayed price.
3. Upload only the dedicated public key and set a strong root password for Lish.
4. Do not add backups, volumes or other optional services.
5. Record the instance's numeric ID and IPv4.
6. Create and attach capstone-website-monitor-fw.
7. Allow inbound TCP 22 and 8080 from the Mac's public IPv4 /32 only.
8. Drop other inbound traffic and allow outbound traffic.
9. Confirm Lish console access works.

**Mac Terminal, Bash session:**

```bash
read -r -p "Linode IPv4: " SERVER_IP
read -r -p "Numeric Linode ID: " LINODE_ID
export SERVER_IP LINODE_ID
```

**Server Lish console:**

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

**Mac Terminal:** collect the host key and compare its fingerprint with Lish.

```bash
ssh-keyscan -T 10 -t ed25519 "$SERVER_IP" > "$KNOWN_HOSTS"
ssh-keygen -lf "$KNOWN_HOSTS"
```

Continue only when the fingerprints match independently:

```bash
chmod 600 "$KNOWN_HOSTS"
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'bash -se' < scripts/server-setup.sh
curl --fail --silent --show-error --max-time 10 "http://$SERVER_IP:8080/"
```

The setup installs Docker and creates capstone-nginx on port 8080 with no
automatic restart policy. Inspect the embedded setup script for exact
commands. Open the same URL in a browser. If local server HTTP works but
Mac HTTP fails, check the cloud firewall and the Mac's current public IP.

## 11. Configure credentials and verify the target

**Cloud Manager:** create a short-lived dedicated token with Linodes
Read/Write permission; leave unrelated permissions disabled.
**Google account:** create a dedicated app password where supported.
Use a recipient inbox you control.

**Mac Terminal:** configure values without displaying secrets. Prompts read
/dev/tty because Python's standard input contains the program itself.

```bash
bash <<'CONFIGURE'
set -euo pipefail
: "${SERVER_IP:?Restore and export SERVER_IP}"
: "${SSH_KEY:?Restore and export SSH_KEY}"
: "${KNOWN_HOSTS:?Restore and export KNOWN_HOSTS}"
: "${LINODE_ID:?Restore and export LINODE_ID}"
git check-ignore -q .env
if [ ! -e .env ]; then
  cp .env.example .env
fi
chmod 600 .env
.venv/bin/python - <<'CONFIG'
import os
import sys
from getpass import getpass
from dotenv import set_key

values = {
    "WEBSITE_URL": f"http://{os.environ['SERVER_IP']}:8080/",
    "SSH_HOST": os.environ["SERVER_IP"],
    "SSH_USERNAME": "root",
    "SSH_KEY_PATH": os.environ["SSH_KEY"],
    "SSH_KNOWN_HOSTS": os.environ["KNOWN_HOSTS"],
    "LINODE_ID": os.environ["LINODE_ID"],
    "CONTAINER_NAME": "capstone-nginx",
}
with open("/dev/tty", "r+") as terminal:
    sys.stdin = terminal
    values.update({
        "EMAIL_ADDRESS": input("Sender Gmail address: ").strip(),
        "EMAIL_RECIPIENT": input("Recipient address: ").strip(),
        "EMAIL_PASSWORD": getpass("Google app password: ", stream=terminal).replace(" ", ""),
        "LINODE_TOKEN": getpass("Linode token: ", stream=terminal).strip(),
    })
if any(not value for value in values.values()):
    raise SystemExit("Empty configuration value; nothing saved.")
for name, value in values.items():
    set_key(".env", name, value)
print("Configuration saved without displaying credentials.")
CONFIG
git check-ignore .env
git status --short
CONFIGURE
```

Never commit .env or private keys. If the terminal was restarted, restore
and export infrastructure variables with actual lab values first.

**Mac Terminal:** verify Linode ID/IP and send one deliberate SMTP test:

```bash
.venv/bin/python - <<'VERIFY'
import importlib.util
import os
import linode_api4
from dotenv import load_dotenv

load_dotenv(".env")
client = linode_api4.LinodeClient(os.environ["LINODE_TOKEN"], timeout=20)
server = client.load(linode_api4.Instance, int(os.environ["LINODE_ID"]))
print(server.label, server.ipv4, server.status)
if server.label != "capstone-website-monitor":
    raise SystemExit("STOP: unexpected instance label")
if os.environ["SSH_HOST"] not in server.ipv4:
    raise SystemExit("STOP: Linode ID/IP mismatch")
spec = importlib.util.spec_from_file_location("monitor", "monitor-website.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.send_notification("Deliberate capstone SMTP test")
VERIFY
```

Verify inbox delivery separately. SMTP submission alone does not prove delivery.

## 12. Capture an evidence baseline

**Mac Terminal:** for fresh development, create feature/verified-recovery
from clean develop. For a released checkout, create a new execution branch
from the selected tag. Use unused branch names for subsequent runs.

```bash
bash <<'EVIDENCE'
set -euo pipefail
test -z "$(git status --porcelain)"
git switch -c feature/verified-recovery
test ! -e .private/raw-evidence
mkdir -p .private/raw-evidence
chmod 700 .private .private/raw-evidence
git rev-parse HEAD > .private/raw-evidence/tested-source-commit.txt
date -u +"%Y-%m-%dT%H:%M:%SZ" > .private/raw-evidence/started-at.txt
.venv/bin/python --version > .private/raw-evidence/python-version.txt
bash scripts/check.sh > .private/raw-evidence/local-validation.txt 2>&1
.venv/bin/python monitor-website.py --once > .private/raw-evidence/healthy-check.txt 2>&1
EVIDENCE
```

Do not overwrite existing execution evidence. Stop and select a fresh
run directory if the guard detects previous logs.

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'docker ps; docker image inspect nginx:stable-alpine --format "{{json .RepoDigests}}"; docker version; cat /proc/sys/kernel/random/boot_id' \
  > .private/raw-evidence/server-baseline.txt
```

Capture the actual container image ID/digest if using a different image.

## 13. Verify HTTP 503 detection

**Mac Terminal; commands inside SSH execute on the server:**

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" 'bash -se' <<'REMOTE'
docker exec capstone-nginx cp /etc/nginx/conf.d/default.conf /tmp/capstone-default.conf
docker exec -i capstone-nginx sh -c 'cat > /etc/nginx/conf.d/default.conf' <<'NGINX'
server {
    listen 80;
    location / {
        return 503;
    }
}
NGINX
docker exec capstone-nginx nginx -t
docker exec capstone-nginx nginx -s reload
REMOTE
```

Capture the expected nonzero monitor result without terminating the shell:

```bash
if .venv/bin/python monitor-website.py --once > .private/raw-evidence/http-503.txt 2>&1; then
  echo "Unexpected healthy result; inspect the response and log."
else
  result=$?
  test "$result" -eq 1
fi
cat .private/raw-evidence/http-503.txt
```

Acceptance: log shows HTTP 503, notification arrives, no recovery occurs.
An exit code of 1 alone is insufficient: inspect the log for configuration errors.
Restore immediately, including when the test did not behave as expected:

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'docker exec capstone-nginx cp /tmp/capstone-default.conf /etc/nginx/conf.d/default.conf && docker exec capstone-nginx nginx -t && docker exec capstone-nginx nginx -s reload'
curl --fail --silent --show-error --max-time 10 "http://$SERVER_IP:8080/" > /dev/null
```

## 14. Verify container recovery without a reboot

**Mac Terminal:** capture boot IDs to establish that container recovery did
not require a server reboot.

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'cat /proc/sys/kernel/random/boot_id' > .private/raw-evidence/container-boot-before.txt
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" 'docker stop capstone-nginx'
.venv/bin/python monitor-website.py --once --recover > .private/raw-evidence/container-recovery.txt 2>&1
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'cat /proc/sys/kernel/random/boot_id' > .private/raw-evidence/container-boot-after.txt
cmp .private/raw-evidence/container-boot-before.txt .private/raw-evidence/container-boot-after.txt
curl --fail --silent --show-error --max-time 10 "http://$SERVER_IP:8080/" > /dev/null
cat .private/raw-evidence/container-recovery.txt
```

Acceptance: delivered email, successful Docker restart, restored HTTP 200,
unchanged boot ID and no API reboot request in the recovery log.

## 15. Verify automatic server recovery

Use only the dedicated lab instance. Verify ID/IP, Lish access and SMTP
first. Ensure no other recovery-enabled monitor is running. This deliberately
stops the container and SSH, then lets Python request the reboot.

**Mac Terminal:**

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'cat /proc/sys/kernel/random/boot_id' > .private/raw-evidence/boot-id-before.txt
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" 'bash -se' <<'REMOTE'
systemctl enable ssh.socket
systemctl enable docker
docker stop capstone-nginx
systemd-run --unit=capstone-stop-ssh --on-active=5s /usr/bin/systemctl stop ssh.service ssh.socket
REMOTE
sleep 8
.venv/bin/python monitor-website.py --once --recover > .private/raw-evidence/server-recovery.txt 2>&1
cat .private/raw-evidence/server-recovery.txt
```

The transient timer stops SSH at runtime; boot activation remains enabled.
After the monitor reports success:

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'cat /proc/sys/kernel/random/boot_id' > .private/raw-evidence/boot-id-after.txt
```

```bash
bash <<'BOOT_CHECK'
set -euo pipefail
test -s .private/raw-evidence/boot-id-before.txt
test -s .private/raw-evidence/boot-id-after.txt
if cmp -s .private/raw-evidence/boot-id-before.txt .private/raw-evidence/boot-id-after.txt; then
  echo "FAIL: boot ID did not change"
  exit 1
fi
curl --fail --silent --show-error --max-time 10 "http://$SERVER_IP:8080/" > /dev/null
echo "Changed boot ID and healthy HTTP response verified."
BOOT_CHECK
```

Acceptance: outage email, API reboot request, changed nonempty boot ID,
restored SSH, Python container restart and HTTP 200. A reboot-request log
alone does not prove recovery. Investigate failed recovery in Lish rather
than repeatedly restarting the monitor and resetting outage protection.

## 16. Verify scheduled execution

**Mac Terminal:**

```bash
CHECK_INTERVAL_SECONDS=30 .venv/bin/python monitor-website.py --recover \
  2>&1 | tee .private/raw-evidence/scheduled-monitor.txt
```

Observe the immediate check and at least two scheduled checks, then press
Ctrl+C. Default operation uses the configured five-minute interval:

```bash
.venv/bin/python monitor-website.py --recover
```

The Mac must remain awake and connected. Persistent monitor hosting is
outside this capstone's scope.

## 17. Troubleshooting and recovery

| Symptom | Action |
| --- | --- |
| HTTP fails only from Mac | Check current public IPv4, firewall source /32 and port 8080. |
| SSH authentication fails | Check username, private key and authorized_keys; authentication failure should not reboot the server. |
| Host-key mismatch | Verify the fingerprint independently through Lish; do not disable host-key checking. |
| SMTP fails | Check app password, sender/recipient and network access. Verify the inbox separately. |
| API authorization fails | Check token expiry and Linodes Read/Write permission. |
| Unhealthy HTTP after restart | Inspect Docker/Nginx logs; restart does not repair incorrect configuration. |
| API reboot error | Inspect Cloud Manager events and instance state. |
| Recovery timeout | Use Lish and inspect services rather than blindly rerunning recovery. |
| Local connection fails | Restore connectivity before enabling recovery. |
| EOFError during credential prompts | Use the /dev/tty credential block from section 5. |
| Zsh closes with exit code 1 | Use child Bash blocks for strict checks; inspect the failing command. |
| Wrong branch or uncommitted files | Inspect status/log; finish the current milestone without discarding work. |

An unresolved outage is handled once per monitor process. Cooldown and
outage state live in memory; restarting resets them.

**Server Lish console:**

```bash
systemctl start ssh.socket
systemctl start ssh.service
systemctl status docker --no-pager
docker ps -a
docker logs --tail 100 capstone-nginx
docker start capstone-nginx
```

## 18. Preserve, sanitize and commit execution evidence

**Mac Terminal:** capture final server logs before deletion.

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'docker ps -a; docker logs --tail 100 capstone-nginx; systemctl is-enabled docker; systemctl is-enabled ssh.socket' \
  > .private/raw-evidence/final-server-checks.txt
```

Capture screenshots of the Nginx page, received outage email, recovery logs
and Linode reboot event. Hide personal information and secrets.
Keep raw logs in ignored .private/raw-evidence. Sanitize before deleting .env:

```bash
.venv/bin/python - <<'SANITIZE'
from pathlib import Path
from dotenv import dotenv_values

if not Path(".env").is_file():
    raise SystemExit("STOP: .env is missing; use an explicitly reviewed redaction method.")
config = dotenv_values(".env")
destination = Path("docs/evidence")
destination.mkdir(parents=True, exist_ok=True)
names = (
    "LINODE_TOKEN", "EMAIL_PASSWORD", "EMAIL_ADDRESS", "EMAIL_RECIPIENT",
    "SSH_HOST", "SSH_KEY_PATH", "SSH_KNOWN_HOSTS", "LINODE_ID", "WEBSITE_URL",
)
pairs = sorted(
    ((config[name], f"<{name}>") for name in names if config.get(name)),
    key=lambda item: len(item[0]), reverse=True,
)
for source in Path(".private/raw-evidence").glob("*.txt"):
    content = source.read_text(errors="replace")
    for value, replacement in pairs:
        content = content.replace(value, replacement)
    (destination / source.name).write_text(content)
print("Sanitized copies created; manually review every file and screenshot.")
SANITIZE
```

This is value replacement, not a complete secret scanner. Inspect email
headers, account details, screenshots and unrelated terminal content.

Write docs/evidence/RESULTS.md using the completed-run record in the final
documentation section as a structure,
replacing the completed run's claims with your actual new execution results.
Record timestamp, tested revision, Python/dependency versions, image digest,
healthy/503 behavior, SMTP/inbox, both recovery experiments, boot IDs,
scheduling, limitations and relative evidence links. Do not manufacture a
cloud-tested revision from an implementation commit or write current time
as the historical test timestamp. Jenkins build number is not applicable.

After review, fresh-development route:

```bash
bash scripts/git-milestone.sh feature/verified-recovery \
  "test: record verified website monitoring and recovery evidence" docs/evidence
```

Use an accurate message if a requirement failed or was incomplete. Existing
release reproductions should commit new evidence on their execution branch
and follow their own integration policy, without rewriting the prior release.

## 19. Resource and credential cleanup

**Mac Terminal:** stop the monitor with Ctrl+C and inspect remaining processes.
Stop only identified capstone monitor PIDs; do not kill unrelated Python work.

```bash
pgrep -fl 'monitor-website.py' || true
```

While the server remains reachable:

```bash
ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" "root@$SERVER_IP" \
  'docker rm -f capstone-nginx; docker ps -a' > .private/raw-evidence/container-cleanup.txt
```

Sanitize this new cleanup log with section 12's command while .env still
exists, and manually inspect the public copy. Removing a container does not
stop instance billing.

**Cloud Manager:**

1. Verify the dedicated instance label, ID and IP.
2. Delete the instance; do not merely power it off.
3. Confirm it is absent from the instance list.
4. Delete its dedicated firewall and remove the dedicated uploaded public key.
5. Check for project-associated volumes, backups, images, NodeBalancers,
   storage, reserved addresses and other paid add-ons.
6. Leave unrelated resources alone.
7. Capture and review sanitized deletion/resource-list evidence.
8. Revoke the dedicated Linode API token.

**Google account settings:** revoke the dedicated app password.

**Mac Terminal:** remove only the named lab files. Normal GitHub/GitLab keys
are outside this command's scope. These explicit paths also work after a
terminal restart, without relying on unset infrastructure variables.

```bash
rm -f -- "$HOME/.ssh/capstone-website-monitor" \
  "$HOME/.ssh/capstone-website-monitor.pub" \
  "$HOME/.ssh/capstone-website-monitor-known-hosts"
rm -f -- .env
```

Create docs/evidence/CLEANUP.md using the final documentation section and actual
new-run outcomes. Update RESULTS.md with cleanup status. Declare completion
only after project-associated paid resources are gone. Previously accrued
charges may remain. Retain .venv for final local checks and generation.

## 20. Final documentation and source snapshots

**Mac Terminal, fresh-development route:** enter the documentation branch
without discarding cleanup/evidence edits already made on develop.

```bash
bash <<'DOC_BRANCH'
set -euo pipefail
case "$(git branch --show-current)" in
  docs/final-runbook) ;;
  develop)
    if git show-ref --verify --quiet refs/heads/docs/final-runbook; then
      git switch docs/final-runbook
    else
      git switch -c docs/final-runbook
    fi
    ;;
  *) echo "STOP: finish the current milestone before final documentation"; exit 1 ;;
esac
DOC_BRANCH
```

The following full documentation contents describe this completed project,
using the operator's explicit confirmation for live outcomes and cleanup.
For a fresh reproduction, replace the outcomes with that run's actual results;
retain original execution records instead of inventing timestamps or digests.


#### File: `docs/evidence/RESULTS.md`

**Execution location:** Mac Terminal, repository root.

Completed-project documentation. Review against execution evidence before submission.

<!-- SOURCE:docs/evidence/RESULTS.md -->
```bash
mkdir -p docs/evidence
cat > docs/evidence/RESULTS.md <<'CAPSTONE_522DA872675E0240'
# Verification results

## Outcome

The operator confirms completion of live website monitoring and recovery.
Local validation is supported by the terminal output shared during development.

## Local validation

- Validation session date: 2026-10-24.
- Python: 3.12 family.
- Implementation commit: d358bfe.
- Implementation integration commit: f592d18.
- Python compilation: Passed.
- Eight mocked unit tests: Passed.
- Dependency consistency: Passed; no broken requirements found.
- Shell syntax and Git whitespace checks: Passed.
- Implementation branch and develop pushes to GitHub/GitLab: Passed.
- Dependencies: [requirements.lock](../../requirements.lock).

## Live execution — operator-confirmed

- Healthy HTTP 200 and deliberate HTTP 503 detection: Passed.
- SMTP submission and recipient inbox delivery: Passed.
- Container restart through SSH without server reboot: Passed.
- Linode API reboot when SSH was unavailable: Passed.
- Changed boot ID, restored SSH and Python container restart: Passed.
- Post-recovery HTTP 200: Passed.
- Immediate check and at least two scheduled checks: Passed.

The implementation commits above identify development milestones. Exact
cloud-tested revision, UTC timestamp and image digest must be read from the
original execution records; no values are inferred here.

## Cleanup

The operator confirms completed dedicated-resource and credential cleanup,
with no project-associated paid resources remaining.
See [cleanup record](CLEANUP.md).

## Evidence basis

Local results are supported by shared terminal output. Live outcomes are
operator-confirmed; supporting logs/screenshots must remain with the submission.
Mocked tests do not independently prove cloud execution or inbox delivery.
Jenkins build number: Not applicable.
CAPSTONE_522DA872675E0240
```
<!-- END_SOURCE:docs/evidence/RESULTS.md -->

#### File: `docs/evidence/CLEANUP.md`

**Execution location:** Mac Terminal, repository root.

Completed-project documentation. Review against execution evidence before submission.

<!-- SOURCE:docs/evidence/CLEANUP.md -->
```bash
mkdir -p docs/evidence
cat > docs/evidence/CLEANUP.md <<'CAPSTONE_EF67619A425A0425'
# Cleanup record

## Outcome

The project operator confirms that all dedicated lab cleanup actions are
complete and no project-associated paid resources remain.

- Monitor stopped: Completed.
- Dedicated Docker container removed: Completed.
- Dedicated Linode deleted: Completed.
- Dedicated firewall deleted: Completed.
- Uploaded lab SSH public key removed: Completed.
- Dedicated Linode token revoked: Completed.
- Dedicated Google app password revoked: Completed.
- Local .env removed: Completed.
- Dedicated private/public keys and known-hosts file removed: Completed.
- Extra project-associated paid resources checked: Completed.
- Remaining project-associated paid resources: None.

The virtual environment may be retained until final checks and documentation
are finished. Keep supporting sanitized cleanup records with the submission.
Previously accrued usage may still appear on a later bill.
CAPSTONE_EF67619A425A0425
```
<!-- END_SOURCE:docs/evidence/CLEANUP.md -->

#### File: `README.md`

**Execution location:** Mac Terminal, repository root.

Completed-project documentation. Review against execution evidence before submission.

<!-- SOURCE:README.md -->
```bash
cat > README.md <<'CAPSTONE_9E7BCFFEB9A46BEB'
# Website Monitoring and Recovery

A Python automation capstone based on Nana Janashia / TechWorld with Nana
Module 14. An external Mac monitor checks Nginx on an Ubuntu 24.04 Linode,
sends SMTP notifications, restarts Docker through SSH and uses the Linode
API for server recovery when SSH cannot connect.

## Components

Requests, Paramiko, linode-api4, schedule, python-dotenv, SMTP STARTTLS,
Docker, Nginx, verified SSH host keys and environment-based configuration.

## Verification

Eight mocked tests and local validation passed. The operator confirms live
HTTP checks, inbox delivery, container recovery, API reboot recovery,
changed boot ID, restored HTTP 200 and scheduled checks.
See [verification results](docs/evidence/RESULTS.md).

## Cleanup

The operator confirms completed dedicated-resource/credential cleanup and
no remaining project-associated paid resources.
See [cleanup record](docs/evidence/CLEANUP.md).

## Reproduction

[Complete implementation runbook](docs/RUNBOOK.md) includes full source,
setup, deployment, verification, troubleshooting, cleanup and Git milestones.

## Limitations

The Mac must remain awake and connected. Recovery state is held in memory.
Network failure can resemble server failure. HTTP 200 is a basic availability
check. Root SSH is limited to this disposable lab design.

## Attribution

Original reference:
https://gitlab.com/twn-devops-bootcamp/latest/14-automation-with-python/automation-projects

Reference commit: fb3d2f537cb599e734ba6c24683b179bb8ae3840.
Original upstream authorship/history are preserved.
See [source provenance](docs/SOURCE_PROVENANCE.md).
CAPSTONE_9E7BCFFEB9A46BEB
```
<!-- END_SOURCE:README.md -->

#### File: `docs/SOURCE_PROVENANCE.md`

**Execution location:** Mac Terminal, repository root.

Completed-project documentation. Review against execution evidence before submission.

<!-- SOURCE:docs/SOURCE_PROVENANCE.md -->
```bash
mkdir -p docs
cat > docs/SOURCE_PROVENANCE.md <<'CAPSTONE_643125FE690529EF'
# Source provenance

## Reference

Nana Janashia / TechWorld with Nana, Module 14 — Automation with Python.
Project: Website Monitoring and Recovery.
https://gitlab.com/twn-devops-bootcamp/latest/14-automation-with-python/automation-projects

Baseline: fb3d2f537cb599e734ba6c24683b179bb8ae3840.
Earlier preserved commit: 4bac3655ff774fd3c66876c641cb5fad7ad5ab08.
Relevant original file: monitor-website.py.

The seven unrelated lesson scripts were removed from the working tree;
their original contents and author history remain in Git.

## Retained method and adaptations

Retains Requests, SMTP, Paramiko, Linode SDK, schedule and Nana's
send_notification, restart_container, restart_server_and_container and
monitor_application structure.

Adds environment configuration, a named container, verified host keys,
explicit call timeouts, separate notification/recovery error handling,
SSH before reboot, Docker restart, HTTP recovery checks, recovery waiting,
outage suppression, cooldown and mocked unit tests.

## Development milestones

- Foundation: 165447f; integration: 7f0b3bc.
- Monitoring implementation: d358bfe; integration: f592d18.
- Container-host implementation: 6cce9b6.

The runbook source snapshot was taken from GitHub develop at
0869fcd7e86ade03b8775a73c2fea57d3373e644. This is not asserted to be the
precise cloud-tested revision.

## Current status

Local validation and eight mocked tests passed. The operator confirms live
monitoring, notifications, both recovery paths, scheduling and cleanup.
See [results](evidence/RESULTS.md) and [cleanup](evidence/CLEANUP.md).

## Attribution

Original upstream history/authorship are preserved. Adaptations are recorded
in subsequent commits. No new licence over upstream material is asserted.
CAPSTONE_643125FE690529EF
```
<!-- END_SOURCE:docs/SOURCE_PROVENANCE.md -->

Create docs/RELEASE_NOTES.md if not yet present:

```bash
cat > docs/RELEASE_NOTES.md <<'NOTES'
# Release notes

## Implementation

Scheduled HTTP checks, SMTP outage notifications, SSH Docker recovery,
Linode API reboot recovery, verified SSH host keys, explicit timeouts,
post-recovery checks and in-memory outage suppression/cooldown.

## Validation and cleanup

See [verification results](evidence/RESULTS.md) and
[cleanup record](evidence/CLEANUP.md) for actual outcomes.

## Limitations

The monitor requires an awake, connected Mac. Network failure can resemble
server failure. Recovery state resets on process restart. No Jenkins,
AWS, EKS or snapshot automation is included.

## Attribution

Based on Nana Janashia / TechWorld with Nana Module 14.
See [source provenance](SOURCE_PROVENANCE.md).
NOTES
```

This runbook already contains every implementation file in full at its creation
step. Save it as docs/RUNBOOK.md. After editing source or the final documents,
update the corresponding full-file block and verify it matches before committing.
Do not embed private credentials.


### Verify embedded files match the checkout

**Mac Terminal, repository root:** this only compares source; it does not execute
embedded commands. If your local source or final documents have changed,
update the corresponding runbook block before committing.

```bash
.venv/bin/python - <<'VERIFY_SNAPSHOTS'
from pathlib import Path
import re

text = Path("docs/RUNBOOK.md").read_text()
sections = re.findall(r"<!-- SOURCE:(.*?) -->\n(.*?)<!-- END_SOURCE:\1 -->", text, re.S)
if len(sections) != 13:
    raise SystemExit(f"Expected 13 full-file snapshots; found {len(sections)}")
seen = set()
for name, section in sections:
    if name in seen:
        raise SystemExit("Duplicate: " + name)
    seen.add(name)
    match = re.search(r"<<'(CAPSTONE_[A-F0-9]+)'\n", section)
    if not match:
        raise SystemExit("Missing delimiter: " + name)
    content = section[match.end():].split(match.group(1) + "\n", 1)[0]
    if content.encode() != Path(name).read_bytes():
        raise SystemExit("Source mismatch: " + name)
    print("MATCH", name)
print("All 13 source/document snapshots match.")
VERIFY_SNAPSHOTS
```

## 21. Audit, integrate and release

**Mac Terminal:**

```bash
bash scripts/check.sh
git diff --check
git status --short
git diff --stat
git ls-files
```

Review README, provenance, results, cleanup, evidence links and full source
snapshots together. Confirm private keys, .env and raw evidence are not
tracked. Check staged and unstaged changes; automated scans alone are not
proof of secret-free history. Revoke any accidentally committed credential.

Search for unfinished record entries:

```bash
rg -n 'NOT RECORDED|TODO|TBD' README.md docs/SOURCE_PROVENANCE.md \
  docs/RELEASE_NOTES.md docs/evidence/RESULTS.md docs/evidence/CLEANUP.md
```

No matches is the desired outcome; rg returns 1 for no matches. Accurately
record a failed requirement rather than changing it to Passed for release.

Integrate final documentation in the fresh-development route:

```bash
bash scripts/git-milestone.sh docs/final-runbook \
  "docs: finalize runbook provenance and release notes" README.md docs
```

Release only after all required verification, evidence and cleanup are
complete and reviewed. This block checks both destination main branches
are already contained in develop, preventing publication over divergent
remote history. Resolve any rejection deliberately; never force-push.

```bash
bash <<'RELEASE'
set -euo pipefail
test "$(git branch --show-current)" = develop
test -z "$(git status --porcelain)"
git fetch origin --tags
git fetch gitlab --tags
git merge-base --is-ancestor origin/main develop
git merge-base --is-ancestor gitlab/main develop
git switch main
git pull --ff-only origin main
git merge --no-ff develop -m "merge: release website monitoring and recovery"
git push origin main
git push gitlab main
git switch develop
git merge --ff-only main
git push origin develop
git push gitlab develop
git diff --exit-code main develop
RELEASE
```

Create a new annotated tag. Change v1.0.0 to an unused version if necessary.
Both remote tag namespaces were fetched above; never replace an existing tag.

```bash
bash <<'TAG_RELEASE'
set -euo pipefail
RELEASE_TAG=v1.0.0
test -z "$(git tag --list "$RELEASE_TAG")"
git tag -a "$RELEASE_TAG" main -m "Website monitoring and recovery capstone release"
git push origin "$RELEASE_TAG"
git push gitlab "$RELEASE_TAG"
git ls-remote --heads origin main develop
git ls-remote --heads gitlab main develop
git ls-remote --tags origin "$RELEASE_TAG" "$RELEASE_TAG^{}"
git ls-remote --tags gitlab "$RELEASE_TAG" "$RELEASE_TAG^{}"
git status --short --branch
git log --graph --oneline --decorate -15
TAG_RELEASE
```

Acceptance: both main/develop branches on both remotes point to the same
released commit; annotated tag objects and peeled targets match; working
tree is clean. If a push partly succeeds, inspect remote state and finish
the missing operation rather than recreating the tag.

## 22. Final local cleanup and completion criteria

After final checks, matching source snapshots and preservation of reviewed
public evidence, remove only reproducible/private temporary material from
the repository root:

```bash
bash <<'LOCAL_CLEANUP'
set -euo pipefail
test "$(pwd -P)" = "$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
test -s docs/RUNBOOK.md
test -z "$(git status --porcelain)"
rm -rf -- .venv .private
LOCAL_CLEANUP
unset SERVER_IP LINODE_ID SSH_KEY KNOWN_HOSTS
```

- Local tests and live verification are recorded separately.
- SMTP submission and inbox delivery are separately established.
- HTTP 200 and deliberate HTTP 503 behavior are verified.
- Container recovery did not reboot the server.
- Server recovery has changed-boot-ID and restored-HTTP evidence.
- Scheduled checks were observed.
- Execution records identify the tested revision and image digest.
- Evidence is manually sanitized and preserved.
- Dedicated resources are deleted and credentials revoked.
- README, provenance, results and cleanup agree.
- Full-file snapshots match repository bytes and can recreate each file.
- Git workflow remains feature/docs → develop → main, preserving upstream.
- Both remotes contain matching release branches and an unused annotated tag.


## 23. Source snapshot manifest

SHA256 values identify the nine implementation files fetched for this document.

| File | SHA256 |
| --- | --- |
| `requirements.lock` | `582b0bfaca1c54670c22cdc32ba96c956360a9c7e0ffae56b69423f4d1a3ef67` |
| `.env.example` | `2c4754a1f5bff00c364d5ab635c155ebf38024bdb04b42fd13aab5b4fbd76437` |
| `.gitignore` | `28557eb7a320a3c83b5590f3a6e92dc62ba6b2580b378305a867439ddea5e3fa` |
| `requirements.in` | `7f7341ff1de4bbef5d73009887a4e677cbfdf665c4d4d033ad70884e6056b3f1` |
| `monitor-website.py` | `93859df6dce439ca8948157eb54883ec26ddc0c8e9807d7a50d472229647c941` |
| `tests/test_monitor.py` | `7cf2e99c691aeb7d5b85448ff59cb913f7ef224914507eec1f412b51b8b218da` |
| `scripts/check.sh` | `42259d31cfd4ea7d6ba6c24cbcbbfa64e3d6b09a227864a9e0bb959874dd0ecc` |
| `scripts/git-milestone.sh` | `4d3ae26dd389870af3f8725478da06b25063a71019b7305942aa1de7e247bb04` |
| `scripts/server-setup.sh` | `e0c3666ea19aa919bfe9a7b41bf096339607ed9bdf311918dea52b2403d86d51` |
