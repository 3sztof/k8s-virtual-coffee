# Virtual Coffee Platform - Installation and Setup Guide

This guide provides step-by-step instructions for installing and setting up the Virtual Coffee Platform on AWS EKS.

## Prerequisites

Before installing the Virtual Coffee Platform, ensure you have the following prerequisites:

1. **AWS Account** with appropriate permissions to create:
   - EKS clusters
   - DynamoDB tables
   - IAM roles and policies
   - SES configurations

2. **Kubernetes Cluster** running on AWS EKS (version 1.21+)
   - Minimum recommended cluster size: 3 nodes
   - Node instance type: t3.medium or larger
   - Kubernetes version: 1.21 to 1.25

3. **Required CLI Tools**:
   - `kubectl` (version 1.21+) configured to access your EKS cluster
   - `helm` (version 3.0+) for installing Kubernetes packages
   - `aws-cli` (version 2.0+) configured with appropriate credentials
   - `uv` Python package manager for development dependencies
   - `git` (version 2.0+) for repository operations

4. **Git Repository** access for storing configuration and application code

5. **Network Requirements**:
   - Outbound internet access from the EKS cluster
   - Access to AWS services (DynamoDB, SES, etc.)
   - Inbound access to the cluster for ArgoCD and application endpoints

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/virtual-coffee-platform.git
cd virtual-coffee-platform
```

### 2. Set Up Development Environment

```bash
# Install development dependencies
make setup-dev
```

This command installs all required dependencies for both the backend API and frontend application.

### 3. Install ArgoCD

ArgoCD is used for GitOps-based deployments of the Virtual Coffee Platform.

```bash
# Install and configure ArgoCD
make setup-argocd
```

After installation, you'll receive the initial admin password. Access the ArgoCD UI by running:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then visit [https://localhost:8080](https://localhost:8080) in your browser.

#### ArgoCD Configuration

After installing ArgoCD, you need to configure it to work with your Git repository:

1. Log in to the ArgoCD UI using the initial admin password
2. Go to Settings > Repositories
3. Add your Git repository with appropriate credentials
4. Verify the repository connection status

### 4. Install Crossplane

Crossplane is used to provision and manage AWS infrastructure resources.

```bash
# Install Crossplane and AWS provider
make setup-operators
```

This command installs:

- Crossplane core components
- AWS provider for Crossplane
- Required Custom Resource Definitions (CRDs)

Verify the installation by checking the status of Crossplane components:

```bash
kubectl get pods -n crossplane-system
```

### 5. Configure AWS Credentials

Configure AWS credentials for Crossplane to provision AWS resources:

```bash
# Create AWS credentials secret for Crossplane
make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret
```

The AWS credentials should have permissions for:

- DynamoDB table creation and management
- SES configuration and email sending
- IAM role and policy management

For production environments, consider using more restricted permissions based on the principle of least privilege.

### 6. Apply Crossplane Resources

Apply the Crossplane resource definitions and compositions:

```bash
# Apply Crossplane resource definitions and compositions
make apply-crossplane-resources
```

This command applies:

- Custom Resource Definitions (CRDs) for Virtual Coffee resources
- Compositions that define how to create AWS resources
- Provider configurations for AWS services

Verify that the resources were applied correctly:

```bash
kubectl get xrd
kubectl get compositions
```

### 7. Deploy Your First Instance

Deploy a new instance of the Virtual Coffee Platform:

```bash
# Deploy a new instance
make deploy-instance INSTANCE=team-a
```

This creates:

- A new namespace for the instance
- DynamoDB tables for users, matches, and configuration
- An ArgoCD application for the instance
- Backend API, frontend, and supporting services

The deployment process takes approximately 5-10 minutes to complete. You can check the status using the `check-instance-status` command.

#### Customizing the Deployment

To customize the deployment, you can create a configuration file before deploying:

```bash
# Create a custom configuration
cat <<EOF > team-a-config.yaml
apiVersion: virtualcoffee.io/v1alpha1
kind: VirtualCoffeeConfig
metadata:
  name: team-a-config
  namespace: team-a
spec:
  schedule: "0 0 * * 1"  # Every Monday at midnight
  timezone: "America/New_York"
  meetingSize: 2
  adminEmails:
    - admin@example.com
EOF

# Apply the configuration
kubectl apply -f team-a-config.yaml
```

### 8. Set Up Monitoring (Optional)

Set up monitoring for the platform using Prometheus and Grafana:

```bash
# Setup monitoring
make setup-monitoring
```

Access Grafana by running:

```bash
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
```

Default credentials:

- Username: admin
- Password: prom-operator

#### Importing Dashboards

After setting up monitoring, import the provided dashboards:

1. Log in to Grafana
2. Go to Dashboards > Import
3. Upload the dashboard JSON files from the `monitoring/dashboards` directory
4. Select the Prometheus data source
5. Click Import

## Verification

After installation, verify that all components are running correctly:

```bash
# Check instance status
make check-instance-status INSTANCE=team-a

# Check ArgoCD applications status
make check-argocd-status

# Check Crossplane resources status
make check-crossplane-status
```

For a comprehensive validation, run:

```bash
# Run comprehensive validation
make validate-deployment INSTANCE=team-a
```

This runs a series of tests to verify:

- ArgoCD application health
- AWS resource provisioning
- Configuration validation
- API functionality

### Accessing the Application

After successful deployment, access the application:

1. Get the ingress URL:
   ```bash
   kubectl get ingress -n team-a
   ```

2. Add the hostname to your local hosts file or configure DNS

3. Access the application in your browser

## Next Steps

After successful installation:

1. Configure your instance settings through the admin interface
2. Set up email notifications by configuring SES
3. Invite users to register and set their preferences
4. Configure the matching schedule for your team

For detailed usage instructions, refer to the [User Guide](user-guide.md) and [Admin Guide](admin-guide.md).

## Upgrading

To upgrade the Virtual Coffee Platform:

1. Pull the latest changes from the repository:
   ```bash
   git pull
   ```

2. Apply any database migrations (if applicable):
   ```bash
   # If there are migrations to run
   make run-migrations INSTANCE=team-a
   ```

3. Update ArgoCD applications to use the new version:
   ```bash
   make apply-crossplane-resources
   ```

4. Verify the upgrade:
   ```bash
   make validate-deployment INSTANCE=team-a
   ```

ArgoCD will automatically detect changes and sync the applications.

## Backup and Restore

### Creating Backups

To back up your instance data:

```bash
# Create a backup
make backup-instance INSTANCE=team-a
```

This creates a backup of:

- DynamoDB tables
- Configuration
- User data

Backups are stored in the `backups` directory with a timestamp.

### Restoring from Backup

To restore from a backup:

```bash
# Restore from backup
make restore-instance INSTANCE=team-a BACKUP_FILE=path/to/backup.json
```

## Uninstallation

To completely uninstall the Virtual Coffee Platform:

1. Destroy all instances:
   ```bash
   # For each instance
   make destroy-instance INSTANCE=team-a
   ```

2. Remove ArgoCD:
   ```bash
   kubectl delete namespace argocd
   ```

3. Remove Crossplane:
   ```bash
   helm uninstall crossplane -n crossplane-system
   kubectl delete namespace crossplane-system
   ```

4. Remove monitoring (if installed):
   ```bash
   kubectl delete namespace monitoring
   ```
