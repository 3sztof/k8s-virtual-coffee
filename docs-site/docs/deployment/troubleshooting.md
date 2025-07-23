---
sidebar_position: 4
---

# Troubleshooting Guide

This guide provides solutions for common issues you might encounter when deploying and operating the Virtual Coffee Platform.

## Diagnosing Issues

When troubleshooting the Virtual Coffee Platform, follow these general steps:

1. **Identify the affected component**:
   - Infrastructure (Crossplane, AWS resources)
   - Deployment (ArgoCD, Kubernetes resources)
   - Application (API, Frontend)
   - Networking (Ingress, Services)
   - Authentication (OAuth, JWT)

2. **Check logs and status**:
   - Use the appropriate Makefile targets to check status
   - Examine logs from the affected components
   - Look for error messages and exceptions
   - Check event logs for Kubernetes resources

3. **Verify configuration**:
   - Check that environment variables are correctly set
   - Verify that AWS credentials are valid
   - Ensure that Kubernetes resources are properly configured
   - Validate configuration files for syntax errors

4. **Isolate the problem**:
   - Determine if the issue is specific to one instance or affects all instances
   - Check if the issue is reproducible or intermittent
   - Identify any recent changes that might have caused the issue
   - Test with minimal configuration to eliminate variables

## Common Issues and Solutions

### Infrastructure Issues

#### AWS Credentials Issues

**Symptoms**:
- Crossplane resources remain in "Creating" state
- Error messages about AWS authentication failures
- AWS provider shows "Unhealthy" status
- Error logs containing "AccessDenied" or "InvalidClientTokenId"

**Solutions**:
1. Verify that AWS credentials are correct:
   ```bash
   aws sts get-caller-identity
   ```

2. Check AWS credential expiration:
   ```bash
   aws sts get-caller-identity --query 'Credentials.Expiration'
   ```

3. Recreate the AWS credentials secret:
   ```bash
   make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret
   ```

4. Check that the AWS provider is healthy:
   ```bash
   kubectl get providers
   kubectl describe provider.pkg.crossplane.io/provider-aws
   ```

5. Verify IAM permissions:
   ```bash
   aws iam get-user
   aws iam list-attached-user-policies --user-name <username>
   ```

6. Restart the AWS provider:
   ```bash
   kubectl rollout restart deployment -n crossplane-system provider-aws-*
   ```

#### DynamoDB Table Creation Failures

**Symptoms**:
- DynamoDB tables not being created
- Resource claims stuck in "Creating" state
- Error messages about throughput or quota limits
- Timeout errors during resource creation

**Solutions**:
1. Check the Crossplane controller logs:
   ```bash
   kubectl logs -n crossplane-system deployment/crossplane
   kubectl logs -n crossplane-system deployment/provider-aws-*
   ```

2. Verify that the AWS region is accessible:
   ```bash
   aws dynamodb list-tables --region us-west-2
   ```

3. Check for AWS service quotas or limits:
   ```bash
   aws service-quotas get-service-quota --service-code dynamodb --quota-code L-F98FE922
   ```

4. Verify table doesn't already exist (name conflict):
   ```bash
   aws dynamodb describe-table --table-name users-<instance> --region us-west-2
   ```

5. Delete and recreate the resource claim:
   ```bash
   kubectl delete virtualcoffeedynamodbclaim.virtualcoffee.io/<instance>-dynamodb -n <instance>
   make deploy-instance INSTANCE=<instance>
   ```

6. Check for resource definition issues:
   ```bash
   kubectl get xrd
   kubectl describe xrd virtualcoffeedynamodbclaims.virtualcoffee.io
   ```

### Deployment Issues

#### ArgoCD Application Not Syncing

**Symptoms**:
- ArgoCD application shows "OutOfSync" status
- Resources not being deployed
- Error messages in ArgoCD UI
- Sync operations failing

**Solutions**:
1. Check the ArgoCD application status:
   ```bash
   kubectl describe application.argoproj.io/virtual-coffee-<instance> -n argocd
   ```

