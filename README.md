# Virtual Coffee Platform

## Overview

The Virtual Coffee Platform is a multi-tenant application that enables teams and offices to organize virtual coffee meetings through automated matching and scheduling. The platform facilitates random connections between colleagues, helping to build relationships across teams and locations.

## 🚧 Work in Progress 🚧

This project is currently under active development. Features, architecture, and implementation details may change.

## Features

- User registration and preference management
- Random matching algorithm that avoids recent pairings
- Configurable meeting sizes and schedules per deployment
- Email notifications for matches (with future support for Slack, Telegram, Signal)
- Multi-tenant architecture for isolated team/office deployments
- Federated authentication with corporate SSO and Google
- User participation toggle (pause/resume)

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with Cloudscape Design System (AWS UI components)
- **Database**: AWS DynamoDB
- **Notifications**: AWS SES (Simple Email Service)
- **Authentication**: Federated auth with AWS SSO and Google OAuth
- **Deployment**: AWS EKS (Elastic Kubernetes Service) with ArgoCD
- **Infrastructure**: AWS resources managed via Kubernetes operators
- **Documentation**: Docusaurus for comprehensive documentation site

## Project Structure

```bash
virtual-coffee-platform/
├── backend/
│   ├── api/            # Python FastAPI application
│   │   ├── auth/       # Authentication modules
│   │   ├── models/     # Pydantic data models
│   │   ├── repositories/ # Data access layer
│   │   ├── routes/     # API route handlers
│   │   ├── scheduler/  # Meeting scheduling logic
│   │   ├── services/   # Business logic services
│   │   ├── tests/      # Unit tests
│   │   └── main.py     # FastAPI application entry point
│   └── python/         # Additional Python modules
├── crossplane/         # Crossplane infrastructure definitions
│   ├── compositions/   # Resource compositions
│   ├── definitions/    # Custom resource definitions
│   └── providers/      # Provider configurations
├── docs/               # Markdown documentation files
├── docs-site/          # Docusaurus documentation site
├── frontend/           # React frontend with Cloudscape Design System
├── k8s/                # Kubernetes manifests
├── scripts/            # Utility scripts and automation
├── .devcontainer/      # Development container configuration
├── .github/            # GitHub Actions workflows
└── Makefile           # Development and deployment automation
```

## Deployment

The platform is designed to be deployed on AWS EKS using GitOps principles with ArgoCD. Each virtual coffee instance is deployed as an isolated tenant with its own resources.

Key deployment features:

- Multi-tenant isolation
- GitOps workflow with ArgoCD
- AWS infrastructure managed through Kubernetes operators
- Makefile automation for common operations

## Documentation

The Virtual Coffee Platform includes comprehensive documentation available in two formats:

1. **Markdown Documentation**: Located in the `docs/` directory, these files contain detailed guides for installation, operations, troubleshooting, and usage.

2. **Docusaurus Documentation Site**: Located in the `docs-site/` directory, this is a full-featured documentation website built with Docusaurus that can be deployed to GitHub Pages.

### Documentation Structure

The documentation is organized into three main sections:

- **User Guide**: For end users of the platform
  - Getting started
  - Setting preferences
  - Managing matches
  - Notifications
  - Troubleshooting

- **Admin Guide**: For administrators managing the platform
  - User management
  - Match administration
  - Configuration
  - Monitoring and analytics
  - Troubleshooting

- **Deployment Guide**: For DevOps engineers deploying and operating the platform
  - Installation
  - Makefile usage
  - Operations
  - Troubleshooting
  - Crossplane resources
  - Validation

### Running the Documentation Site Locally

```bash
# Install dependencies
cd docs-site
npm install

# Start the development server
npm start
```

This will start a local development server and open up a browser window. Most changes are reflected live without having to restart the server.

### Documentation Deployment

The documentation site is automatically deployed to GitHub Pages when changes are pushed to the main branch. The deployment is handled by a GitHub Actions workflow defined in `.github/workflows/documentation.yml`.

To build the site manually:

```bash
cd docs-site
npm run build
```

This command generates static content into the `build` directory that can be served using any static content hosting service.

## Development Status

- [x] Project planning and requirements
- [x] Architecture design
- [x] Infrastructure as Code
  - [x] Crossplane resource definitions and compositions
  - [x] Kubernetes manifests and overlays
  - [x] ArgoCD application configurations
- [x] Documentation
  - [x] Installation and setup guides
  - [x] User and admin documentation
  - [x] Operations and troubleshooting guides
  - [x] Docusaurus documentation site
- [x] Development Environment
  - [x] Development container configuration
  - [x] Makefile automation for common tasks
  - [x] Pre-commit hooks and code quality tools
- [ ] Backend API implementation
  - [x] Project structure and data models
  - [x] DynamoDB repository layer
  - [x] Authentication framework
  - [x] Scheduler and services structure
  - [ ] Complete API endpoints and business logic
- [ ] Frontend development
- [ ] End-to-end testing and validation

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 16+
- AWS CLI (for DynamoDB local setup)
- Docker (optional, for containerized development)
- kubectl (for Kubernetes deployment)
- Helm (for installing Kubernetes applications)

### Quick Start with Makefile

The project includes a comprehensive Makefile for common development and deployment tasks:

```bash
# Setup development environment
make setup-dev

# Run the API server locally
make run-api

# Run DynamoDB Local for development
make run-dynamodb-local

# Run tests
make test-api

# Setup code quality hooks
make setup-hooks

# Run pre-commit hooks
make run-pre-commit

# Deploy a new instance
make deploy-instance INSTANCE=team-a

# Check instance status
make check-instance-status INSTANCE=team-a

# View all available commands
make help
```

### Backend Setup

1. Set up a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies using uv:

   ```bash
   pip install uv
   uv pip install -e ".[dev]"
   ```

3. Set up local DynamoDB:

   ```bash
   # Option 1: Using Docker
   docker run -p 8000:8000 amazon/dynamodb-local

   # Option 2: Using DynamoDB Local JAR
   # Download from: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html
   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
   ```

4. Configure environment variables:

   ```bash
   # For local development
   export DYNAMODB_ENDPOINT_URL=http://localhost:8000
   export AWS_REGION=us-east-1
   ```

5. Run the API server:

   ```bash
   cd backend/api
   uvicorn main:app --reload
   ```

6. Access the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs)

### Running Tests

```bash
cd backend/api
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
