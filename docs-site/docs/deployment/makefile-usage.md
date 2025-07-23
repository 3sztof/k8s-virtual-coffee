---
sidebar_position: 2
---

# Makefile Usage Guide

This guide provides detailed instructions on how to use the Makefile targets for deploying and managing the Virtual Coffee Platform.

## Prerequisites

Before using the Makefile targets, ensure you have the following tools installed:

- kubectl (version 1.21+, configured to access your Kubernetes cluster)
- helm (version 3.0+)
- AWS CLI (version 2.0+, configured with appropriate credentials)
- uv (Python package manager)
- git (version 2.0+)
- Python (version 3.9+)
- Docker (version 20.0+, for building images)

## Makefile Target Categories

The Makefile provides targets organized into the following categories:

1. **Development Commands**: For local development and testing
2. **Code Quality Commands**: For maintaining code quality
3. **Deployment Commands**: For deploying and managing instances
4. **Monitoring Commands**: For monitoring the platform and instances
5. **Backup and Restore Commands**: For data management
6. **Validation Commands**: For testing deployments

## Development Commands

### Setting Up Development Environment

```bash
# Setup complete development environment (API + Frontend)
make setup-dev

# Setup only API development environment
make setup-api

# Setup only frontend development environment
make setup-frontend
```

### Running Local Services

```bash
# Run the API server locally
make run-api

# Run DynamoDB Local for development
make run-dynamodb-local
```

