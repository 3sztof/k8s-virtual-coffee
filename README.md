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

## Development Status

- [x] Project planning and requirements
- [x] Architecture design
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
   cd backend/api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
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