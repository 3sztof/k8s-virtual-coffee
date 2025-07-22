.PHONY: help setup-dev setup-api setup-frontend test-api test-frontend build-api build-frontend deploy-instance destroy-instance setup-argocd setup-operators run-api run-dynamodb-local setup-hooks install-pre-commit run-pre-commit install-crossplane setup-aws-provider create-aws-secret apply-crossplane-resources check-crossplane-status check-argocd-status check-instance-status setup-monitoring

# Help command
help:
	@echo "Virtual Coffee Platform - Makefile Commands"
	@echo ""
	@echo "Development Commands:"
	@echo "  setup-dev          Setup local development environment"
	@echo "  setup-api          Setup API development environment"
	@echo "  setup-frontend     Setup frontend development environment"
	@echo "  run-api            Run the API server locally"
	@echo "  run-dynamodb-local Run DynamoDB Local for development"
	@echo "  test-api           Run API tests"
	@echo "  test-frontend      Run frontend tests"
	@echo "  build-api          Build API Docker image"
	@echo "  build-frontend     Build frontend Docker image"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  setup-hooks        Setup git hooks for code quality checks"
	@echo "  install-pre-commit Install pre-commit hooks"
	@echo "  run-pre-commit     Run pre-commit hooks on all files"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  setup-argocd       Install and configure ArgoCD"
	@echo "  setup-operators    Install AWS infrastructure operators"
	@echo "  install-crossplane Install Crossplane on the cluster"
	@echo "  setup-aws-provider Setup AWS provider for Crossplane"
	@echo "  create-aws-secret  Create AWS credentials secret for Crossplane"
	@echo "  apply-crossplane-resources Apply Crossplane resource definitions and compositions"
	@echo "  deploy-instance    Deploy a new virtual coffee instance"
	@echo "  destroy-instance   Safely destroy an instance and resources"
	@echo ""
	@echo "Monitoring Commands:"
	@echo "  check-crossplane-status Check status of Crossplane resources"
	@echo "  check-argocd-status     Check status of ArgoCD applications"
	@echo "  check-instance-status   Check status of a specific instance"
	@echo "  setup-monitoring        Setup monitoring for the platform"
	@echo ""
	@echo "Usage Examples:"
	@echo "  make deploy-instance INSTANCE=team-a"
	@echo "  make destroy-instance INSTANCE=team-a"
	@echo "  make check-instance-status INSTANCE=team-a"
	@echo "  make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret"

# Development setup
setup-dev: setup-api setup-frontend

setup-api:
	@echo "Setting up API development environment..."
	uv pip install -e ".[dev]"

setup-frontend:
	@echo "Setting up frontend development environment..."
	cd frontend && npm install

# Testing
test-api:
	@echo "Running API tests..."
	cd backend/api && pytest --cov=. --cov-report=term-missing

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Building
build-api:
	@echo "Building API Docker image..."
	docker build -t virtual-coffee-platform/api:latest ./backend/api

build-frontend:
	@echo "Building frontend Docker image..."
	docker build -t virtual-coffee-platform/frontend:latest ./frontend

# ArgoCD setup
setup-argocd:
	@echo "Installing ArgoCD..."
	kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
	@echo "Waiting for ArgoCD to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
	@echo "Setting up ArgoCD CLI..."
	@echo "ArgoCD initial admin password:"
	kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
	@echo "\nAccess ArgoCD UI by running: kubectl port-forward svc/argocd-server -n argocd 8080:443"
	@echo "Then visit: https://localhost:8080"

# AWS operators setup
setup-operators: install-crossplane setup-aws-provider

# Crossplane installation
install-crossplane:
	@echo "Installing Crossplane..."
	kubectl create namespace crossplane-system --dry-run=client -o yaml | kubectl apply -f -
	helm repo add crossplane-stable https://charts.crossplane.io/stable
	helm repo update
	helm install crossplane --namespace crossplane-system crossplane-stable/crossplane --version 1.12.1
	@echo "Waiting for Crossplane to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/crossplane -n crossplane-system

# AWS Provider setup
setup-aws-provider:
	@echo "Setting up AWS provider for Crossplane..."
	kubectl apply -f crossplane/providers/aws-controller-config.yaml
	kubectl apply -f crossplane/providers/aws-provider.yaml
	@echo "Waiting for AWS provider to be installed..."
	kubectl wait --for=condition=healthy --timeout=300s provider.pkg.crossplane.io/provider-aws

# AWS Secret creation
create-aws-secret:
ifndef AWS_ACCESS_KEY_ID
	$(error AWS_ACCESS_KEY_ID is not set. Usage: make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret)
endif
ifndef AWS_SECRET_ACCESS_KEY
	$(error AWS_SECRET_ACCESS_KEY is not set. Usage: make create-aws-secret AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret)
