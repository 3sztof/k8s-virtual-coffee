# Design Document

## Overview

The Virtual Coffee Platform is designed as a cloud-native, multi-tenant application deployed on AWS EKS using GitOps principles. The architecture follows microservices patterns with clear separation between the Go-based backend API, frontend interface, and supporting AWS infrastructure components.

### Key Design Principles

- **Multi-tenancy**: Complete isolation between different team/office deployments
- **Cloud-native**: Kubernetes-first design leveraging AWS EKS capabilities
- **GitOps**: All infrastructure and application deployments managed through ArgoCD
- **Security**: Federated authentication with corporate SSO and Google integration
- **Scalability**: Horizontal scaling capabilities for multiple concurrent deployments
- **Simplicity**: Minimal complexity for MVP while maintaining extensibility

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "AWS EKS Cluster"
        subgraph "ArgoCD"
            AC[ArgoCD Controller]
            AW[ArgoCD Workflows]
        end
        
        subgraph "Deployment Instance A"
            FE_A[Frontend A]
            API_A[Go API A]
            SCHED_A[Scheduler A]
        end
        
        subgraph "Deployment Instance B"
            FE_B[Frontend B]
            API_B[Go API B]
            SCHED_B[Scheduler B]
        end
    end
    
    subgraph "AWS Services"
        DDB[DynamoDB Tables]
        SES[SES Email Service]
        SSO[AWS SSO]
        GOOGLE[Google OAuth]
    end
    
    subgraph "AWS Infrastructure Operators"
        DDB_OP[DynamoDB Operator]
        SES_OP[SES Operator]
    end
    
    Users --> FE_A
    Users --> FE_B
    FE_A --> API_A
    FE_B --> API_B
    API_A --> DDB
    API_B --> DDB
    API_A --> SES
    API_B --> SES
    API_A --> SSO
    API_A --> GOOGLE
    API_B --> SSO
    API_B --> GOOGLE
    
    AC --> DDB_OP
    AC --> SES_OP
    AW --> SCHED_A
    AW --> SCHED_B
```

### Deployment Architecture

Each virtual coffee deployment consists of:

1. **Frontend Application**: Simple web interface for user interactions
2. **Backend API**: Go-based REST API handling business logic
3. **Scheduler Component**: Handles matching algorithm execution
4. **Dedicated AWS Resources**: Isolated DynamoDB tables and SES configuration
5. **ArgoCD Workflow**: Manages scheduled matching operations

## Components and Interfaces

### Frontend Application

**Technology**: 
- React.js with TypeScript for type safety and developer experience
- AWS Cloudscape Design System for UI components and layout

**Key Features**:
- User registration and profile management using Cloudscape forms and input components
- Preference configuration interface with Cloudscape form components
- Participation toggle (pause/resume) using Cloudscape toggle components
- Match notification display with Cloudscape cards and status indicators
- AWS-like navigation experience with Cloudscape side navigation
- Responsive design using Cloudscape responsive layout components

**Cloudscape Components**:
- AppLayout for consistent application structure
- SideNavigation for menu navigation
- Table for displaying matches and history
- Cards for user profile and match information
- Form components for user preferences
- Alert components for notifications and errors
- Modal dialogs for confirmations
- Buttons and form controls for user interactions

**API Integration**:
- RESTful API calls to Python FastAPI backend
- JWT token-based authentication
- Status indicators for loading states and errors

### Backend Architecture

The backend uses a hybrid approach with Go for core API services and FastAPI (Python) for business logic implementation:

**Go API Layer**:
- HTTP routing and middleware using Gin framework
- Authentication and session management
- Request validation and error handling
- API endpoint implementation
- Service coordination

**Python Business Logic (FastAPI)**:
- Matching algorithm implementation
- Data analysis and processing
- Complex business rules
- Preference processing
- Exposed as internal microservice

**Core Modules**:

1. **Authentication Service (Go)**
   - Federated authentication with AWS SSO and Google OAuth
   - JWT token generation and validation
   - Session management

2. **User Service (Go)**
   - User registration and profile management
   - Preference storage and retrieval
   - Participation status management

3. **Matching Service (Python/FastAPI)**
   - Random matching algorithm implementation
   - Historical pairing tracking to avoid recent matches
   - Configurable meeting size support
   - Exposed as internal API consumed by Go services

4. **Notification Service (Go)**
   - Email template management
   - SES integration for email delivery
   - Support for multiple notification channels (email, Slack, Telegram, Signal)
   - Channel preference management
   - Retry logic and fallback mechanisms

5. **Configuration Service (Go)**
   - Deployment-specific configuration management
   - Schedule configuration
   - Time zone handling

**API Endpoints**:

```
Authentication:
POST /auth/login
POST /auth/logout
GET  /auth/me

