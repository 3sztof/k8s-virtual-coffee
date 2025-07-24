# Virtual Coffee Platform - Operations Guide

This guide provides detailed instructions for day-to-day operations of the Virtual Coffee Platform. It covers routine tasks, maintenance procedures, and operational best practices.

## Operational Overview

The Virtual Coffee Platform consists of several components that require regular operational attention:

1. **Infrastructure Components**:
   - AWS EKS Cluster
   - DynamoDB Tables
   - SES Email Service
   - IAM Roles and Policies

2. **Kubernetes Components**:
   - ArgoCD Applications
   - Crossplane Resources
   - Application Deployments
   - Scheduled Jobs

3. **Application Components**:
   - Backend API
   - Frontend Interface
   - Matching Algorithm
   - Notification System

## Routine Operations

### Daily Operations

#### Health Checks

Perform these checks daily to ensure the platform is operating correctly:

```bash
# Check overall instance status
make check-instance-status INSTANCE=<instance>

# Check ArgoCD applications status
make check-argocd-status

# Check Crossplane resources status
make check-crossplane-status
```

#### Log Review

Review logs for errors or warnings:

```bash
# Check API logs
kubectl logs -n <instance> deployment/virtual-coffee-api --tail=100

# Check frontend logs
kubectl logs -n <instance> deployment/virtual-coffee-frontend --tail=100

# Check scheduler logs
kubectl logs -n <instance> cronjob/virtual-coffee-matching-cronjob --tail=100
```

#### Backup Verification

Verify that scheduled backups are running successfully:

```bash
# Check backup job status
kubectl get cronjob -n <instance> virtual-coffee-backup-job
kubectl get job -n <instance> -l app=virtual-coffee-backup
```

### Weekly Operations

#### Resource Utilization Review

Check resource utilization to identify potential scaling needs:

```bash
# Check pod resource usage
kubectl top pods -n <instance>

# Check node resource usage
kubectl top nodes
```

#### Security Updates

Apply security updates to the platform components:

```bash
# Update ArgoCD
make update-argocd

# Update Crossplane
make update-crossplane

# Update application components
git pull
make apply-crossplane-resources
```

#### User Activity Review

Review user activity and participation metrics:

```bash
# Access the admin dashboard
kubectl port-forward -n <instance> svc/virtual-coffee-api 8000:80
# Then navigate to http://localhost:8000/admin in your browser
```

### Monthly Operations

#### AWS Cost Review

Review AWS costs associated with the platform:

1. Log in to the AWS Management Console
2. Navigate to AWS Cost Explorer
3. Filter by tags associated with the Virtual Coffee Platform
4. Identify any unexpected cost increases

#### Performance Testing

Run performance tests to ensure the platform can handle the expected load:

```bash
# Run performance tests
make performance-test INSTANCE=<instance>
```

#### Comprehensive Validation

Run a comprehensive validation of the platform:

```bash
# Run validation with rollback tests
make validate-deployment-with-rollback INSTANCE=<instance>
```

## Maintenance Procedures

### Scaling the Platform

#### Horizontal Scaling

To add more replicas to handle increased load:

```bash
# Scale API deployment
kubectl scale deployment -n <instance> virtual-coffee-api --replicas=3

# Scale frontend deployment
kubectl scale deployment -n <instance> virtual-coffee-frontend --replicas=3
```

#### Vertical Scaling

To increase resources for components:

```bash
# Update resource limits
kubectl set resources deployment -n <instance> virtual-coffee-api --limits=cpu=1,memory=2Gi --requests=cpu=500m,memory=1Gi
```

#### DynamoDB Scaling

To adjust DynamoDB capacity:

```bash
# Update DynamoDB capacity
aws dynamodb update-table --table-name users-<instance> --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10
```

### Upgrading Components

#### Upgrading ArgoCD

```bash
# Update ArgoCD to the latest version
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

#### Upgrading Crossplane

```bash
# Update Crossplane to the latest version
helm upgrade crossplane --namespace crossplane-system crossplane-stable/crossplane
```

#### Upgrading Application Components

```bash
# Pull the latest changes
git pull

# Apply the changes
make apply-crossplane-resources
```

### Database Maintenance

#### DynamoDB Maintenance

```bash
# Check DynamoDB table status
aws dynamodb describe-table --table-name users-<instance>

# Enable point-in-time recovery
aws dynamodb update-continuous-backups --table-name users-<instance> --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

#### Data Cleanup

```bash
# Clean up old match data
kubectl exec -it -n <instance> deployment/virtual-coffee-api -- python -c "from backend.api.repositories.match_repository import MatchRepository; MatchRepository().cleanup_old_matches()"
```

## Disaster Recovery

### Backup and Restore

#### Creating Manual Backups

```bash
# Create a manual backup
make backup-instance INSTANCE=<instance>
```

#### Restoring from Backup

