# Virtual Coffee Platform - Makefile Usage Guide

This document provides detailed instructions on how to use the Makefile targets for deploying and managing the Virtual Coffee Platform.

## Prerequisites

Before using the Makefile targets, ensure you have the following tools installed:

- kubectl (configured to access your Kubernetes cluster)
- helm (v3 or later)
- AWS CLI (configured with appropriate credentials)
- uv (Python package manager)

## Deployment Workflow

The typical deployment workflow follows these steps:

1. Set up ArgoCD for GitOps-based deployments
2. Install and configure Crossplane for AWS infrastructure provisioning
3. Deploy instances of the Virtual Coffee Platform
4. Monitor the status of deployments and resources

## ArgoCD Setup

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

## Crossplane Setup

Crossplane is used to provision and manage AWS infrastructure resources.

```bash
# Install Crossplane and AWS provider
make setup-operators
```

This is a composite command that runs:
- `make install-crossplane`: Installs Crossplane core components
- `make setup-aws-provider`: Installs the AWS provider for Crossplane

### AWS Credentials Configuration

To allow Crossplane to provision AWS resources, you need to provide AWS credentials:

```bash
# Create AWS credentials secret for Crossplane
make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret
```

### Apply Crossplane Resources

After setting up Crossplane and configuring AWS credentials, apply the resource definitions and compositions:

```bash
# Apply Crossplane resource definitions and compositions
make apply-crossplane-resources
```

## Instance Management

### Deploying an Instance

To deploy a new instance of the Virtual Coffee Platform:

```bash
# Deploy a new instance
make deploy-instance INSTANCE=team-a
```

This command:
- Creates a namespace for the instance
- Applies a DynamoDB claim for the instance
- Creates an ArgoCD application for the instance

### Checking Instance Status

To check the status of a deployed instance:

```bash
# Check instance status
make check-instance-status INSTANCE=team-a
```

This displays:
- ArgoCD application status
- DynamoDB resource status
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
- Deletes the DynamoDB claim
- Waits for resources to be cleaned up
- Deletes the instance namespace

## Monitoring

### Setting Up Monitoring

To set up monitoring for the platform using Prometheus and Grafana:

```bash
# Setup monitoring
make setup-monitoring
```

This installs the Prometheus Operator stack with Grafana for visualization.

### Checking Resource Status

To check the status of Crossplane resources:

```bash
# Check Crossplane status
make check-crossplane-status
```

To check the status of ArgoCD applications:

```bash
# Check ArgoCD applications status
make check-argocd-status
```

## Development Commands

For local development, the following commands are available:

```bash
# Set up development environment
make setup-dev

# Run API server locally
make run-api

# Run DynamoDB Local for development
make run-dynamodb-local

# Run tests
make test-api
make test-frontend

# Build Docker images
make build-api
make build-frontend
```

## Code Quality Commands

To ensure code quality:

```bash
# Set up git hooks for code quality checks
make setup-hooks

# Run pre-commit hooks on all files
make run-pre-commit
```

## Troubleshooting

### Common Issues

1. **ArgoCD application not syncing**
   - Check if the Git repository is accessible
   - Verify that the path to the manifests is correct
   - Check for syntax errors in the Kubernetes manifests

2. **Crossplane resources not being created**
   - Verify AWS credentials are correct
   - Check if the AWS provider is healthy
   - Look for errors in the Crossplane controller logs

3. **Instance deployment fails**
   - Check the ArgoCD application status
   - Verify that the DynamoDB claim was created successfully
   - Check for errors in the pod logs

### Getting Logs

To get logs from ArgoCD:
```bash
kubectl logs -n argocd deployment/argocd-application-controller
```

To get logs from Crossplane:
```bash
kubectl logs -n crossplane-system deployment/crossplane
```

To get logs from the AWS provider:
```bash
kubectl logs -n crossplane-system deployment/provider-aws-*
```

## Best Practices

1. Always check the status of resources after deployment
2. Use descriptive instance names that reflect their purpose
3. Clean up unused resources to avoid unnecessary costs
4. Regularly monitor the health of the platform
5. Keep AWS credentials secure and rotate them regularly