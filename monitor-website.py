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