```bash
# Restore from backup
make restore-instance INSTANCE=<instance> BACKUP_FILE=path/to/backup.json
```

### Recovering from Failures

#### Kubernetes Cluster Failure

If the Kubernetes cluster fails:

1. Restore the EKS cluster from backup or create a new one
2. Reinstall ArgoCD and Crossplane
3. Reconnect to the Git repository
4. Redeploy the Virtual Coffee Platform instances

#### DynamoDB Failure

If DynamoDB tables are corrupted:

1. Restore from the latest backup
2. Verify data integrity
3. Reconnect the application to the restored tables

#### Application Failure

If the application components fail:

1. Check logs for errors
2. Rollback to a previous version if necessary
3. Restart the affected components
4. Verify functionality

## Monitoring and Alerting

### Prometheus and Grafana

#### Accessing Grafana

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

Then visit [http://localhost:3000](http://localhost:3000) in your browser.

Default credentials:
- Username: admin
- Password: prom-operator

#### Important Dashboards

1. **Kubernetes Cluster Overview**: General cluster health and resource usage
2. **Virtual Coffee API**: API performance and error rates
3. **DynamoDB Metrics**: Table throughput and latency
4. **Matching Algorithm**: Matching performance and success rates

#### Setting Up Alerts

Configure alerts in Grafana for:

1. High API error rates
2. DynamoDB throttling events
3. Pod restarts
4. High resource utilization

### Log Aggregation

#### Accessing Centralized Logs

If using a log aggregation solution like ELK or CloudWatch:

```bash
# For ELK
kubectl port-forward -n logging svc/kibana 5601:5601

# For CloudWatch
aws logs get-log-events --log-group-name /aws/eks/<cluster-name>/pods --log-stream-name <instance>/virtual-coffee-api
```

## Security Operations

### Credential Rotation

#### Rotating AWS Credentials

```bash
# Create new AWS credentials in the AWS console
# Then update the Crossplane secret
make create-aws-secret AWS_ACCESS_KEY_ID=new-key AWS_SECRET_ACCESS_KEY=new-secret
```

#### Rotating ArgoCD Credentials

```bash
# Update ArgoCD admin password
argocd account update-password --account admin --current-password <current-password> --new-password <new-password>
```

### Security Scanning

#### Running Security Scans

```bash
# Scan container images
make security-scan

# Scan Kubernetes resources
kubectl kube-scan

# Scan infrastructure as code
make iac-scan
```

## Multi-Tenant Operations

### Adding New Tenants

```bash
# Deploy a new instance
make deploy-instance INSTANCE=new-team
```

### Isolating Tenant Resources

Ensure proper isolation between tenants:

```bash
# Create network policies
kubectl apply -f k8s/network-policies/tenant-isolation.yaml -n <instance>

# Verify isolation
make verify-tenant-isolation INSTANCE=<instance>
```

### Tenant Cleanup

When a tenant is no longer needed:

```bash
# Destroy an instance
make destroy-instance INSTANCE=old-team
```

## Performance Tuning

### API Performance

#### Optimizing API Performance

```bash
# Update API resource limits
kubectl set resources deployment -n <instance> virtual-coffee-api --limits=cpu=1,memory=2Gi --requests=cpu=500m,memory=1Gi

# Scale API horizontally
kubectl scale deployment -n <instance> virtual-coffee-api --replicas=3
```

### DynamoDB Performance

#### Optimizing DynamoDB Performance

```bash
# Update DynamoDB capacity
aws dynamodb update-table --table-name users-<instance> --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10

# Enable DynamoDB auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/users-<instance> \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100
```

## Operational Best Practices

1. **Follow GitOps Workflow**:
   - Make all changes through Git
   - Let ArgoCD handle deployments
   - Keep the Git repository as the source of truth

2. **Regular Backups**:
   - Ensure automated backups are running
   - Periodically test backup restoration
   - Store backups in multiple locations

3. **Monitoring and Alerting**:
   - Set up alerts for critical issues
   - Regularly review monitoring dashboards
   - Adjust thresholds based on usage patterns

4. **Documentation**:
   - Keep documentation up to date
   - Document all operational procedures
   - Maintain a runbook for common issues

5. **Security**:
   - Regularly rotate credentials
   - Apply security patches promptly
   - Conduct periodic security reviews

6. **Testing**:
   - Test changes in a staging environment first
   - Run validation tests after changes
   - Perform regular disaster recovery drills

7. **Resource Management**:
   - Monitor resource usage trends
   - Scale resources proactively
   - Optimize costs without sacrificing performance

## Troubleshooting

For detailed troubleshooting procedures, refer to the [Troubleshooting Guide](troubleshooting-guide.md).

## Reference

- [Installation Guide](installation-guide.md)
- [Admin Guide](admin-guide.md)
- [User Guide](user-guide.md)
- [Makefile Usage](makefile-usage.md)
- [Deployment Validation](deployment-validation.md)