The API server will be available at [http://localhost:8000](http://localhost:8000).

### Testing

```bash
# Run API tests
make test-api

# Run frontend tests
make test-frontend
```

The API tests include unit tests, integration tests, and end-to-end tests.

### Building

```bash
# Build API Docker image
make build-api

# Build frontend Docker image
make build-frontend
```

These commands build Docker images tagged as `virtual-coffee-platform/api:latest` and `virtual-coffee-platform/frontend:latest`.

## Code Quality Commands

### Setting Up Git Hooks

```bash
# Setup git hooks for code quality checks
make setup-hooks
```

This installs pre-commit hooks that run automatically before each commit.

### Installing Pre-commit

```bash
# Install pre-commit
make install-pre-commit
```

### Running Pre-commit Hooks

```bash
# Run pre-commit hooks on all files
make run-pre-commit
```

This checks all files for:

- Code formatting issues
- Linting errors
- Type checking issues
- Security vulnerabilities

## Deployment Commands

### ArgoCD Setup

ArgoCD is used for GitOps-based deployments of the Virtual Coffee Platform.

```bash
# Install and configure ArgoCD
make setup-argocd
```

This command:

- Creates the argocd namespace
- Installs ArgoCD components
- Displays the initial admin password
- Provides instructions for accessing the ArgoCD UI

After installation, access the ArgoCD UI by running:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then visit [https://localhost:8080](https://localhost:8080) in your browser.

### Crossplane Setup

Crossplane is used to provision and manage AWS infrastructure resources.

```bash
# Install Crossplane and AWS provider
make setup-operators
```

This is a composite command that runs:

- `make install-crossplane`: Installs Crossplane core components
- `make setup-aws-provider`: Installs the AWS provider for Crossplane

For more granular control, you can run these commands individually:

```bash
# Install only Crossplane
make install-crossplane

# Setup only the AWS provider
make setup-aws-provider
```

### AWS Credentials Configuration

To allow Crossplane to provision AWS resources, you need to provide AWS credentials:

```bash
# Create AWS credentials secret for Crossplane
make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret
```

This creates a Kubernetes secret containing the AWS credentials and configures the AWS provider to use them.

### Apply Crossplane Resources

After setting up Crossplane and configuring AWS credentials, apply the resource definitions and compositions:

```bash
# Apply Crossplane resource definitions and compositions
make apply-crossplane-resources
```

This applies:

- Custom Resource Definitions (CRDs) for Virtual Coffee resources
- Compositions that define how to create AWS resources
- Provider configurations for AWS services

## Instance Management

### Deploying an Instance

To deploy a new instance of the Virtual Coffee Platform:

```bash
# Deploy a new instance
make deploy-instance INSTANCE=team-a
```

This command:

- Creates a namespace for the instance
- Applies a DynamoDB claim for the instance (creates users, matches, and config tables)
- Creates an ArgoCD application for the instance
- Deploys the backend API, frontend, and supporting services

The deployment process takes a few minutes to complete. You can check the status using the `check-instance-status` command.

### Checking Instance Status

To check the status of a deployed instance:

```bash
# Check instance status
make check-instance-status INSTANCE=team-a
```

This displays:

- ArgoCD application status (synced/out-of-sync)
- DynamoDB resource status (ready/not ready)
- Pods running in the instance namespace
- Services available in the instance namespace

### Destroying an Instance

To safely destroy an instance and clean up all associated resources:

```bash
# Destroy an instance
make destroy-instance INSTANCE=team-a
```

This command:

- Deletes the ArgoCD application
- Deletes the DynamoDB claim (which triggers deletion of AWS resources)
- Waits for resources to be cleaned up
- Deletes the instance namespace

This process ensures that all AWS resources are properly cleaned up to avoid ongoing charges.

## Validation Commands

### Validating Deployments

To validate that a deployment is working correctly:

```bash
# Run basic deployment validation
make validate-deployment INSTANCE=team-a
```

This runs a series of tests to verify:

- ArgoCD application health
- AWS resource provisioning
- Configuration validation
- API functionality

### Testing Rollback Procedures

To test rollback procedures:

```bash
# Run deployment validation with rollback tests
make validate-deployment-with-rollback INSTANCE=team-a
```

This performs additional tests to verify that the system can recover from failures.

## Monitoring Commands

### Setting Up Monitoring

To set up monitoring for the platform using Prometheus and Grafana:

```bash
# Setup monitoring
make setup-monitoring
```

This installs the Prometheus Operator stack with Grafana for visualization.

Access Grafana by running:

```bash
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
```

Default credentials:

- Username: admin
- Password: prom-operator

### Checking Resource Status

To check the status of various components:

```bash
# Check Crossplane resources status
make check-crossplane-status

# Check ArgoCD applications status
make check-argocd-status

# Check specific instance status
make check-instance-status INSTANCE=team-a
```

## Backup and Restore Commands

### Creating Backups

To back up your instance data:

```bash
# Create a backup
make backup-instance INSTANCE=team-a
```

This creates a backup of:

- DynamoDB tables (users, matches, config)
- Configuration settings
- User data and preferences
- Match history

Backups are stored in the `backups` directory with a timestamp in the format `YYYY-MM-DD-HHMMSS`.

#### Backup Options

You can customize the backup process with additional options:

```bash
# Backup with custom output location
make backup-instance INSTANCE=team-a OUTPUT_DIR=/path/to/custom/directory

# Backup with encryption
make backup-instance INSTANCE=team-a ENCRYPT=true

# Backup specific tables only
make backup-instance INSTANCE=team-a TABLES=users,matches
```

### Restoring from Backup

To restore from a backup:

```bash
# Restore from backup
make restore-instance INSTANCE=team-a BACKUP_FILE=path/to/backup.json
```

#### Restore Options

You can customize the restore process:

```bash
# Restore with validation only (dry run)
make restore-instance INSTANCE=team-a BACKUP_FILE=path/to/backup.json DRY_RUN=true

# Restore specific tables only
make restore-instance INSTANCE=team-a BACKUP_FILE=path/to/backup.json TABLES=users,matches

# Restore with conflict resolution strategy
make restore-instance INSTANCE=team-a BACKUP_FILE=path/to/backup.json CONFLICT_STRATEGY=overwrite
```

### Scheduled Backups

To set up scheduled backups using a Kubernetes CronJob:

```bash
# Create a daily backup job
make create-backup-job INSTANCE=team-a SCHEDULE="0 0 * * *"
```

This creates a CronJob that runs daily at midnight to back up the instance data.