Users:
POST /users/register
GET  /users/profile
PUT  /users/profile
PUT  /users/preferences
PUT  /users/participation

Matches:
GET  /matches/current
GET  /matches/history
POST /matches/feedback

Admin (Future):
GET  /admin/users
GET  /admin/stats
```

### Scheduler Component

**Implementation**: Kubernetes CronJob triggered by ArgoCD Workflows

**Functionality**:
- Executes matching algorithm on configured schedule
- Handles time zone calculations per deployment
- Triggers notification service after successful matching
- Logs execution results for monitoring

### AWS Infrastructure Components

**Infrastructure Deployment Approach**:
All AWS resources managed through Kubernetes operators via ArgoCD:

1. **AWS Controllers for Kubernetes (ACK)**:
   - DynamoDB tables and indexes
   - SES configurations and identities
   - Lambda functions and event sources
   - IAM roles and policies
   - Managed through GitOps workflow with ArgoCD

2. **Custom Operators (if needed)**:
   - Complex resource orchestration
   - Cross-resource dependencies
   - Deployment-specific configurations

**AWS Resources**:

**DynamoDB Tables** (per deployment):
- `users-{deployment-id}`: User profiles and preferences
- `matches-{deployment-id}`: Match history and current matches
- `config-{deployment-id}`: Deployment configuration

**Lambda Functions**:
- `matching-{deployment-id}`: Executes the matching algorithm
- `notification-{deployment-id}`: Handles email delivery
- `cleanup-{deployment-id}`: Periodic data maintenance

**SES Configuration** (per deployment):
- Dedicated email templates
- Sender identity configuration
- Bounce and complaint handling

**Aurora Serverless** (optional alternative to DynamoDB):
- Relational data storage for complex queries
- Auto-scaling based on demand
- Isolated per deployment

**IAM Roles**:
- EKS service roles with minimal required permissions
- Lambda execution roles with specific permissions
- Cross-service access policies for resource access

## Data Models

### User Model

```go
type User struct {
    ID              string    `json:"id" dynamodb:"id"`
    Email           string    `json:"email" dynamodb:"email"`
    Name            string    `json:"name" dynamodb:"name"`
    DeploymentID    string    `json:"deployment_id" dynamodb:"deployment_id"`
    Preferences     Preferences `json:"preferences" dynamodb:"preferences"`
    NotificationPrefs NotificationPreferences `json:"notification_prefs" dynamodb:"notification_prefs"`
    IsActive        bool      `json:"is_active" dynamodb:"is_active"`
    IsPaused        bool      `json:"is_paused" dynamodb:"is_paused"`
    CreatedAt       time.Time `json:"created_at" dynamodb:"created_at"`
    UpdatedAt       time.Time `json:"updated_at" dynamodb:"updated_at"`
}

type Preferences struct {
    Availability    []string  `json:"availability" dynamodb:"availability"`
    Topics          []string  `json:"topics" dynamodb:"topics"`
    MeetingLength   int       `json:"meeting_length" dynamodb:"meeting_length"`
}

