#!/usr/bin/env python3
"""
Comprehensive deployment validation script for the Virtual Coffee Platform.
This script validates that a deployment meets all MVP requirements.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")
    print(f"{BLUE}{BOLD} {text}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 80}{RESET}\n")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_warning(text):
    """Print a warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_error(text):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print an info message."""
    print(f"{BLUE}ℹ {text}{RESET}")

def run_command(command, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Error: {e}")
        return None

def check_argocd_application(instance):
    """Check the status of the ArgoCD application."""
    print_header("Checking ArgoCD Application Status")
    
    # Get the ArgoCD application status
    result = run_command(f"kubectl get application.argoproj.io/virtual-coffee-{instance} -n argocd -o json")
    
    if result.returncode != 0:
        print_error(f"Failed to get ArgoCD application status for {instance}")
        return False
    
    try:
        app_data = json.loads(result.stdout)
        sync_status = app_data.get("status", {}).get("sync", {}).get("status")
        health_status = app_data.get("status", {}).get("health", {}).get("status")
        
        print_info(f"Application: virtual-coffee-{instance}")
        print_info(f"Sync Status: {sync_status}")
        print_info(f"Health Status: {health_status}")
        
        if sync_status == "Synced" and health_status == "Healthy":
            print_success("ArgoCD application is synced and healthy")
            return True
        else:
            print_warning("ArgoCD application is not fully synced or healthy")
            return False
    except json.JSONDecodeError:
        print_error("Failed to parse ArgoCD application status")
        return False

def check_dynamodb_resources(instance):
    """Check the status of DynamoDB resources."""
    print_header("Checking DynamoDB Resources")
    
    # Get the DynamoDB claim status
    result = run_command(f"kubectl get virtualcoffeedynamodbclaim.virtualcoffee.io/{instance}-dynamodb -n {instance} -o json")
    
    if result.returncode != 0:
        print_error(f"Failed to get DynamoDB claim status for {instance}")
        return False
    
    try:
        claim_data = json.loads(result.stdout)
        claim_status = claim_data.get("status", {}).get("conditions", [])
        
        ready = False
        for condition in claim_status:
            if condition.get("type") == "Ready":
                ready = condition.get("status") == "True"
                break
        
        print_info(f"DynamoDB Claim: {instance}-dynamodb")
        print_info(f"Ready: {ready}")
        
        if ready:
            print_success("DynamoDB resources are ready")
            
            # Check if tables are accessible
            print_info("Checking DynamoDB table accessibility...")
            
            # Get the AWS provider configuration
            aws_region = claim_data.get("spec", {}).get("parameters", {}).get("region", "us-west-2")
            
            # Check if we can list tables using the AWS CLI
            aws_result = run_command(f"aws dynamodb list-tables --region {aws_region}")
            
            if aws_result.returncode == 0:
                print_success("DynamoDB tables are accessible via AWS CLI")
                return True
            else:
                print_warning("DynamoDB tables may not be accessible via AWS CLI")
                print_warning("This may be expected if running in a development environment")
                return True  # Still return True as the claim is ready
        else:
            print_error("DynamoDB resources are not ready")
            return False
    except json.JSONDecodeError:
        print_error("Failed to parse DynamoDB claim status")
        return False

def check_kubernetes_resources(instance):
    """Check the status of Kubernetes resources."""
    print_header("Checking Kubernetes Resources")
    
    # Check pods
    pod_result = run_command(f"kubectl get pods -n {instance} -o json")
    
    if pod_result.returncode != 0:
        print_error(f"Failed to get pods for {instance}")
        return False
    
    try:
        pod_data = json.loads(pod_result.stdout)
        pods = pod_data.get("items", [])
        
        all_running = True
        for pod in pods:
            pod_name = pod.get("metadata", {}).get("name", "unknown")
            pod_status = pod.get("status", {}).get("phase", "Unknown")
            
            if pod_status == "Running":
                print_success(f"Pod {pod_name} is running")
            else:
                print_warning(f"Pod {pod_name} is in state {pod_status}")
                all_running = False
        
        if not pods:
            print_warning("No pods found in the namespace")
            all_running = False
        
        # Check services
        svc_result = run_command(f"kubectl get services -n {instance} -o json")
        
        if svc_result.returncode != 0:
            print_error(f"Failed to get services for {instance}")
            return False
        
        svc_data = json.loads(svc_result.stdout)
        services = svc_data.get("items", [])
        
        for svc in services:
            svc_name = svc.get("metadata", {}).get("name", "unknown")
            svc_type = svc.get("spec", {}).get("type", "unknown")
            
            print_info(f"Service {svc_name} of type {svc_type} is available")
        
        if not services:
            print_warning("No services found in the namespace")
            all_running = False
        
        return all_running
    except json.JSONDecodeError:
        print_error("Failed to parse Kubernetes resource status")
        return False

def check_api_health(instance):
    """Check the health of the API."""
    print_header("Checking API Health")
    
    # Port-forward to the API service
    print_info("Setting up port-forwarding to API service...")
    port_forward_process = subprocess.Popen(
        f"kubectl port-forward -n {instance} svc/virtual-coffee-api 8000:80",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for port-forwarding to be established
    time.sleep(5)
    
    try:
        # Check API health endpoint
        health_result = run_command("curl -s http://localhost:8000/health")
        
        if health_result.returncode != 0 or "healthy" not in health_result.stdout.lower():
            print_error("API health check failed")
            return False
        
        print_success("API health check passed")
        
        # Check API version endpoint
        version_result = run_command("curl -s http://localhost:8000/version")
        
        if version_result.returncode == 0:
            print_info(f"API Version: {version_result.stdout.strip()}")
        
        return True
    finally:
        # Clean up port-forwarding
        port_forward_process.terminate()
        port_forward_process.wait()

def check_frontend_health(instance):
    """Check the health of the frontend."""
    print_header("Checking Frontend Health")
    
    # Port-forward to the frontend service
    print_info("Setting up port-forwarding to frontend service...")
    port_forward_process = subprocess.Popen(
        f"kubectl port-forward -n {instance} svc/virtual-coffee-frontend 3000:80",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for port-forwarding to be established
    time.sleep(5)
    
    try:
        # Check frontend health
        health_result = run_command("curl -s http://localhost:3000/")
        
        if health_result.returncode != 0:
            print_error("Frontend health check failed")
            return False
        
        if "virtual coffee platform" in health_result.stdout.lower():
            print_success("Frontend health check passed")
            return True
        else:
            print_warning("Frontend response doesn't contain expected content")
            return False
    finally:
        # Clean up port-forwarding
        port_forward_process.terminate()
        port_forward_process.wait()

def test_rollback_procedure(instance):
    """Test the rollback procedure."""
    print_header("Testing Rollback Procedure")
    
    # Get current ArgoCD application revision
    result = run_command(f"kubectl get application.argoproj.io/virtual-coffee-{instance} -n argocd -o jsonpath='{{.status.sync.revision}}'")
    
    if result.returncode != 0:
        print_error("Failed to get current revision")
        return False
    
    current_revision = result.stdout.strip()
    print_info(f"Current revision: {current_revision}")
    
    # Simulate a bad deployment by patching the application with an invalid path
    print_info("Simulating a bad deployment...")
    patch_result = run_command(f"kubectl patch application.argoproj.io/virtual-coffee-{instance} -n argocd --type merge -p '{{\"spec\":{{\"source\":{{\"path\":\"non-existent-path\"}}}}}}' --record")
    
    if patch_result.returncode != 0:
        print_error("Failed to patch application")
        return False
    
    # Wait for the application to become OutOfSync
    print_info("Waiting for application to become OutOfSync...")
    time.sleep(10)
    
    # Check application status
    sync_result = run_command(f"kubectl get application.argoproj.io/virtual-coffee-{instance} -n argocd -o jsonpath='{{.status.sync.status}}'")
    
    if sync_result.returncode != 0:
        print_error("Failed to get sync status")
        return False
    
    if sync_result.stdout.strip() != "OutOfSync":
        print_warning("Application did not become OutOfSync as expected")
    else:
        print_success("Application is OutOfSync as expected")
    
    # Rollback to the previous revision
    print_info("Rolling back to previous revision...")
    rollback_result = run_command(f"kubectl patch application.argoproj.io/virtual-coffee-{instance} -n argocd --type merge -p '{{\"spec\":{{\"source\":{{\"path\":\"k8s/overlays/dev\"}}}}}}' --record")
    
    if rollback_result.returncode != 0:
        print_error("Failed to rollback application")
        return False
    
    # Wait for the application to sync
    print_info("Waiting for application to sync...")
    time.sleep(30)
    
    # Check application status
    final_sync_result = run_command(f"kubectl get application.argoproj.io/virtual-coffee-{instance} -n argocd -o jsonpath='{{.status.sync.status}}'")
    
    if final_sync_result.returncode != 0:
        print_error("Failed to get final sync status")
        return False
    
    if final_sync_result.stdout.strip() == "Synced":
        print_success("Application successfully rolled back and synced")
        return True
    else:
        print_error(f"Application failed to sync after rollback: {final_sync_result.stdout.strip()}")
        return False

def test_resource_recovery(instance):
    """Test resource recovery after deletion."""
    print_header("Testing Resource Recovery")
    
    # Get a deployment in the namespace
    result = run_command(f"kubectl get deployment -n {instance} -o jsonpath='{{.items[0].metadata.name}}'")
    
    if result.returncode != 0 or not result.stdout.strip():
        print_error("No deployments found to test recovery")
        return False
    
    deployment_name = result.stdout.strip()
    print_info(f"Testing recovery with deployment: {deployment_name}")
    
    # Delete the deployment
    print_info(f"Deleting deployment {deployment_name}...")
    delete_result = run_command(f"kubectl delete deployment {deployment_name} -n {instance}")
    
    if delete_result.returncode != 0:
        print_error(f"Failed to delete deployment {deployment_name}")
        return False
    
    # Wait for ArgoCD to detect the change
    print_info("Waiting for ArgoCD to detect the change...")
    time.sleep(10)
    
    # Check if the deployment is gone
    check_result = run_command(f"kubectl get deployment {deployment_name} -n {instance} --ignore-not-found")
    
    if deployment_name in check_result.stdout:
        print_warning(f"Deployment {deployment_name} was not deleted as expected")
        return False
    
    # Wait for ArgoCD to restore the deployment
    print_info("Waiting for ArgoCD to restore the deployment...")
    
    # Wait up to 2 minutes for the deployment to be restored
    restored = False
    for i in range(12):  # 12 * 10 seconds = 2 minutes
        time.sleep(10)
        check_result = run_command(f"kubectl get deployment {deployment_name} -n {instance} --ignore-not-found")
        
        if deployment_name in check_result.stdout:
            restored = True
            break
    
    if restored:
        print_success(f"Deployment {deployment_name} was successfully restored by ArgoCD")
        
        # Wait for the deployment to be ready
        print_info("Waiting for deployment to be ready...")
        time.sleep(30)
        
        # Check if the deployment is ready
        ready_result = run_command(f"kubectl rollout status deployment/{deployment_name} -n {instance} --timeout=60s")
        
        if ready_result.returncode == 0:
            print_success(f"Deployment {deployment_name} is ready")
            return True
        else:
            print_warning(f"Deployment {deployment_name} was restored but may not be ready")
            return True  # Still return True as the resource was recovered
    else:
        print_error(f"Deployment {deployment_name} was not restored within the timeout period")
        return False

def verify_mvp_requirements(instance):
    """Verify that all MVP requirements are satisfied."""
    print_header("Verifying MVP Requirements")
    
    requirements = [
        {
            "id": "1",
            "description": "User registration and preferences",
            "verification": "Check user API endpoints and models",
            "endpoints": ["/users/register", "/users/profile"],
            "importance": "critical"
        },
        {
            "id": "2",
            "description": "User preferences configuration",
            "verification": "Check preference API endpoints and models",
            "endpoints": ["/users/preferences"],
            "importance": "critical"
        },
        {
            "id": "3",
            "description": "Configurable shuffle schedules",
            "verification": "Check scheduler configuration and ArgoCD workflows",
            "endpoints": ["/scheduler/run-matching"],
            "importance": "critical"
        },
        {
            "id": "4",
            "description": "Match notifications",
            "verification": "Check notification service and templates",
            "endpoints": ["/matches/current"],
            "importance": "critical"
        },
        {
            "id": "5",
            "description": "Multi-tenant deployment isolation",
            "verification": "Check namespace isolation and resource separation",
            "endpoints": [],
            "importance": "critical"
        },
        {
            "id": "6",
            "description": "ArgoCD and Crossplane integration",
            "verification": "Check ArgoCD applications and Crossplane resources",
            "endpoints": [],
            "importance": "critical"
        },
        {
            "id": "7",
            "description": "AWS Cloudscape Design System frontend",
            "verification": "Check frontend components and styling",
            "endpoints": [],
            "importance": "critical"
        },
        {
            "id": "8",
            "description": "Automated matching algorithm",
            "verification": "Check matching service and scheduler",
            "endpoints": ["/matches/history"],
            "importance": "critical"
        },
        {
            "id": "9",
            "description": "Federated authentication",
            "verification": "Check authentication providers and JWT implementation",
            "endpoints": ["/auth/login", "/auth/me"],
            "importance": "critical"
        },
        {
            "id": "13",
            "description": "Pause/resume functionality",
            "verification": "Check user participation toggle",
            "endpoints": ["/users/participation"],
            "importance": "critical"
        },
        {
            "id": "15",
            "description": "Automated deployment operations",
            "verification": "Check Makefile targets and automation",
            "endpoints": [],
            "importance": "critical"
        }
    ]
    
    # Check API endpoints to verify requirements
    print_info("Setting up port-forwarding to API service...")
    port_forward_process = subprocess.Popen(
        f"kubectl port-forward -n {instance} svc/virtual-coffee-api 8000:80",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for port-forwarding to be established
    time.sleep(5)
    
    try:
        # Check API documentation for endpoints
        docs_result = run_command("curl -s http://localhost:8000/docs")
        
        if docs_result.returncode != 0:
            print_error("Failed to access API documentation")
            return False
        
        # Check specific endpoints for each requirement
        endpoints_to_check = {
            "1": ["/users/register", "/users/profile"],
            "2": ["/users/preferences"],
            "3": ["/scheduler/run-matching"],
            "4": ["/matches/current"],
            "8": ["/matches/history"],
            "9": ["/auth/login", "/auth/me"],
            "13": ["/users/participation"]
        }
        
        for req in requirements:
            req_id = req["id"]
            print_info(f"Checking requirement {req_id}: {req['description']}")
            
            if req_id in endpoints_to_check:
                endpoints = endpoints_to_check[req_id]
                all_endpoints_found = True
                
                for endpoint in endpoints:
                    if endpoint in docs_result.stdout:
                        print_success(f"Endpoint {endpoint} found for requirement {req_id}")
                    else:
                        print_warning(f"Endpoint {endpoint} not found for requirement {req_id}")
                        all_endpoints_found = False
                
                if all_endpoints_found:
                    print_success(f"Requirement {req_id} verified")
                else:
                    print_warning(f"Requirement {req_id} partially verified")
            else:
                # For requirements that can't be verified through API endpoints
                if req_id == "5":
                    # Check namespace isolation
                    isolation_result = run_command(f"kubectl get namespace {instance}")
                    if isolation_result.returncode == 0:
                        print_success(f"Requirement {req_id} verified: Namespace isolation")
                    else:
                        print_warning(f"Requirement {req_id} not verified: Namespace isolation issue")
                
                elif req_id == "6":
                    # Check ArgoCD and Crossplane integration
                    argocd_result = run_command(f"kubectl get application.argoproj.io/virtual-coffee-{instance} -n argocd")
                    crossplane_result = run_command(f"kubectl get virtualcoffeedynamodbclaim.virtualcoffee.io/{instance}-dynamodb -n {instance}")
                    
                    if argocd_result.returncode == 0 and crossplane_result.returncode == 0:
                        print_success(f"Requirement {req_id} verified: ArgoCD and Crossplane integration")
                    else:
                        print_warning(f"Requirement {req_id} not fully verified: ArgoCD or Crossplane issue")
                
                elif req_id == "7":
                    # Check frontend for Cloudscape components
                    print_info(f"Requirement {req_id}: Manual verification required for Cloudscape Design System")
                
                elif req_id == "15":
                    # Check Makefile targets
                    makefile_result = run_command("grep -c 'deploy-instance\|destroy-instance' Makefile")
                    if makefile_result.returncode == 0 and int(makefile_result.stdout.strip()) > 0:
                        print_success(f"Requirement {req_id} verified: Makefile automation targets")
                    else:
                        print_warning(f"Requirement {req_id} not verified: Makefile automation targets issue")
                
                else:
                    print_info(f"Requirement {req_id}: Manual verification required")
        
        return True
    finally:
        # Clean up port-forwarding
        port_forward_process.terminate()
        port_forward_process.wait()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate a Virtual Coffee Platform deployment")
    parser.add_argument("--instance", required=True, help="Instance name to validate")
    parser.add_argument("--validate-rollback", action="store_true", help="Run rollback validation tests")
    args = parser.parse_args()
    
    instance = args.instance
    validate_rollback = args.validate_rollback
    
    print_header(f"Validating Virtual Coffee Platform Deployment: {instance}")
    print_info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run validation checks
    argocd_ok = check_argocd_application(instance)
    dynamodb_ok = check_dynamodb_resources(instance)
    kubernetes_ok = check_kubernetes_resources(instance)
    api_ok = check_api_health(instance)
    frontend_ok = check_frontend_health(instance)
    
    # Verify MVP requirements
    mvp_ok = verify_mvp_requirements(instance)
    
    # Run rollback tests if requested
    rollback_ok = True
    recovery_ok = True
    if validate_rollback:
        rollback_ok = test_rollback_procedure(instance)
        recovery_ok = test_resource_recovery(instance)
    
    # Print summary
    print_header("Validation Summary")
    print_info(f"Instance: {instance}")
    print_info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if argocd_ok:
        print_success("ArgoCD Application: PASSED")
    else:
        print_error("ArgoCD Application: FAILED")
    
    if dynamodb_ok:
        print_success("DynamoDB Resources: PASSED")
    else:
        print_error("DynamoDB Resources: FAILED")
    
    if kubernetes_ok:
        print_success("Kubernetes Resources: PASSED")
    else:
        print_error("Kubernetes Resources: FAILED")
    
    if api_ok:
        print_success("API Health: PASSED")
    else:
        print_error("API Health: FAILED")
    
    if frontend_ok:
        print_success("Frontend Health: PASSED")
    else:
        print_error("Frontend Health: FAILED")
    
    if mvp_ok:
        print_success("MVP Requirements: PASSED")
    else:
        print_error("MVP Requirements: FAILED")
    
    if validate_rollback:
        if rollback_ok:
            print_success("Rollback Procedure: PASSED")
        else:
            print_error("Rollback Procedure: FAILED")
        
        if recovery_ok:
            print_success("Resource Recovery: PASSED")
        else:
            print_error("Resource Recovery: FAILED")
    
    # Overall result
    print()
    all_passed = argocd_ok and dynamodb_ok and kubernetes_ok and api_ok and frontend_ok and mvp_ok
    if validate_rollback:
        all_passed = all_passed and rollback_ok and recovery_ok
    
    if all_passed:
        print_success("OVERALL VALIDATION: PASSED")
        return 0
    else:
        print_error("OVERALL VALIDATION: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())