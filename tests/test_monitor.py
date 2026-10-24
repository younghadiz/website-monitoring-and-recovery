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
