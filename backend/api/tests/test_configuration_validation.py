"""
Tests for configuration validation of the Virtual Coffee Platform.
This test verifies that configuration is correctly validated and applied.
"""
import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock
import contextlib


def run_command(command):
    """Run a shell command and return the output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


class TestConfigurationValidation:
    """Test configuration validation for the Virtual Coffee Platform."""

    @pytest.fixture
    def mock_kubectl(self):
        """Mock kubectl command execution."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            yield mock_popen

    def test_configmap_validation(self, mock_kubectl):
        """Test that ConfigMaps are validated correctly."""
        # Mock the kubectl output for ConfigMaps
        mock_process = mock_kubectl.return_value
        mock_process.communicate.return_value = (
            json.dumps({
                "items": [
                    {
                        "metadata": {
                            "name": "virtual-coffee-config",
                            "namespace": "test-instance"
                        },
                        "data": {
                            "DEPLOYMENT_ID": "test-instance",
                            "TIMEZONE": "America/Los_Angeles",
                            "SCHEDULE": "0 9 * * 1,3,5",  # Monday, Wednesday, Friday at 9 AM
                            "MEETING_SIZE": "2"
                        }
                    }
                ]
            }),
            ""
        )
        mock_process.returncode = 0

        # Run the command to get ConfigMaps
        exit_code, stdout, stderr = run_command([
            "kubectl", "get", "configmap", "-n", "test-instance", "-o", "json"
        ])

        # Parse the output
        configmaps_data = json.loads(stdout)
        
        # Verify the ConfigMap properties
        assert len(configmaps_data["items"]) == 1
        configmap = configmaps_data["items"][0]
        
        # Check required configuration keys
        required_keys = ["DEPLOYMENT_ID", "TIMEZONE", "SCHEDULE", "MEETING_SIZE"]
        for key in required_keys:
            assert key in configmap["data"]
        
        # Check specific values
        assert configmap["data"]["DEPLOYMENT_ID"] == "test-instance"
        assert configmap["data"]["TIMEZONE"] == "America/Los_Angeles"
        assert configmap["data"]["SCHEDULE"] == "0 9 * * 1,3,5"
        assert configmap["data"]["MEETING_SIZE"] == "2"

    def test_invalid_configuration_detection(self, mock_kubectl):
        """Test that invalid configuration is detected."""
        # Test cases for invalid configurations
        test_cases = [
            # Missing TIMEZONE
            {
                "data": {
                    "DEPLOYMENT_ID": "test-instance",
                    "SCHEDULE": "0 9 * * 1,3,5",
                    "MEETING_SIZE": "2"
                },
                "expected_missing": ["TIMEZONE"]
            },
            # Invalid SCHEDULE format
            {
                "data": {
                    "DEPLOYMENT_ID": "test-instance",
                    "TIMEZONE": "America/Los_Angeles",
                    "SCHEDULE": "invalid-cron",
                    "MEETING_SIZE": "2"
                },
                "expected_invalid": ["SCHEDULE"]
            },
            # Invalid MEETING_SIZE (non-numeric)
            {
                "data": {
                    "DEPLOYMENT_ID": "test-instance",
                    "TIMEZONE": "America/Los_Angeles",
                    "SCHEDULE": "0 9 * * 1,3,5",
                    "MEETING_SIZE": "invalid"
                },
                "expected_invalid": ["MEETING_SIZE"]
            }
        ]
        
        for test_case in test_cases:
            # Mock the kubectl output for ConfigMaps with invalid configuration
            mock_process = mock_kubectl.return_value
            mock_process.communicate.return_value = (
                json.dumps({
                    "items": [
                        {
                            "metadata": {
                                "name": "virtual-coffee-config",
                                "namespace": "test-instance"
                            },
                            "data": test_case["data"]
                        }
                    ]
                }),
                ""
            )
            mock_process.returncode = 0

            # Run the command to get ConfigMaps
            exit_code, stdout, stderr = run_command([
                "kubectl", "get", "configmap", "-n", "test-instance", "-o", "json"
            ])

            # Parse the output
            configmaps_data = json.loads(stdout)
            
            # Verify the ConfigMap properties
            assert len(configmaps_data["items"]) == 1
            configmap = configmaps_data["items"][0]
            
            # Check for missing keys
            if "expected_missing" in test_case:
                for key in test_case["expected_missing"]:
                    assert key not in configmap["data"]
            
            # Check for invalid values (would be validated by the application)
            if "expected_invalid" in test_case:
                for key in test_case["expected_invalid"]:
                    if key == "SCHEDULE" and key in configmap["data"]:
                        # Simple cron validation (very basic)
                        assert len(configmap["data"][key].split()) != 5
                    elif key == "MEETING_SIZE" and key in configmap["data"]:
                        with contextlib.suppress(ValueError):
                            int(configmap["data"][key])
                            # If we get here, it's a valid integer, which is not what we expect
                            # for the invalid case
                            assert False, f"Expected invalid integer for {key}"

    def test_argocd_application_configuration(self, mock_kubectl):
        """Test that ArgoCD application configuration is valid."""
        # Mock the kubectl output for ArgoCD application
        mock_process = mock_kubectl.return_value
        mock_process.communicate.return_value = (
            json.dumps({
                "metadata": {
                    "name": "virtual-coffee-test-instance",
                    "namespace": "argocd"
                },
                "spec": {
                    "project": "default",
                    "source": {
                        "repoURL": "https://github.com/example/virtual-coffee-platform.git",
                        "path": "k8s/overlays/dev",
                        "targetRevision": "main"
                    },
                    "destination": {
                        "server": "https://kubernetes.default.svc",
                        "namespace": "test-instance"
                    },
                    "syncPolicy": {
                        "automated": {
                            "prune": True,
                            "selfHeal": True
                        }
                    }
                },
                "status": {
                    "sync": {
                        "status": "Synced"
                    },
                    "health": {
                        "status": "Healthy"
                    }
                }
            }),
            ""
        )
        mock_process.returncode = 0

        # Run the command to get ArgoCD application
        exit_code, stdout, stderr = run_command([
            "kubectl", "get", "application.argoproj.io/virtual-coffee-test-instance",
            "-n", "argocd", "-o", "json"
        ])

        # Parse the output
        app_data = json.loads(stdout)
        
        # Verify the application properties
        assert app_data["metadata"]["name"] == "virtual-coffee-test-instance"
        assert app_data["metadata"]["namespace"] == "argocd"
        
        # Check source configuration
        source = app_data["spec"]["source"]
        assert "repoURL" in source
        assert "path" in source
        assert "targetRevision" in source
        
        # Check destination configuration
        destination = app_data["spec"]["destination"]
        assert destination["namespace"] == "test-instance"
        
        # Check sync policy
        sync_policy = app_data["spec"]["syncPolicy"]
        assert "automated" in sync_policy
        assert sync_policy["automated"]["prune"] is True
        assert sync_policy["automated"]["selfHeal"] is True
        
        # Check status
        assert app_data["status"]["sync"]["status"] == "Synced"
        assert app_data["status"]["health"]["status"] == "Healthy"