2. Verify that the Git repository is accessible:
   ```bash
   kubectl get secret -n argocd argocd-repo-*
   kubectl logs -n argocd deployment/argocd-repo-server
   ```

3. Check for syntax errors in Kubernetes manifests:
   ```bash
   kubectl logs -n argocd deployment/argocd-application-controller | grep -i error
   ```

4. Verify the application path in the Git repository:
   ```bash
   kubectl get application.argoproj.io/virtual-coffee-<instance> -n argocd -o jsonpath='{.spec.source.path}'
   ```

5. Check for network connectivity issues:
   ```bash
   kubectl exec -it -n argocd deployment/argocd-repo-server -- ping github.com
   ```

6. Force a sync operation:
   ```bash
   kubectl patch application.argoproj.io/virtual-coffee-<instance> -n argocd --type merge -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
   ```

7. Refresh the application:
   ```bash
   kubectl annotate application.argoproj.io/virtual-coffee-<instance> -n argocd argocd.argoproj.io/refresh="hard"
   ```

8. Check for RBAC issues:
   ```bash
   kubectl auth can-i get deployments -n <instance> --as system:serviceaccount:argocd:argocd-application-controller
   ```

#### Pods Not Starting

**Symptoms**:
- Pods stuck in "Pending" or "CrashLoopBackOff" state
- Services not available
- Error events in pod description
- Container startup failures

**Solutions**:
1. Check pod status and events:
   ```bash
   kubectl get pods -n <instance>
   kubectl describe pod -n <instance> <pod-name>
   ```

2. Check for resource constraints:
   ```bash
   kubectl describe nodes | grep -A 5 "Allocated resources"
   kubectl top nodes
   ```

3. Check for node taints or affinity issues:
   ```bash
   kubectl get nodes -o json | jq '.items[].spec.taints'
   kubectl describe pod -n <instance> <pod-name> | grep -A 5 "Tolerations"
   ```

4. Check pod logs:
   ```bash
   kubectl logs -n <instance> <pod-name>
   # For previous container instances
   kubectl logs -n <instance> <pod-name> --previous
   ```

5. Check for image pull issues:
   ```bash
   kubectl describe pod -n <instance> <pod-name> | grep -A 5 "Events"
   ```

6. Verify that ConfigMaps and Secrets are correctly mounted:
   ```bash
   kubectl describe pod -n <instance> <pod-name> | grep -A 10 "Volumes"
   ```

7. Check for PersistentVolume issues:
   ```bash
   kubectl get pv,pvc -n <instance>
   ```

8. Verify network policies:
   ```bash
   kubectl get networkpolicies -n <instance>
   ```

9. For CrashLoopBackOff, check container exit codes:
   ```bash
   kubectl get pod -n <instance> <pod-name> -o json | jq '.status.containerStatuses[].lastState.terminated.exitCode'
   ```

### Application Issues

#### API Errors

**Symptoms**:
- API returning 5xx errors
- Frontend unable to connect to API

**Solutions**:
1. Check API logs:
   ```bash
   kubectl logs -n <instance> deployment/virtual-coffee-api
   ```

2. Verify that environment variables are correctly set:
   ```bash
   kubectl describe deployment -n <instance> virtual-coffee-api | grep -A 20 "Environment"
   ```

3. Check that DynamoDB tables are accessible:
   ```bash
   kubectl exec -it -n <instance> deployment/virtual-coffee-api -- python -c "from backend.api.repositories.dynamodb_connection import get_dynamodb_client; print(get_dynamodb_client().list_tables())"
   ```

4. Restart the API deployment:
   ```bash
   kubectl rollout restart deployment -n <instance> virtual-coffee-api
   ```

#### Authentication Issues

**Symptoms**:
- Users unable to log in
- Authentication errors in logs

**Solutions**:
1. Check authentication service logs:
   ```bash
   kubectl logs -n <instance> deployment/virtual-coffee-api | grep -i auth
   ```