type NotificationPreferences struct {
    Email           bool      `json:"email" dynamodb:"email"`
    Slack           bool      `json:"slack" dynamodb:"slack"`
    SlackWebhook    string    `json:"slack_webhook,omitempty" dynamodb:"slack_webhook,omitempty"`
    Telegram        bool      `json:"telegram" dynamodb:"telegram"`
    TelegramChatID  string    `json:"telegram_chat_id,omitempty" dynamodb:"telegram_chat_id,omitempty"`
    Signal          bool      `json:"signal" dynamodb:"signal"`
    SignalNumber    string    `json:"signal_number,omitempty" dynamodb:"signal_number,omitempty"`
    PrimaryChannel  string    `json:"primary_channel" dynamodb:"primary_channel"`
}
```

### Match Model

```go
type Match struct {
    ID              string    `json:"id" dynamodb:"id"`
    DeploymentID    string    `json:"deployment_id" dynamodb:"deployment_id"`
    Participants    []string  `json:"participants" dynamodb:"participants"`
    ScheduledDate   time.Time `json:"scheduled_date" dynamodb:"scheduled_date"`
    Status          string    `json:"status" dynamodb:"status"`
    CreatedAt       time.Time `json:"created_at" dynamodb:"created_at"`
    NotificationSent bool     `json:"notification_sent" dynamodb:"notification_sent"`
}
```

### Configuration Model

```go
type DeploymentConfig struct {
    DeploymentID    string    `json:"deployment_id" dynamodb:"deployment_id"`
    Schedule        string    `json:"schedule" dynamodb:"schedule"`
    TimeZone        string    `json:"timezone" dynamodb:"timezone"`
    MeetingSize     int       `json:"meeting_size" dynamodb:"meeting_size"`
    AdminEmails     []string  `json:"admin_emails" dynamodb:"admin_emails"`
    EmailTemplates  EmailTemplates `json:"email_templates" dynamodb:"email_templates"`
    CreatedAt       time.Time `json:"created_at" dynamodb:"created_at"`
    UpdatedAt       time.Time `json:"updated_at" dynamodb:"updated_at"`
}
```

## Error Handling

### API Error Responses

Standardized error response format:

```go
type ErrorResponse struct {
    Error   string `json:"error"`
    Code    int    `json:"code"`
    Message string `json:"message"`
    Details map[string]interface{} `json:"details,omitempty"`
}
```

### Error Categories

1. **Authentication Errors** (401): Invalid or expired tokens
2. **Authorization Errors** (403): Insufficient permissions
3. **Validation Errors** (400): Invalid input data
4. **Not Found Errors** (404): Resource not found
5. **Internal Errors** (500): System failures
6. **Service Unavailable** (503): External service failures

### Retry Logic

- **Email Notifications**: Exponential backoff with maximum 3 retries
- **Database Operations**: Circuit breaker pattern for DynamoDB
- **External Auth**: Timeout and retry for SSO/OAuth services

## Testing Strategy

### Unit Testing

**Go Backend**:
- Service layer unit tests with mocked dependencies
- HTTP handler tests using httptest package
- Data model validation tests
- Matching algorithm tests with various scenarios

**Frontend**:
- Component unit tests using Jest and React Testing Library
- API integration tests with mocked backend
- User interaction flow tests

### Integration Testing

**API Integration**:
- End-to-end API tests against test DynamoDB tables
- Authentication flow tests with test OAuth providers
- Email notification tests with SES sandbox

**Infrastructure Testing**:
- ArgoCD deployment validation
- Kubernetes resource creation tests
- AWS resource provisioning tests

### Load Testing

**Performance Targets**:
- API response time: < 200ms for 95th percentile
- Concurrent users: Support 100 active users per deployment
- Matching algorithm: Complete within 30 seconds for 500 users

## Security Considerations

### Authentication Security

- JWT tokens with short expiration (15 minutes)
- Refresh token rotation
- Secure cookie handling for session management
- HTTPS enforcement for all communications

### Data Security

- Encryption at rest for DynamoDB tables
- Encryption in transit for all API communications
- PII data minimization in logs
- Regular security scanning of container images

### Multi-tenant Isolation

- Deployment-scoped data access controls
- Network policies for pod-to-pod communication
- Resource quotas per deployment namespace
- Audit logging for cross-deployment access attempts

## Deployment Strategy

### Makefile Automation

**Core Makefile Targets**:

```makefile
# Platform Setup
make setup-argocd          # Install and configure ArgoCD
make setup-secrets         # Configure ArgoCD repository secrets
make setup-operators       # Install AWS infrastructure operators

# Instance Management  
make deploy INSTANCE=team-a    # Deploy new virtual coffee instance
make destroy INSTANCE=team-a   # Safely destroy instance and resources
make config INSTANCE=team-a    # Update instance configuration

# Development
make dev-setup             # Setup local development environment
make build                 # Build application containers
make test                  # Run test suite

# Monitoring
make status                # Check all deployments status
make logs INSTANCE=team-a  # View instance logs
```

**Automation Features**:
- **ArgoCD Bootstrap**: Automated installation and initial configuration
- **Secret Management**: Secure handling of repository credentials and AWS keys
- **Resource Provisioning**: Automated AWS resource creation via operators
- **Configuration Validation**: Pre-deployment validation of instance configs
- **Cleanup Operations**: Safe resource removal with confirmation prompts

### GitOps Workflow

1. **Platform Bootstrap**: `make setup-argocd` initializes the platform
2. **Instance Deployment**: `make deploy INSTANCE=name` creates new deployments
3. **Infrastructure Changes**: Committed to infrastructure repository
4. **ArgoCD Sync**: Automatically applies infrastructure changes
5. **Application Changes**: Committed to application repository
6. **Container Build**: CI/CD pipeline builds and pushes images
7. **ArgoCD Application Sync**: Deploys new application versions

### Environment Progression

1. **Development**: Single deployment for testing (`make dev-setup`)
2. **Staging**: Multi-deployment testing environment
3. **Production**: Isolated production deployments per team/office

### Rollback Strategy

- ArgoCD automatic rollback on deployment failures
- Database migration rollback procedures
- Blue-green deployment for zero-downtime updates
- `make rollback INSTANCE=name` for manual rollback operations