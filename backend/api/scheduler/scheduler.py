"""
Scheduler implementation for the Virtual Coffee Platform.

This module handles the scheduling of matching operations using Kubernetes CronJobs
and ArgoCD Workflows.
"""
import logging
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
        
        This method would typically:
        1. Get the deployment configuration
        2. Generate the CronJob and ArgoCD Workflow manifests
        3. Apply the manifests to the Kubernetes cluster
        
        In this implementation, we'll just log the actions.
        
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
        
        # In a real implementation, we would apply these manifests to the cluster
        # For now, we'll just log them
        logger.info(f"Generated CronJob for deployment {deployment_id}")
        logger.info(f"Generated ArgoCD Workflow for deployment {deployment_id}")
        
        return True
    
    async def remove_schedule(self, deployment_id: str) -> bool:
        """
        Remove the schedule for a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            True if the schedule was removed successfully, False otherwise
        """
        # In a real implementation, we would delete the CronJob and Workflow
        # For now, we'll just log the action
        logger.info(f"Removed schedule for deployment {deployment_id}")
        
        return True