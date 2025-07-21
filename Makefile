.PHONY: help setup-dev setup-api setup-frontend test-api test-frontend build-api build-frontend deploy-instance destroy-instance setup-argocd setup-operators run-api run-dynamodb-local

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
	@echo "Deployment Commands:"
	@echo "  setup-argocd       Install and configure ArgoCD"
	@echo "  setup-operators    Install AWS infrastructure operators"
	@echo "  deploy-instance    Deploy a new virtual coffee instance"
	@echo "  destroy-instance   Safely destroy an instance and resources"
	@echo ""
	@echo "Usage Examples:"
	@echo "  make deploy-instance INSTANCE=team-a"
	@echo "  make destroy-instance INSTANCE=team-a"

# Development setup
setup-dev: setup-api setup-frontend

setup-api:
	@echo "Setting up API development environment..."
	cd backend/api && pip install -r requirements.txt

setup-frontend:
	@echo "Setting up frontend development environment..."
	cd frontend && npm install

# Testing
test-api:
	@echo "Running API tests..."
	cd backend/api && pytest

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
	@echo "Setting up ArgoCD (placeholder)..."
	# This would contain actual ArgoCD installation and configuration

# AWS operators setup
setup-operators:
	@echo "Setting up AWS operators (placeholder)..."
	# This would contain actual operator installation commands

# Instance management
deploy-instance:
ifndef INSTANCE
	$(error INSTANCE is not set. Usage: make deploy-instance INSTANCE=team-a)
endif
	@echo "Deploying instance $(INSTANCE)..."
	# This would contain actual deployment commands

destroy-instance:
ifndef INSTANCE
	$(error INSTANCE is not set. Usage: make destroy-instance INSTANCE=team-a)
endif
	@echo "Destroying instance $(INSTANCE)..."
	# This would contain actual cleanup commands