2. Verify OAuth configuration:
   ```bash
   kubectl get configmap -n <instance> virtual-coffee-config -o yaml | grep -A 10 "oauth"
   ```

3. Check JWT token validation:
   ```bash
   kubectl exec -it -n <instance> deployment/virtual-coffee-api -- python -c "from backend.api.auth.jwt import decode_token; print(decode_token('your-token'))"
   ```

#### Matching Algorithm Issues

**Symptoms**:
- Matches not being created
- Scheduler errors

**Solutions**:
1. Check scheduler logs:
   ```bash
   kubectl logs -n <instance> job/virtual-coffee-matching-job
   ```

2. Verify that there are active users:
   ```bash
   kubectl exec -it -n <instance> deployment/virtual-coffee-api -- python -c "from backend.api.repositories.user_repository import UserRepository; print(UserRepository().get_active_users())"
   ```

3. Check matching service configuration:
   ```bash
   kubectl get configmap -n <instance> virtual-coffee-config -o yaml | grep -A 10 "matching"
   ```

4. Manually trigger the matching process:
   ```bash
   kubectl create job --from=cronjob/virtual-coffee-matching-cronjob -n <instance> manual-matching
   ```

## Recovery Procedures

### Rollback to Previous Version

If a deployment causes issues, roll back to a previous version:

```bash
# Get ArgoCD application history
kubectl get application.argoproj.io/virtual-coffee-<instance> -n argocd -o jsonpath='{.status.history}'

# Rollback to a specific revision
kubectl patch application.argoproj.io/virtual-coffee-<instance> -n argocd --type merge -p '{"spec":{"source":{"targetRevision":"<previous-commit-hash>"}}}'
```

### Recreate DynamoDB Tables

If DynamoDB tables are corrupted or need to be recreated:

1. Export data if needed:
   ```bash
   aws dynamodb scan --table-name users-<instance> --region us-west-2 > users-backup.json
   ```

2. Delete and recreate the resource claim:
   ```bash
   kubectl delete virtualcoffeedynamodbclaim.virtualcoffee.io/<instance>-dynamodb -n <instance>
   make deploy-instance INSTANCE=<instance>
   ```

3. Import data if needed (requires custom script).

### Reset User Passwords

If users are unable to log in due to authentication issues:

1. For AWS SSO users, reset through the AWS SSO console.

2. For Google OAuth users, they should use the "Forgot Password" feature on Google.

## Monitoring and Diagnostics

### Checking System Health

Use the following commands to check the health of the system:

```bash
# Check overall instance status
make check-instance-status INSTANCE=<instance>

# Check ArgoCD applications status
make check-argocd-status

# Check Crossplane resources status
make check-crossplane-status

# Run comprehensive validation
make validate-deployment INSTANCE=<instance>
```

### Collecting Diagnostic Information

To collect diagnostic information for troubleshooting:

```bash
# Create a diagnostic bundle
mkdir -p diagnostics
kubectl get all -n <instance> > diagnostics/resources.txt
kubectl describe pods -n <instance> > diagnostics/pods.txt
kubectl logs -n <instance> deployment/virtual-coffee-api > diagnostics/api-logs.txt
kubectl logs -n <instance> deployment/virtual-coffee-frontend > diagnostics/frontend-logs.txt
kubectl get application.argoproj.io/virtual-coffee-<instance> -n argocd -o yaml > diagnostics/argocd-app.yaml
kubectl get virtualcoffeedynamodbclaim.virtualcoffee.io/<instance>-dynamodb -n <instance> -o yaml > diagnostics/dynamodb-claim.yaml
```

## Preventive Measures

To prevent issues from occurring:

1. Regularly run validation tests:
   ```bash
   make validate-deployment INSTANCE=<instance>
   ```

2. Monitor system health using Prometheus and Grafana.

3. Keep AWS credentials secure and rotate them regularly.

4. Follow the GitOps workflow for all changes.

5. Test changes in a staging environment before applying to production.

6. Regularly backup DynamoDB tables.

7. Keep the platform updated with the latest security patches.