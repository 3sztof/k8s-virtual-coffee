---
sidebar_position: 1
---

# Installation Guide

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

### 4. Install Crossplane

Crossplane is used to provision and manage AWS infrastructure resources.

```bash
# Install Crossplane and AWS provider
make setup-operators
```

### 5. Configure AWS Credentials

Configure AWS credentials for Crossplane to provision AWS resources:

```bash
# Create AWS credentials secret for Crossplane
make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret
```

### 6. Apply Crossplane Resources

Apply the Crossplane resource definitions and compositions:

```bash
# Apply Crossplane resource definitions and compositions
make apply-crossplane-resources
```

### 7. Deploy Your First Instance

Deploy a new instance of the Virtual Coffee Platform:

```bash
# Deploy a new instance
make deploy-instance INSTANCE=team-a
```

This creates a new namespace for the instance, provisions DynamoDB tables, and deploys the application components.

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

## Next Steps

After successful installation:

1. Configure your instance settings through the admin interface
2. Set up email notifications by configuring SES
3. Invite users to register and set their preferences
4. Configure the matching schedule for your team

For detailed usage instructions, refer to the [User Guide](../user-guide/introduction.md) and [Admin Guide](../admin-guide/introduction.md).