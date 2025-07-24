"""
Tests for AWS resource provisioning through Crossplane.
This test verifies that AWS resources are correctly provisioned and configured.
"""
import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest


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


class TestAWSResourceProvisioning:
    """Test AWS resource provisioning through Crossplane."""

    @pytest.fixture()
    def mock_kubectl(self):
        """Mock kubectl command execution."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            yield mock_popen

    def test_dynamodb_table_creation(self, mock_kubectl):
        """Test that DynamoDB tables are created correctly."""
        # Mock the kubectl output for a DynamoDB table
        mock_process = mock_kubectl.return_value
        mock_process.communicate.return_value = (
            json.dumps(
                {
                    "items": [
                        {
                            "metadata": {
                                "name": "test-instance-users",
                                "namespace": "crossplane-system",
                            },
                            "spec": {
                                "forProvider": {
                                    "region": "us-west-2",
                                    "provisionedThroughput": {
                                        "readCapacityUnits": 5,
                                        "writeCapacityUnits": 5,
                                    },
                                    "keySchema": [
                                        {
                                            "attributeName": "id",
                                            "keyType": "HASH",
                                        },
                                    ],
                                    "tags": [
                                        {
                                            "key": "Name",
                                            "value": "virtualcoffee-users",
                                        },
                                    ],
                                },
                            },
                            "status": {
                                "conditions": [
                                    {
                                        "type": "Ready",
                                        "status": "True",
                                    },
                                ],
                                "atProvider": {
                                    "tableArn": "arn:aws:dynamodb:us-west-2:123456789012:table/test-instance-users",
                                },
                            },
                        },
                    ],
                }
            ),
            "",
        )
        mock_process.returncode = 0

        # Run the command to get DynamoDB tables
        exit_code, stdout, stderr = run_command(
            [
                "kubectl",
                "get",
                "table.dynamodb.aws.crossplane.io",
                "-o",
                "json",
            ]
        )

        # Parse the output
        tables_data = json.loads(stdout)

        # Verify the table properties
        assert len(tables_data["items"]) == 1
        table = tables_data["items"][0]

        # Check table name
        assert "test-instance" in table["metadata"]["name"]

        # Check provisioned throughput
        throughput = table["spec"]["forProvider"]["provisionedThroughput"]
        read_capacity = 5
        write_capacity = 5
        assert throughput["readCapacityUnits"] == read_capacity
        assert throughput["writeCapacityUnits"] == write_capacity

        # Check key schema
        key_schema = table["spec"]["forProvider"]["keySchema"]
        assert len(key_schema) == 1
        assert key_schema[0]["attributeName"] == "id"
        assert key_schema[0]["keyType"] == "HASH"

        # Check tags
        tags = table["spec"]["forProvider"]["tags"]
        assert any(tag["key"] == "Name" for tag in tags)

        # Check status
        conditions = table["status"]["conditions"]
        ready_condition = next((c for c in conditions if c["type"] == "Ready"), None)
        assert ready_condition is not None
        assert ready_condition["status"] == "True"

        # Check ARN
        assert "tableArn" in table["status"]["atProvider"]
        assert table["status"]["atProvider"]["tableArn"].startswith("arn:aws:dynamodb")

    def test_dynamodb_claim_creation(self, mock_kubectl):
        """Test that DynamoDB claims are created correctly."""
        # Mock the kubectl output for a DynamoDB claim
        mock_process = mock_kubectl.return_value
        mock_process.communicate.return_value = (
            json.dumps(
                {
                    "metadata": {
                        "name": "test-instance-dynamodb",
                        "namespace": "test-instance",
                    },
                    "spec": {
                        "parameters": {
                            "region": "us-west-2",
                            "readCapacity": 5,
                            "writeCapacity": 5,
                        },
                        "compositionRef": {
                            "name": "virtualcoffee-dynamodb",
                        },
                    },
                    "status": {
                        "conditions": [
                            {
                                "type": "Ready",
                                "status": "True",
                                "reason": "Available",
                                "message": "Resource is available",
                            },
                        ],
                        "resourceRefs": [
                            {
                                "apiVersion": "dynamodb.aws.crossplane.io/v1alpha1",
                                "kind": "Table",
                                "name": "test-instance-users",
                            },
                            {
                                "apiVersion": "dynamodb.aws.crossplane.io/v1alpha1",
                                "kind": "Table",
                                "name": "test-instance-matches",
                            },
                            {
                                "apiVersion": "dynamodb.aws.crossplane.io/v1alpha1",
                                "kind": "Table",
                                "name": "test-instance-config",
                            },
                        ],
                    },
                }
            ),
            "",
        )
        mock_process.returncode = 0

        # Run the command to get DynamoDB claim
        exit_code, stdout, stderr = run_command(
            [
                "kubectl",
                "get",
                "virtualcoffeedynamodbclaim.virtualcoffee.io/test-instance-dynamodb",
                "-n",
                "test-instance",
                "-o",
                "json",
            ]
        )

        # Parse the output
        claim_data = json.loads(stdout)

        # Verify the claim properties
        assert claim_data["metadata"]["name"] == "test-instance-dynamodb"
        assert claim_data["metadata"]["namespace"] == "test-instance"

        # Check parameters
        params = claim_data["spec"]["parameters"]
        read_capacity = 5
        write_capacity = 5
        assert params["region"] == "us-west-2"
        assert params["readCapacity"] == read_capacity
        assert params["writeCapacity"] == write_capacity

        # Check composition reference
        assert claim_data["spec"]["compositionRef"]["name"] == "virtualcoffee-dynamodb"

        # Check status
        conditions = claim_data["status"]["conditions"]
        ready_condition = next((c for c in conditions if c["type"] == "Ready"), None)
        assert ready_condition is not None
        assert ready_condition["status"] == "True"

        # Check resource references
        resource_refs = claim_data["status"]["resourceRefs"]
        table_count = 3
        assert len(resource_refs) == table_count
        table_names = [ref["name"] for ref in resource_refs]
        assert "test-instance-users" in table_names
        assert "test-instance-matches" in table_names
        assert "test-instance-config" in table_names
