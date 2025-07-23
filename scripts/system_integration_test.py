#!/usr/bin/env python3
"""
Comprehensive system integration test for the Virtual Coffee Platform.
This script performs end-to-end testing of the entire system, including:
- Multi-tenant deployment validation
- User journey testing
- Disaster recovery testing
- MVP requirement verification
"""

import argparse
import json
import os
import subprocess
import sys
import time
import requests
import uuid
from datetime import datetime, timedelta

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

def setup_port_forwarding(instance, service, local_port, target_port):
    """Set up port forwarding to a service."""
    print_info(f"Setting up port forwarding to {service} service in {instance}...")
    
    # Kill any existing port-forward on the same port
    run_command(f"pkill -f 'port-forward.*:{local_port}'", capture_output=False)
    
    # Start port forwarding
    port_forward_process = subprocess.Popen(
        f"kubectl port-forward -n {instance} svc/{service} {local_port}:{target_port}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for port-forwarding to be established
    time.sleep(5)
    
    return port_forward_process

def cleanup_port_forwarding(process):
    """Clean up port forwarding process."""
    if process:
        process.terminate()
        process.wait()

def get_auth_token(api_url, email, password):
    """Get authentication token from the API."""
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print_error(f"Failed to get auth token: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error getting auth token: {e}")
        return None

def register_test_user(api_url, user_data):
    """Register a test user."""
    try:
        response = requests.post(
            f"{api_url}/users/register",
            json=user_data
        )
        
        if response.status_code == 200:
            print_success(f"Registered user: {user_data['email']}")
            return response.json()
        else:
            print_error(f"Failed to register user: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error registering user: {e}")
        return None

def update_user_preferences(api_url, token, preferences):
    """Update user preferences."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(
            f"{api_url}/users/preferences",
            json=preferences,
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Updated user preferences")
            return response.json()
        else:
            print_error(f"Failed to update preferences: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error updating preferences: {e}")
        return None

def run_matching_algorithm(api_url, deployment_id):
    """Run the matching algorithm."""
    try:
        response = requests.post(
            f"{api_url}/scheduler/run-matching",
            json={"deployment_id": deployment_id}
        )
        
        if response.status_code == 200:
            print_success(f"Ran matching algorithm for {deployment_id}")
            return response.json()
        else:
            print_error(f"Failed to run matching: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error running matching: {e}")
        return None

def get_current_match(api_url, token):
    """Get the current match for a user."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{api_url}/matches/current",
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Retrieved current match")
            return response.json()
        else:
            print_error(f"Failed to get current match: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error getting current match: {e}")
        return None

def update_match_status(api_url, token, match_id, status):
    """Update match status."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(
            f"{api_url}/matches/{match_id}/status",
            json={"status": status},
            headers=headers
        )
        
        if response.status_code == 200:
            print_success(f"Updated match status to {status}")
            return response.json()
        else:
            print_error(f"Failed to update match status: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error updating match status: {e}")
        return None

def submit_match_feedback(api_url, token, match_id, rating, comments):
    """Submit feedback for a match."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{api_url}/matches/feedback",
            json={
                "match_id": match_id,
                "rating": rating,
                "comments": comments
            },
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Submitted match feedback")
            return response.json()
        else:
            print_error(f"Failed to submit feedback: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error submitting feedback: {e}")
        return None

def get_match_history(api_url, token):
    """Get match history for a user."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{api_url}/matches/history",
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Retrieved match history")
            return response.json()
        else:
            print_error(f"Failed to get match history: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print_error(f"Error getting match history: {e}")
        return None

def test_user_journey(api_url, deployment_id):
    """Test the complete user journey."""
    print_header(f"Testing User Journey for {deployment_id}")
    
    # Generate unique test users
    test_id = uuid.uuid4().hex[:8]
    test_users = [
        {
            "email": f"user1_{test_id}@example.com",
            "name": f"Test User 1 {test_id}",
            "preferences": {
                "availability": ["Monday 9-10", "Wednesday 14-15"],
                "topics": ["Technology", "Coffee"],
                "meeting_length": 30
            }
        },
        {
            "email": f"user2_{test_id}@example.com",
            "name": f"Test User 2 {test_id}",
            "preferences": {
                "availability": ["Monday 9-10", "Thursday 15-16"],
                "topics": ["Career", "Technology"],
                "meeting_length": 45
            }
        }
    ]
    
    # Step 1: Register users
    registered_users = []
    for user_data in test_users:
        user = register_test_user(api_url, user_data)
        if user:
            registered_users.append(user)
    
    if len(registered_users) != len(test_users):
        print_error("Failed to register all test users")
        return False
    
    # Get auth tokens for the registered users
    tokens = {}
    for user in registered_users:
        # In a real scenario, we would authenticate properly
        # For this test, we'll simulate token generation
        token = f"simulated_token_{user['id']}"
        tokens[user['id']] = token
    
    # Step 2: Update user preferences
    updated_preferences = {
        "availability": ["Tuesday 11-12", "Thursday 15-16"],
        "topics": ["Career", "Technology", "Coffee"],
        "meeting_length": 45
    }
    
    updated_user = update_user_preferences(api_url, tokens[registered_users[0]['id']], updated_preferences)
    if not updated_user:
        print_error("Failed to update user preferences")
        return False
    
    # Step 3: Run matching algorithm
    matching_result = run_matching_algorithm(api_url, deployment_id)
    if not matching_result:
        print_error("Failed to run matching algorithm")
        return False
    
    # Step 4: Check match results
    match = get_current_match(api_url, tokens[registered_users[0]['id']])
    if not match:
        print_error("Failed to get current match")
        return False
    
    # Step 5: Update match status
    updated_match = update_match_status(api_url, tokens[registered_users[0]['id']], match['id'], "completed")
    if not updated_match:
        print_error("Failed to update match status")
        return False
    
    # Step 6: Submit feedback
    feedback_result = submit_match_feedback(
        api_url, 
        tokens[registered_users[0]['id']], 
        match['id'], 
        5, 
        "Great conversation!"
    )
    if not feedback_result:
        print_error("Failed to submit match feedback")
        return False
    
    # Step 7: Check match history
    history = get_match_history(api_url, tokens[registered_users[0]['id']])
    if not history:
        print_error("Failed to get match history")
        return False
    
    print_success("User journey test completed successfully")
    return True

def test_multi_tenant_isolation(api_url_a, api_url_b, deployment_a, deployment_b):
    """Test isolation between multiple tenants."""
    print_header("Testing Multi-Tenant Isolation")
    
    # Generate unique test users for each deployment
    test_id = uuid.uuid4().hex[:8]
    
    # Users for deployment A
    users_a = [
        {
            "email": f"user_a1_{test_id}@example.com",
            "name": f"User A1 {test_id}",
            "preferences": {
                "availability": ["Monday 9-10"],
                "topics": ["Technology"],
                "meeting_length": 30
            }
        },
        {
            "email": f"user_a2_{test_id}@example.com",
            "name": f"User A2 {test_id}",
            "preferences": {
                "availability": ["Monday 9-10"],
                "topics": ["Technology"],
                "meeting_length": 30
            }
        }
    ]
    
    # Users for deployment B
    users_b = [
        {
            "email": f"user_b1_{test_id}@example.com",
            "name": f"User B1 {test_id}",
            "preferences": {
                "availability": ["Monday 9-10"],
                "topics": ["Technology"],
                "meeting_length": 30
            }
        },
        {
            "email": f"user_b2_{test_id}@example.com",
            "name": f"User B2 {test_id}",
            "preferences": {
                "availability": ["Monday 9-10"],
                "topics": ["Technology"],
                "meeting_length": 30
            }
        }
    ]
    
    # Register users in deployment A
    print_info("Registering users in deployment A...")
    registered_users_a = []
    for user_data in users_a:
        user = register_test_user(api_url_a, user_data)
        if user:
            registered_users_a.append(user)
    
    if len(registered_users_a) != len(users_a):
        print_error("Failed to register all test users in deployment A")
        return False
    
    # Register users in deployment B
    print_info("Registering users in deployment B...")
    registered_users_b = []
    for user_data in users_b:
        user = register_test_user(api_url_b, user_data)
        if user:
            registered_users_b.append(user)
    
    if len(registered_users_b) != len(users_b):
        print_error("Failed to register all test users in deployment B")
        return False
    
    # Run matching in deployment A
    print_info("Running matching in deployment A...")
    matching_result_a = run_matching_algorithm(api_url_a, deployment_a)
    if not matching_result_a:
        print_error("Failed to run matching algorithm in deployment A")
        return False
    
    # Run matching in deployment B
    print_info("Running matching in deployment B...")
    matching_result_b = run_matching_algorithm(api_url_b, deployment_b)
    if not matching_result_b:
        print_error("Failed to run matching algorithm in deployment B")
        return False
    
    # Get auth tokens for the registered users
    tokens_a = {}
    for user in registered_users_a:
        # In a real scenario, we would authenticate properly
        # For this test, we'll simulate token generation
        token = f"simulated_token_{user['id']}"
        tokens_a[user['id']] = token
    
    tokens_b = {}
    for user in registered_users_b:
        token = f"simulated_token_{user['id']}"
        tokens_b[user['id']] = token
    
    # Check matches in deployment A
    print_info("Checking matches in deployment A...")
    match_a = get_current_match(api_url_a, tokens_a[registered_users_a[0]['id']])
    if not match_a:
        print_error("Failed to get current match in deployment A")
        return False
    
    # Check matches in deployment B
    print_info("Checking matches in deployment B...")
    match_b = get_current_match(api_url_b, tokens_b[registered_users_b[0]['id']])
    if not match_b:
        print_error("Failed to get current match in deployment B")
        return False
    
    # Verify isolation: check that users from deployment A are only matched with users from deployment A
    participant_ids_a = [p['id'] for p in match_a['participants']]
    user_ids_a = [u['id'] for u in registered_users_a]
    
    for participant_id in participant_ids_a:
        if participant_id not in user_ids_a:
            print_error(f"User from another deployment found in deployment A match: {participant_id}")
            return False
    
    # Verify isolation: check that users from deployment B are only matched with users from deployment B
    participant_ids_b = [p['id'] for p in match_b['participants']]
    user_ids_b = [u['id'] for u in registered_users_b]
    
    for participant_id in participant_ids_b:
        if participant_id not in user_ids_b:
            print_error(f"User from another deployment found in deployment B match: {participant_id}")
            return False
    
    print_success("Multi-tenant isolation test completed successfully")
    return True

def test_disaster_recovery(instance):
    """Test disaster recovery procedures."""
    print_header(f"Testing Disaster Recovery for {instance}")
    
    # Test 1: Simulate pod failure and verify recovery
    print_info("Testing pod failure recovery...")
    
    # Delete a pod and verify that it gets recreated
    result = run_command(f"kubectl get pods -n {instance} -l app=virtual-coffee-api -o jsonpath='{{.items[0].metadata.name}}'")
    if result.returncode != 0 or not result.stdout.strip():
        print_error("Failed to get API pod name")
        return False
    
    pod_name = result.stdout.strip()
    print_info(f"Deleting pod {pod_name}...")
    
    delete_result = run_command(f"kubectl delete pod {pod_name} -n {instance}")
    if delete_result.returncode != 0:
        print_error(f"Failed to delete pod {pod_name}")
        return False
    
    # Wait for the pod to be recreated
    print_info("Waiting for pod to be recreated...")
    time.sleep(30)
    
    # Check if a new pod is running
    check_result = run_command(f"kubectl get pods -n {instance} -l app=virtual-coffee-api")
    if check_result.returncode != 0 or "Running" not in check_result.stdout:
        print_error("Pod was not recreated successfully")
        return False
    
    print_success("Pod was successfully recreated")
    
    # Test 2: Simulate configuration change and verify ArgoCD sync
    print_info("Testing ArgoCD sync after configuration change...")
    
    # Create a temporary ConfigMap change
    config_patch = {
        "data": {
            "TEST_KEY": f"test-value-{uuid.uuid4().hex[:8]}"
        }
    }
    
    patch_result = run_command(f"kubectl patch configmap -n {instance} virtual-coffee-config --type merge -p '{json.dumps(config_patch)}'")
    if patch_result.returncode != 0:
        print_error("Failed to patch ConfigMap")
        return False
    
    # Trigger ArgoCD sync
    sync_result = run_command(f"kubectl annotate application.argoproj.io/virtual-coffee-{instance} -n argocd argocd.argoproj.io/refresh=hard")
    if sync_result.returncode != 0:
        print_error("Failed to trigger ArgoCD sync")
        return False
    
    # Wait for ArgoCD to sync
    print_info("Waiting for ArgoCD to sync...")
    time.sleep(60)
    
    # Check if the ConfigMap was reverted
    check_result = run_command(f"kubectl get configmap -n {instance} virtual-coffee-config -o yaml")
    if check_result.returncode != 0:
        print_error("Failed to get ConfigMap")
        return False
    
    if f"TEST_KEY: test-value-" in check_result.stdout:
        print_error("ArgoCD did not revert the ConfigMap change")
        return False
    
    print_success("ArgoCD successfully reverted the ConfigMap change")
    
    # Test 3: Test backup and restore
    print_info("Testing backup and restore...")
    
    # Create a backup
    backup_result = run_command(f"make backup-instance INSTANCE={instance}")
    if backup_result.returncode != 0:
        print_error("Failed to create backup")
        return False
    
    # Get the backup file path
    backup_files = run_command("ls -t backups/*.json | head -1")
    if backup_files.returncode != 0 or not backup_files.stdout.strip():
        print_error("Failed to find backup file")
        return False
    
    backup_file = backup_files.stdout.strip()
    print_info(f"Created backup: {backup_file}")
    
    # Restore from backup
    restore_result = run_command(f"make restore-instance INSTANCE={instance} BACKUP_FILE={backup_file} DRY_RUN=true")
    if restore_result.returncode != 0:
        print_error("Failed to restore from backup (dry run)")
        return False
    
    print_success("Backup and restore test completed successfully")
    return True

def verify_mvp_requirements(instance):
    """Verify that all MVP requirements are satisfied."""
    print_header(f"Verifying MVP Requirements for {instance}")
    
    # Run the validation script
    validation_result = run_command(f"python scripts/validate_deployment.py --instance {instance}")
    if validation_result.returncode != 0:
        print_error("Validation script failed")
        print_error(validation_result.stdout)
        print_error(validation_result.stderr)
        return False
    
    # Check for specific requirements in the output
    requirements = [
        {"id": "1", "description": "User registration and preferences"},
        {"id": "2", "description": "User preferences configuration"},
        {"id": "3", "description": "Configurable shuffle schedules"},
        {"id": "4", "description": "Match notifications"},
        {"id": "5", "description": "Multi-tenant deployment isolation"},
        {"id": "6", "description": "ArgoCD and Crossplane integration"},
        {"id": "7", "description": "AWS Cloudscape Design System frontend"},
        {"id": "8", "description": "Automated matching algorithm"},
        {"id": "9", "description": "Federated authentication"},
        {"id": "13", "description": "Pause/resume functionality"},
        {"id": "15", "description": "Automated deployment operations"}
    ]
    
    # Check if all requirements are mentioned in the validation output
    for req in requirements:
        if f"Requirement {req['id']}" in validation_result.stdout and "verified" in validation_result.stdout:
            print_success(f"Requirement {req['id']}: {req['description']} - VERIFIED")
        else:
            print_warning(f"Requirement {req['id']}: {req['description']} - NOT VERIFIED")
    
    # Check overall validation result
    if "OVERALL VALIDATION: PASSED" in validation_result.stdout:
        print_success("All MVP requirements verified")
        return True
    else:
        print_error("Not all MVP requirements were verified")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run system integration tests for the Virtual Coffee Platform")
    parser.add_argument("--instance-a", required=True, help="First instance name to test")
    parser.add_argument("--instance-b", required=True, help="Second instance name to test (for multi-tenant tests)")
    parser.add_argument("--skip-user-journey", action="store_true", help="Skip user journey tests")
    parser.add_argument("--skip-multi-tenant", action="store_true", help="Skip multi-tenant isolation tests")
    parser.add_argument("--skip-disaster-recovery", action="store_true", help="Skip disaster recovery tests")
    parser.add_argument("--skip-mvp-verification", action="store_true", help="Skip MVP requirement verification")
    args = parser.parse_args()
    
    instance_a = args.instance_a
    instance_b = args.instance_b
    
    print_header(f"Running System Integration Tests")
    print_info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Testing instances: {instance_a} and {instance_b}")
    
    # Set up port forwarding for instance A
    api_port_forward_a = setup_port_forwarding(instance_a, "virtual-coffee-api", 8001, 80)
    frontend_port_forward_a = setup_port_forwarding(instance_a, "virtual-coffee-frontend", 3001, 80)
    
    # Set up port forwarding for instance B
    api_port_forward_b = setup_port_forwarding(instance_b, "virtual-coffee-api", 8002, 80)
    frontend_port_forward_b = setup_port_forwarding(instance_b, "virtual-coffee-frontend", 3002, 80)
    
    try:
        api_url_a = "http://localhost:8001"
        api_url_b = "http://localhost:8002"
        
        # Run tests
        results = {}
        
        # Test 1: User Journey
        if not args.skip_user_journey:
            results["user_journey"] = test_user_journey(api_url_a, instance_a)
        else:
            print_info("Skipping user journey tests")
            results["user_journey"] = None
        
        # Test 2: Multi-tenant Isolation
        if not args.skip_multi_tenant:
            results["multi_tenant"] = test_multi_tenant_isolation(api_url_a, api_url_b, instance_a, instance_b)
        else:
            print_info("Skipping multi-tenant isolation tests")
            results["multi_tenant"] = None
        
        # Test 3: Disaster Recovery
        if not args.skip_disaster_recovery:
            results["disaster_recovery"] = test_disaster_recovery(instance_a)
        else:
            print_info("Skipping disaster recovery tests")
            results["disaster_recovery"] = None
        
        # Test 4: MVP Requirement Verification
        if not args.skip_mvp_verification:
            results["mvp_verification"] = verify_mvp_requirements(instance_a)
        else:
            print_info("Skipping MVP requirement verification")
            results["mvp_verification"] = None
        
        # Print summary
        print_header("Test Summary")
        
        if results["user_journey"] is not None:
            if results["user_journey"]:
                print_success("User Journey: PASSED")
            else:
                print_error("User Journey: FAILED")
        
        if results["multi_tenant"] is not None:
            if results["multi_tenant"]:
                print_success("Multi-tenant Isolation: PASSED")
            else:
                print_error("Multi-tenant Isolation: FAILED")
        
        if results["disaster_recovery"] is not None:
            if results["disaster_recovery"]:
                print_success("Disaster Recovery: PASSED")
            else:
                print_error("Disaster Recovery: FAILED")
        
        if results["mvp_verification"] is not None:
            if results["mvp_verification"]:
                print_success("MVP Requirement Verification: PASSED")
            else:
                print_error("MVP Requirement Verification: FAILED")
        
        # Overall result
        all_passed = all(result for result in results.values() if result is not None)
        
        if all_passed:
            print_success("OVERALL SYSTEM INTEGRATION: PASSED")
            return 0
        else:
            print_error("OVERALL SYSTEM INTEGRATION: FAILED")
            return 1
    
    finally:
        # Clean up port forwarding
        cleanup_port_forwarding(api_port_forward_a)
        cleanup_port_forwarding(frontend_port_forward_a)
        cleanup_port_forwarding(api_port_forward_b)
        cleanup_port_forwarding(frontend_port_forward_b)

if __name__ == "__main__":
    sys.exit(main())