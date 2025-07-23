#!/usr/bin/env python3
"""
Deployment validation script for the Virtual Coffee Platform.

This script validates the deployment of the Virtual Coffee Platform by checking:
1. ArgoCD application status
2. Crossplane resource status
3. Kubernetes resource status
4. AWS resource provisioning

Usage:
    python validate_deployment.py --instance <instance-name>
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Any, Optional, Tuple


def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


def check_kubectl_access() -> bool:
    """Check if kubectl is available and configured."""
    print("Checking kubectl access...")
    exit_code, stdout, stderr = run_command(["kubectl", "cluster-info"])
    if exit_code != 0:
        print(f"Error: kubectl not configured correctly: {stderr}")
        return False
    print("✅ kubectl access confirmed")
    return True


def check_argocd_app(instance: str) -> bool:
    """Check if the ArgoCD application for the instance is healthy."""
    print(f"Checking ArgoCD application for instance {instance}...")
    
    # Get the ArgoCD application status
    exit_code, stdout, stderr = run_command([
        "kubectl", "get", "application.argoproj.io/virtual-coffee-" + instance,
        "-n", "argocd", "-o", "json"
    ])
    
    if exit_code != 0:
        print(f"Error: ArgoCD application not found: {stderr}")
        return False
    
    try:
        app_data = json.loads(stdout)
        health = app_data.get("status", {}).get("health", {}).get("status")
        sync_status = app_data.get("status", {}).get("sync", {}).get("status")
        
        if health != "Healthy":
            print(f"Warning: ArgoCD application health is {health}, expected Healthy")
            return False
        
        if sync_status != "Synced":
            print(f"Warning: ArgoCD application sync status is {sync_status}, expected Synced")
            return False
        
        print(f"✅ ArgoCD application is healthy and synced")
        return True
    
    except json.JSONDecodeError:
        print(f"Error: Could not parse ArgoCD application status")
        return False


def check_crossplane_resources(instance: str) -> bool:
    """Check if Crossplane resources for the instance are ready."""
    print(f"Checking Crossplane resources for instance {instance}...")
    
    # Check DynamoDB claim
    exit_code, stdout, stderr = run_command([
        "kubectl", "get", f"virtualcoffeedynamodbclaim.virtualcoffee.io/{instance}-dynamodb",
        "-n", instance, "-o", "json"
    ])
    
    if exit_code != 0:
        print(f"Error: DynamoDB claim not found: {stderr}")
        return False
    
    try:
        claim_data = json.loads(stdout)
        conditions = claim_data.get("status", {}).get("conditions", [])
        
        ready_condition = next((c for c in conditions if c.get("type") == "Ready"), None)
        if not ready_condition or ready_condition.get("status") != "True":
            print(f"Warning: DynamoDB claim is not ready")
            return False
        
        print(f"✅ DynamoDB claim is ready")
        return True
    
    except json.JSONDecodeError:
        print(f"Error: Could not parse DynamoDB claim status")
        return False


def check_kubernetes_resources(instance: str) -> bool:
    """Check if Kubernetes resources for the instance are ready."""
    print(f"Checking Kubernetes resources for instance {instance}...")
    
    # Check namespace
    exit_code, stdout, stderr = run_command([
        "kubectl", "get", "namespace", instance
    ])
    
    if exit_code != 0:
        print(f"Error: Namespace {instance} not found")
        return False
    
    # Check deployments
    exit_code, stdout, stderr = run_command([
        "kubectl", "get", "deployments", "-n", instance, "-o", "json"
    ])
    
    if exit_code != 0:
        print(f"Error: Could not get deployments: {stderr}")
        return False
    
    try:
        deployments_data = json.loads(stdout)
        items = deployments_data.get("items", [])
        
        if not items:
            print(f"Warning: No deployments found in namespace {instance}")
            return False
        
        all_ready = True
        for deployment in items:
            name = deployment.get("metadata", {}).get("name", "unknown")
            status = deployment.get("status", {})
            ready_replicas = status.get("readyReplicas", 0)
            replicas = status.get("replicas", 0)
            
            if ready_replicas < replicas:
                print(f"Warning: Deployment {name} has {ready_replicas}/{replicas} ready replicas")
                all_ready = False
        
        if all_ready:
            print(f"✅ All deployments are ready")
            return True
        else:
            return False
    
    except json.JSONDecodeError:
        print(f"Error: Could not parse deployments data")
        return False


def check_aws_resources(instance: str) -> bool:
    """Check if AWS resources for the instance are properly provisioned."""
    print(f"Checking AWS resources for instance {instance}...")
    
    # Get the DynamoDB tables from Crossplane
    exit_code, stdout, stderr = run_command([
        "kubectl", "get", "table.dynamodb.aws.crossplane.io",
        "-o", "json"
    ])
    
    if exit_code != 0:
        print(f"Error: Could not get DynamoDB tables: {stderr}")
        return False
    
    try:
        tables_data = json.loads(stdout)
        items = tables_data.get("items", [])
        
        if not items:
            print(f"Warning: No DynamoDB tables found")
            return False
        
        instance_tables = [
            table for table in items
            if instance in table.get("metadata", {}).get("name", "")
        ]
        
        if not instance_tables:
            print(f"Warning: No DynamoDB tables found for instance {instance}")
            return False
        
        all_ready = True
        for table in instance_tables:
            name = table.get("metadata", {}).get("name", "unknown")
            conditions = table.get("status", {}).get("conditions", [])
            
            ready_condition = next((c for c in conditions if c.get("type") == "Ready"), None)
            if not ready_condition or ready_condition.get("status") != "True":
                print(f"Warning: DynamoDB table {name} is not ready")
                all_ready = False
        
        if all_ready:
            print(f"✅ All DynamoDB tables are ready")
            return True
        else:
            return False
    
    except json.JSONDecodeError:
        print(f"Error: Could not parse DynamoDB tables data")
        return False


def validate_deployment(instance: str) -> bool:
    """Validate the deployment of the Virtual Coffee Platform."""
    print(f"Validating deployment for instance: {instance}")
    print("=" * 80)
    
    # Check kubectl access
    if not check_kubectl_access():
        return False
    
    # Check ArgoCD application
    argocd_ok = check_argocd_app(instance)
    
    # Check Crossplane resources
    crossplane_ok = check_crossplane_resources(instance)
    
    # Check Kubernetes resources
    k8s_ok = check_kubernetes_resources(instance)
    
    # Check AWS resources
    aws_ok = check_aws_resources(instance)
    
    # Overall status
    print("\nOverall Validation Results:")
    print(f"ArgoCD Application: {'✅ PASS' if argocd_ok else '❌ FAIL'}")
    print(f"Crossplane Resources: {'✅ PASS' if crossplane_ok else '❌ FAIL'}")
    print(f"Kubernetes Resources: {'✅ PASS' if k8s_ok else '❌ FAIL'}")
    print(f"AWS Resources: {'✅ PASS' if aws_ok else '❌ FAIL'}")
    
    all_ok = argocd_ok and crossplane_ok and k8s_ok and aws_ok
    print(f"\nFinal Result: {'✅ DEPLOYMENT VALID' if all_ok else '❌ DEPLOYMENT INVALID'}")
    
    return all_ok


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate Virtual Coffee Platform deployment")
    parser.add_argument("--instance", required=True, help="Instance name to validate")
    args = parser.parse_args()
    
    success = validate_deployment(args.instance)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()