"""
Scheduler implementation for the Virtual Coffee Platform.

This module handles the scheduling of matching operations using Kubernetes CronJobs
and ArgoCD Workflows.
"""
import logging
import asyncio
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.api.models.config import DeploymentConfig
from backend.api.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class MatchingScheduler:
    """
    Scheduler for the Virtual Coffee Platform matching operations.
    
    This class is responsible for:
    1. Converting deployment configurations to Kubernetes CronJob schedules
    2. Handling timezone calculations for scheduling
    3. Generating ArgoCD Workflow configurations
    4. Managing the scheduling lifecycle
    """
    
    def __init__(self):
        """Initialize the matching scheduler."""
        self.config_service = ConfigService()
    
    async def get_all_schedules(self) -> Dict[str, Dict]:
        """
        Get all deployment schedules.
        
        Returns:
            A dictionary mapping deployment IDs to schedule information
        """
        configs = await self.config_service.get_all_configs()
        
        schedules = {}
        for config in configs:
            schedule_info = await self.get_schedule_info(config)
            schedules[config.deployment_id] = schedule_info
        
        return schedules
    
    async def get_schedule_info(self, config: DeploymentConfig) -> Dict:
        """
        Get schedule information for a deployment.
        
        Args:
            config: The deployment configuration
            
        Returns:
            A dictionary containing schedule information
        """
        # Parse the cron expression
        cron_parts = config.schedule.split()
        if len(cron_parts) != 5:
            logger.error(f"Invalid cron expression: {config.schedule}")
            return {
                "valid": False,
                "error": "Invalid cron expression"
            }
        
        # Get timezone
        timezone = config.timezone or "UTC"
        
        try:
            tz = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {timezone}")
            return {
                "valid": False,
                "error": f"Unknown timezone: {timezone}"
            }
        
        # Calculate next run time (simplified)
        # In a real implementation, this would use a proper cron parser
        now = datetime.utcnow()
        
        # For demonstration purposes, we'll just add a day
        # In a real implementation, this would calculate the actual next run time
        next_run = now + timedelta(days=1)
        
        return {
            "valid": True,
            "cron": config.schedule,
            "timezone": timezone,
            "next_run_utc": next_run.isoformat(),
            "deployment_id": config.deployment_id,
            "meeting_size": config.meeting_size
        }
    
    def generate_cronjob_manifest(self, deployment_id: str, schedule: str, timezone: str) -> Dict:
        """
        Generate a Kubernetes CronJob manifest for a deployment.
        
        Args:
            deployment_id: The deployment ID
            schedule: The cron schedule expression
            timezone: The timezone for the schedule
            
        Returns:
            A dictionary containing the CronJob manifest
        """
        # Convert cron expression to Kubernetes format if needed
        k8s_schedule = schedule
        
        # Create the CronJob manifest
        manifest = {
            "apiVersion": "batch/v1",
            "kind": "CronJob",
            "metadata": {
                "name": f"virtual-coffee-matching-{deployment_id}",
                "namespace": "virtual-coffee",
                "labels": {
                    "app": "virtual-coffee",
                    "component": "matching",
                    "deployment-id": deployment_id
                }
            },
            "spec": {
                "schedule": k8s_schedule,
                "timeZone": timezone,
                "concurrencyPolicy": "Forbid",
                "successfulJobsHistoryLimit": 3,
                "failedJobsHistoryLimit": 3,
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "metadata": {
                                "labels": {
                                    "app": "virtual-coffee",
                                    "component": "matching",
                                    "deployment-id": deployment_id
                                }
                            },
                            "spec": {
                                "containers": [
                                    {
                                        "name": "matching",
                                        "image": "virtual-coffee/api:latest",
                                        "command": [
                                            "python",
                                            "-m",
                                            "backend.api.scheduler.run_matching"
                                        ],
                                        "env": [
                                            {
                                                "name": "DEPLOYMENT_ID",
                                                "value": deployment_id
                                            }
                                        ],
                                        "resources": {
                                            "requests": {
                                                "memory": "128Mi",
                                                "cpu": "100m"
                                            },
                                            "limits": {
                                                "memory": "256Mi",
                                                "cpu": "200m"
                                            }
                                        }
                                    }
                                ],
                                "restartPolicy": "OnFailure"
                            }
                        }
                    }
                }
            }
        }
        
        return manifest
    
    def generate_argocd_workflow(self, deployment_id: str, schedule: str, timezone: str) -> Dict:
        """
        Generate an ArgoCD Workflow for a deployment.
        
        Args:
            deployment_id: The deployment ID
            schedule: The cron schedule expression
            timezone: The timezone for the schedule
            
        Returns:
            A dictionary containing the ArgoCD Workflow manifest
        """
        # Create the ArgoCD Workflow manifest
        manifest = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "name": f"virtual-coffee-matching-{deployment_id}",
                "namespace": "argocd",
                "labels": {
                    "app": "virtual-coffee",
                    "component": "matching",
                    "deployment-id": deployment_id
                }
            },
            "spec": {
                "entrypoint": "matching-workflow",
                "arguments": {
                    "parameters": [
                        {
                            "name": "deployment-id",
                            "value": deployment_id
                        }
                    ]
                },
                "templates": [
                    {
                        "name": "matching-workflow",
                        "steps": [
                            [
                                {
                                    "name": "run-matching",
                                    "template": "run-matching",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "deployment-id",
                                                "value": "{{workflow.parameters.deployment-id}}"
                                            }
                                        ]
                                    }
                                }
                            ],
                            [
                                {
                                    "name": "send-notifications",
                                    "template": "send-notifications",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "deployment-id",
                                                "value": "{{workflow.parameters.deployment-id}}"
                                            }
                                        ]
                                    },
                                    "depends": "run-matching"
                                }
                            ]
                        ]
                    },
                    {
                        "name": "run-matching",
                        "inputs": {
                            "parameters": [
                                {
                                    "name": "deployment-id"
                                }
                            ]
                        },
                        "container": {
                            "image": "virtual-coffee/api:latest",
                            "command": [
                                "python",
                                "-m",
                                "backend.api.scheduler.run_matching"
                            ],
                            "env": [
                                {
                                    "name": "DEPLOYMENT_ID",
                                    "value": "{{inputs.parameters.deployment-id}}"
                                }
                            ]
                        }
                    },
                    {
                        "name": "send-notifications",
                        "inputs": {
                            "parameters": [
                                {
                                    "name": "deployment-id"
                                }
                            ]
                        },
                        "container": {
                            "image": "virtual-coffee/api:latest",
                            "command": [
                                "python",
                                "-m",
                                "backend.api.scheduler.send_notifications"
                            ],
                            "env": [
                                {
                                    "name": "DEPLOYMENT_ID",
                                    "value": "{{inputs.parameters.deployment-id}}"
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        return manifest
    
    async def apply_schedule(self, deployment_id: str) -> bool:
        """
        Apply the schedule for a deployment.
        
        This method:
        1. Gets the deployment configuration
        2. Generates the CronJob and ArgoCD Workflow manifests
        3. Applies the manifests to the Kubernetes cluster
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            True if the schedule was applied successfully, False otherwise
        """
        # Get the deployment configuration
        config = await self.config_service.get_config(deployment_id)
        if not config:
            logger.error(f"No configuration found for deployment {deployment_id}")
            return False
        
        # Get schedule information
        schedule_info = await self.get_schedule_info(config)
        if not schedule_info["valid"]:
            logger.error(f"Invalid schedule for deployment {deployment_id}: {schedule_info['error']}")
            return False
        
        # Generate manifests
        cronjob = self.generate_cronjob_manifest(
            deployment_id,
            config.schedule,
            config.timezone
        )
        
        workflow = self.generate_argocd_workflow(
            deployment_id,
            config.schedule,
            config.timezone
        )
        
        # Apply the manifests to the cluster
        try:
            # Apply CronJob manifest
            success = await self._apply_kubernetes_manifest(cronjob, "CronJob")
            if not success:
                logger.error(f"Failed to apply CronJob for deployment {deployment_id}")
                return False
            
            # Apply ArgoCD Workflow manifest
            success = await self._apply_argocd_workflow(workflow)
            if not success:
                logger.error(f"Failed to apply ArgoCD Workflow for deployment {deployment_id}")
                # Try to clean up the CronJob if workflow application fails
                await self._delete_kubernetes_manifest(
                    f"virtual-coffee-matching-{deployment_id}",
                    "CronJob",
                    "virtual-coffee"
                )
                return False
            
            logger.info(f"Successfully applied schedule for deployment {deployment_id}")
            return True
        except Exception as e:
            logger.exception(f"Error applying schedule for deployment {deployment_id}: {e}")
            return False
    
    async def remove_schedule(self, deployment_id: str) -> bool:
        """
        Remove the schedule for a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            True if the schedule was removed successfully, False otherwise
        """
        try:
            # Delete the CronJob
            cronjob_success = await self._delete_kubernetes_manifest(
                f"virtual-coffee-matching-{deployment_id}",
                "CronJob",
                "virtual-coffee"
            )
            
            # Delete the ArgoCD Workflow
            workflow_success = await self._delete_kubernetes_manifest(
                f"virtual-coffee-matching-{deployment_id}",
                "Workflow",
                "argocd"
            )
            
            if cronjob_success and workflow_success:
                logger.info(f"Successfully removed schedule for deployment {deployment_id}")
                return True
            else:
                logger.warning(f"Partial success removing schedule for deployment {deployment_id}")
                return False
        except Exception as e:
            logger.exception(f"Error removing schedule for deployment {deployment_id}: {e}")
            return False
            
    async def _apply_kubernetes_manifest(self, manifest: Dict, kind: str, max_retries: int = 3) -> bool:
        """
        Apply a Kubernetes manifest to the cluster.
        
        Args:
            manifest: The Kubernetes manifest to apply
            kind: The kind of resource being applied (for logging)
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if the manifest was applied successfully, False otherwise
        """
        import json
        import tempfile
        import subprocess
        import os
        
        # In a real implementation, this would use the Kubernetes Python client
        # or a similar library. For this implementation, we'll use kubectl via subprocess.
        
        retries = 0
        while retries <= max_retries:
            try:
                # Create a temporary file for the manifest
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
                    json.dump(manifest, temp)
                    temp_path = temp.name
                
                try:
                    # Apply the manifest using kubectl
                    logger.info(f"Applying {kind} manifest: {manifest['metadata']['name']}")
                    
                    # Execute kubectl apply
                    result = subprocess.run(
                        ["kubectl", "apply", "-f", temp_path],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    logger.info(f"Successfully applied {kind}: {result.stdout.strip()}")
                    return True
                    
                finally:
                    # Clean up the temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
            except subprocess.CalledProcessError as e:
                retries += 1
                logger.warning(
                    f"Failed to apply {kind} (attempt {retries}/{max_retries}): "
                    f"{e.stderr.strip() if e.stderr else str(e)}"
                )
                
                if retries <= max_retries:
                    # Wait before retrying (exponential backoff)
                    await asyncio.sleep(2 ** retries)
                else:
                    logger.error(f"Failed to apply {kind} after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                logger.exception(f"Error applying {kind}: {e}")
                return False
                
        return False
        
    async def _apply_argocd_workflow(self, workflow: Dict, max_retries: int = 3) -> bool:
        """
        Apply an ArgoCD Workflow manifest to the cluster.
        
        Args:
            workflow: The ArgoCD Workflow manifest to apply
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if the workflow was applied successfully, False otherwise
        """
        # ArgoCD workflows require special handling through the Argo CLI
        # For this implementation, we'll use the same approach as _apply_kubernetes_manifest
        return await self._apply_kubernetes_manifest(workflow, "ArgoCD Workflow", max_retries)
        
    async def _delete_kubernetes_manifest(self, name: str, kind: str, namespace: str, max_retries: int = 3) -> bool:
        """
        Delete a Kubernetes resource from the cluster.
        
        Args:
            name: The name of the resource to delete
            kind: The kind of resource to delete
            namespace: The namespace containing the resource
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if the resource was deleted successfully, False otherwise
        """
        import subprocess
        import asyncio
        
        retries = 0
        while retries <= max_retries:
            try:
                # Execute kubectl delete
                logger.info(f"Deleting {kind} {name} in namespace {namespace}")
                
                result = subprocess.run(
                    ["kubectl", "delete", kind.lower(), name, "-n", namespace],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Successfully deleted {kind}: {result.stdout.strip()}")
                return True
                
            except subprocess.CalledProcessError as e:
                # Check if the resource doesn't exist (which is fine)
                if "not found" in e.stderr:
                    logger.info(f"{kind} {name} not found in namespace {namespace}, nothing to delete")
                    return True
                    
                retries += 1
                logger.warning(
                    f"Failed to delete {kind} (attempt {retries}/{max_retries}): "
                    f"{e.stderr.strip() if e.stderr else str(e)}"
                )
                
                if retries <= max_retries:
                    # Wait before retrying (exponential backoff)
                    await asyncio.sleep(2 ** retries)
                else:
                    logger.error(f"Failed to delete {kind} after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                logger.exception(f"Error deleting {kind}: {e}")
                return False
                
        return False