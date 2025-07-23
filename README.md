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

## Project Structure

```bash
virtual-coffee-platform/
├── backend/
│   └── api/            # Python FastAPI application
│       ├── models/     # Pydantic data models
│       ├── repositories/ # Data access layer
│       └── tests/      # Unit tests
├── docs/               # Markdown documentation files
├── docs-site/          # Docusaurus documentation site
├── frontend/           # React frontend with Cloudscape Design System
├── k8s/
│   ├── base/           # Base Kubernetes manifests
│   └── overlays/       # Environment-specific overlays
└── scripts/            # Utility scripts and automation
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

### Documentation Site

The documentation site is organized into three main sections:

- **User Guide**: For end users of the platform
- **Admin Guide**: For administrators managing the platform
- **Deployment**: For DevOps engineers deploying and operating the platform

#### Running the Documentation Site Locally

```bash
# Install dependencies
cd docs-site
npm install

# Start the development server
npm start
```

This will start a local development server and open up a browser window. Most changes are reflected live without having to restart the server.

#### Building and Deploying

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
- [x] Documentation
  - [x] Installation and setup guides
  - [x] User and admin documentation
  - [x] Operations and troubleshooting guides
  - [x] Docusaurus documentation site
- [ ] Backend API implementation
  - [x] Data models (User, Match, Configuration)
  - [x] DynamoDB repository layer
  - [ ] API endpoints and business logic
  - [ ] Authentication and authorization
- [ ] Frontend development
- [ ] Infrastructure automation
- [ ] Deployment and testing

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- AWS CLI (for DynamoDB local setup)
- Docker (optional, for containerized development)

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

6. Access the API documentation at http://localhost:8000/docs

### Running Tests

```bash
cd backend/api
pytest
```

## License

*License information to be determined*