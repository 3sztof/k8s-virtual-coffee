# Virtual Coffee Platform - Crossplane Resources Guide

This guide provides detailed information about the Crossplane resources used in the Virtual Coffee Platform. It explains how AWS infrastructure is provisioned and managed through Crossplane.

## Introduction to Crossplane

Crossplane is an open-source Kubernetes add-on that enables platform teams to assemble infrastructure from multiple vendors, and expose higher-level self-service APIs for application teams to consume, without having to write any code.

In the Virtual Coffee Platform, Crossplane is used to:

1. Provision and manage AWS resources (DynamoDB tables, SES configurations, etc.)
2. Create abstractions for multi-tenant deployments
3. Implement a consistent infrastructure-as-code approach
4. Enable GitOps-based infrastructure management

## Crossplane Architecture

The Crossplane architecture in the Virtual Coffee Platform consists of:

```ascii
┌─────────────────────────────────┐
│         Kubernetes Cluster      │
│                                 │
│  ┌─────────────────────────┐    │
│  │      Crossplane Core    │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │     AWS Provider        │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │     Compositions        │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌─────────────────────────┐    │
│  │   Resource Claims       │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

## Crossplane Components

### 1. AWS Provider

The AWS Provider allows Crossplane to provision and manage AWS resources. It's configured with AWS credentials to interact with the AWS API.

**Configuration File**: `crossplane/providers/aws-provider.yaml`

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: crossplane/provider-aws:v0.24.1
```

**Controller Configuration**: `crossplane/providers/aws-controller-config.yaml`

```yaml
apiVersion: pkg.crossplane.io/v1alpha1
kind: ControllerConfig
metadata:
  name: aws-config
spec:
  podSecurityContext:
    fsGroup: 2000
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 256Mi
```

### 2. Custom Resource Definitions (CRDs)

Custom Resource Definitions define the schema for custom resources used in the Virtual Coffee Platform.

**DynamoDB Definition**: `crossplane/definitions/dynamodb-definition.yaml`

This file defines the `VirtualCoffeeDynamoDBClaim` resource, which is used to provision DynamoDB tables for a Virtual Coffee instance.

Key components:

- Schema for the claim parameters
- Validation rules
- Connection details format
- Status fields

### 3. Compositions

Compositions define how to fulfill a claim by creating and configuring AWS resources.

**DynamoDB Composition**: `crossplane/compositions/dynamodb-composition.yaml`

This composition creates:

- Users table
- Matches table
- Configuration table
- IAM role for accessing the tables
- IAM policy with appropriate permissions

Key features:

- Table naming based on instance name
- Consistent throughput configuration
- Appropriate key schema for each table
- Tags for resource tracking

## Resource Claims

Resource claims are instance-specific requests for infrastructure resources. They reference compositions and provide parameters for customization.

### DynamoDB Claim

When deploying a new instance, a DynamoDB claim is created:

```yaml
apiVersion: virtualcoffee.io/v1alpha1
kind: VirtualCoffeeDynamoDBClaim
metadata:
  name: team-a-dynamodb
  namespace: team-a
spec:
  parameters:
    region: us-west-2
    readCapacity: 5
    writeCapacity: 5
  compositionRef:
    name: virtualcoffee-dynamodb
```

This claim:

- References the `virtualcoffee-dynamodb` composition
- Specifies the AWS region
- Sets read and write capacity for the tables

## Provisioning Flow

The provisioning flow for AWS resources follows these steps:

1. A resource claim is created in a namespace
2. Crossplane's AWS provider processes the claim
3. The provider creates AWS resources according to the composition
4. Connection details are stored in a Kubernetes secret
5. The application uses the connection details to access the resources

## Managing Crossplane Resources

### Installing Crossplane

```bash
# Install Crossplane
make install-crossplane

# Setup AWS provider
make setup-aws-provider

# Create AWS credentials secret
make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret
```

### Applying Resource Definitions and Compositions

```bash
# Apply resource definitions and compositions
make apply-crossplane-resources
```

### Checking Resource Status

```bash
# Check Crossplane resources status
make check-crossplane-status

# Check specific claim status
kubectl get virtualcoffeedynamodbclaim.virtualcoffee.io/team-a-dynamodb -n team-a -o yaml
```

### Troubleshooting Crossplane Issues

If resources are not being provisioned correctly:

1. Check the AWS provider logs:
   ```bash
   kubectl logs -n crossplane-system deployment/provider-aws-*
   ```

2. Check the claim status:
   ```bash
   kubectl describe virtualcoffeedynamodbclaim.virtualcoffee.io/team-a-dynamodb -n team-a
   ```

3. Verify AWS credentials:
   ```bash
   kubectl get secret -n crossplane-system aws-creds -o yaml
   ```

4. Check for AWS service limits or errors:
   ```bash
   aws dynamodb list-tables --region us-west-2
   ```

## Best Practices

### Resource Organization

1. **Namespace Isolation**: Each instance has its own namespace
2. **Consistent Naming**: Resources follow a consistent naming pattern
3. **Resource Tagging**: All AWS resources are tagged with instance information
4. **Minimal Permissions**: IAM roles have only the necessary permissions

### Composition Design

1. **Reusability**: Compositions are designed to be reusable across instances
2. **Parameterization**: Key values are parameterized for customization
3. **Defaults**: Sensible defaults are provided for most parameters
4. **Validation**: Input validation is implemented in resource definitions

### Security Considerations

1. **Credential Management**: AWS credentials are stored securely in Kubernetes secrets
2. **Least Privilege**: IAM policies follow the principle of least privilege
3. **Resource Isolation**: Each instance has isolated AWS resources
4. **Access Control**: RBAC is used to control access to Crossplane resources

## Advanced Topics

### Custom Compositions

To create a custom composition for additional AWS resources:

1. Define the resource schema in a CRD
2. Create a composition that maps the schema to AWS resources
3. Apply the CRD and composition
4. Create claims referencing the composition

### Multi-Region Deployments

For multi-region deployments:

1. Create provider configurations for each region
2. Create compositions that reference the appropriate provider configuration
3. Create claims that specify the desired region

### Resource Deletion Protection

To protect resources from accidental deletion:

1. Add a deletion policy to the composition:
   ```yaml
   apiVersion: apiextensions.crossplane.io/v1
   kind: Composition
   metadata:
     name: virtualcoffee-dynamodb
   spec:
     compositeTypeRef:
       apiVersion: virtualcoffee.io/v1alpha1
       kind: VirtualCoffeeDynamoDBClaim
     resources:
       - name: users-table
         base:
           apiVersion: dynamodb.aws.crossplane.io/v1alpha1
           kind: Table
           spec:
             deletionPolicy: Retain  # Protects the resource from deletion
   ```

2. Implement a finalizer in the claim to handle cleanup logic

## Reference

- [Crossplane Documentation](https://crossplane.io/docs/v1.9/)
- [AWS Provider Documentation](https://doc.crds.dev/github.com/crossplane/provider-aws)
- [Composition Specification](https://crossplane.io/docs/v1.9/concepts/composition.html)