endif
	@echo "Creating AWS credentials secret for Crossplane..."
	kubectl create secret generic aws-creds -n crossplane-system --from-literal=creds="[default]\naws_access_key_id=$(AWS_ACCESS_KEY_ID)\naws_secret_access_key=$(AWS_SECRET_ACCESS_KEY)" --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f - <<EOF
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-creds
      key: creds
EOF

# Apply Crossplane resources
apply-crossplane-resources:
	@echo "Applying Crossplane resource definitions and compositions..."
	kubectl apply -f crossplane/definitions/
	kubectl apply -f crossplane/compositions/
	@echo "Waiting for resource definitions to be established..."
	sleep 5
	kubectl get xrd

# Instance management
deploy-instance:
ifndef INSTANCE
	$(error INSTANCE is not set. Usage: make deploy-instance INSTANCE=team-a)
endif
	@echo "Deploying instance $(INSTANCE)..."
	# Create namespace for the instance
	kubectl create namespace $(INSTANCE) --dry-run=client -o yaml | kubectl apply -f -
	# Apply DynamoDB claim for the instance
	cat <<EOF | kubectl apply -f -
apiVersion: virtualcoffee.io/v1alpha1
kind: VirtualCoffeeDynamoDBClaim
metadata:
  name: $(INSTANCE)-dynamodb
  namespace: $(INSTANCE)
spec:
  parameters:
    region: us-west-2
    readCapacity: 5
    writeCapacity: 5
  compositionRef:
    name: virtualcoffee-dynamodb
EOF
	# Apply ArgoCD application for the instance
	sed 's/$${INSTANCE}/$(INSTANCE)/g' k8s/argocd/apps/dev-application.yaml | kubectl apply -f -
	@echo "Instance $(INSTANCE) deployment initiated. Check status with: make check-instance-status INSTANCE=$(INSTANCE)"

destroy-instance:
ifndef INSTANCE
	$(error INSTANCE is not set. Usage: make destroy-instance INSTANCE=team-a)
endif
	@echo "Destroying instance $(INSTANCE)..."
	# Delete ArgoCD application first to remove k8s resources
	kubectl delete application.argoproj.io/virtual-coffee-$(INSTANCE) -n argocd --ignore-not-found
	# Delete DynamoDB claim
	kubectl delete virtualcoffeedynamodbclaim.virtualcoffee.io/$(INSTANCE)-dynamodb -n $(INSTANCE) --ignore-not-found
	# Wait for resources to be cleaned up
	@echo "Waiting for resources to be cleaned up..."
	sleep 30
	# Delete namespace as final cleanup
	kubectl delete namespace $(INSTANCE) --ignore-not-found
	@echo "Instance $(INSTANCE) destroyed."

# Monitoring and status commands
check-crossplane-status:
	@echo "Checking Crossplane status..."
	kubectl get providers
	kubectl get xrds
	kubectl get compositions
	kubectl get managed

check-argocd-status:
	@echo "Checking ArgoCD applications status..."
	kubectl get applications -n argocd
	@echo "\nFor detailed status, use ArgoCD CLI or UI"

check-instance-status:
ifndef INSTANCE
	$(error INSTANCE is not set. Usage: make check-instance-status INSTANCE=team-a)
endif
	@echo "Checking status of instance $(INSTANCE)..."
	@echo "\nArgoCD Application:"
	kubectl get application.argoproj.io/virtual-coffee-$(INSTANCE) -n argocd -o yaml | grep -A5 status
	@echo "\nDynamoDB Resources:"
	kubectl get virtualcoffeedynamodbclaim.virtualcoffee.io/$(INSTANCE)-dynamodb -n $(INSTANCE) -o yaml | grep -A10 status
	@echo "\nPods:"
	kubectl get pods -n $(INSTANCE)
	@echo "\nServices:"
	kubectl get services -n $(INSTANCE)

setup-monitoring:
	@echo "Setting up monitoring for the platform..."
	kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring
	@echo "Monitoring setup complete. Access Grafana by running: kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80"
	@echo "Default Grafana credentials - Username: admin, Password: prom-operator"

# Code quality setup
setup-hooks: install-pre-commit
	@echo "Setting up git hooks for code quality..."
	pre-commit install

install-pre-commit:
	@echo "Installing pre-commit..."
	uv pip install pre-commit

run-pre-commit:
	@echo "Running pre-commit hooks on all files..."
	pre-commit run --all-files

# Run local development services
run-api:
	@echo "Running API server locally..."
	cd backend/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-dynamodb-local:
	@echo "Running DynamoDB Local..."
	.devcontainer/start-dynamodb-local.sh
