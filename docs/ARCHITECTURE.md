# Expense Tracker — Backend Architecture

Version: 1.0  
Status: MVP  
Backend: FastAPI  
Database: Supabase PostgreSQL  
ORM: SQLAlchemy 2.x  
Migrations: Alembic  
Authentication: JWT Access Token + Refresh Token  
Deployment: Docker + Vercel-compatible deployment

## 1. Purpose

This document defines the internal architecture of the Expense Tracker backend.

The architecture must:

- Keep business logic separate from HTTP handling.
- Keep database access separate from business logic.
- Make authentication and authorization explicit.
- Support automated testing.
- Support Docker-based deployment.
- Allow the backend to evolve without coupling the Expo application to internal implementation details.

Related documents:

```text
docs/BACKEND_PRD.md
docs/DATABASE_SCHEMA.md
docs/API_SPEC.md
```

## 2. High-Level Architecture

```text
React Native / Expo
        │
       HTTPS
        ↓
     FastAPI
        ↓
 Dependencies
(Auth / DB / Context)
        ↓
 Service Layer
(Business Logic)
        ↓
 Repository Layer
(Data Access)
        ↓
Supabase PostgreSQL
```

## 3. Architectural Layers

### API / Router Layer

Responsible for:

- HTTP endpoints
- Request parsing
- Authentication dependency integration
- Calling services
- Response schemas
- HTTP status codes

Routers must not contain complex business logic.

### Service Layer

Contains application and business logic.

Recommended services:

```text
AuthService
AccountService
CategoryService
TransactionService
BudgetService
RecurringTransactionService
DashboardService
ReportService
NotificationService
GamificationService
```

Services handle:

- Business rules
- Cross-repository operations
- Financial calculations
- Authorization-related business rules
- Related domain behavior
- Transaction boundaries where appropriate

### Repository Layer

Repositories isolate database access.

Recommended repositories:

```text
UserRepository
RefreshTokenRepository
AccountRepository
CategoryRepository
TransactionRepository
BudgetRepository
RecurringTransactionRepository
NotificationRepository
StreakRepository
AchievementRepository
```

Repositories handle:

- Queries
- Inserts
- Updates
- Deletes/deactivation
- Filtering
- Pagination
- Aggregations where appropriate

Repositories must not contain HTTP-specific behavior.

## 4. Recommended Project Structure

```text
expense-tracker-backend/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── accounts.py
│   │       ├── categories.py
│   │       ├── transactions.py
│   │       ├── budgets.py
│   │       ├── recurring_transactions.py
│   │       ├── dashboard.py
│   │       ├── reports.py
│   │       ├── notifications.py
│   │       └── gamification.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── constants.py
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── utils/
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│
├── docs/
│   ├── BACKEND_PRD.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_SPEC.md
│   └── ARCHITECTURE.md
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
├── .gitignore
└── README.md
```

Do not create every file blindly at initialization. Create files as their feature is implemented.

## 5. Database Layer

Use:

```text
SQLAlchemy 2.x
asyncpg
Alembic
PostgreSQL
```

Use SQLAlchemy models for persistence.

Use Pydantic schemas for API input/output.

Do not expose SQLAlchemy ORM objects directly as the API contract.

## 6. Dependency Injection

Use FastAPI dependencies for:

- Database sessions
- Current authenticated user
- Shared request dependencies

Protected endpoints should use:

```python
current_user: User = Depends(get_current_user)
```

## 7. Authentication Architecture

MVP authentication:

```text
Email
+
Password
+
JWT Access Token
+
Refresh Token
```

No social login in MVP.

Future:

```text
Google
Apple
```

Passwords must never be stored directly. Use Argon2id.

### JWT

Use short-lived access tokens with only necessary claims:

```text
sub
iat
exp
type
```

Do not store sensitive user information inside JWT claims.

### Refresh Tokens

Refresh tokens are long-lived sessions stored as hashes in the database.

They must be:

- Expirable
- Revocable
- Associated with a user

Logout revokes the corresponding refresh-token session.

## 8. Authorization

Every protected query must be scoped to the authenticated user.

Correct:

```python
repository.get_by_id(
    resource_id,
    user_id=current_user.id,
)
```

Do not fetch a resource globally and assume it is safe.

User ownership is a mandatory security boundary.

## 9. Financial Transaction Architecture

Creating an expense:

```text
HTTP Request
     ↓
Transaction Router
     ↓
Transaction Service
     ↓
Validate User
     ↓
Validate Account Ownership
     ↓
Validate Category Ownership
     ↓
Validate Amount
     ↓
BEGIN DATABASE TRANSACTION
     ↓
Create Transaction
     ↓
Update Account Balance
     ↓
Update Budget State
     ↓
Update Streak/Gamification
     ↓
COMMIT
```

Any failure must roll back the operation.

### Transaction Update

If an update changes amount, type, or account:

```text
BEGIN
 ↓
Reverse old financial effect
 ↓
Validate new account/category
 ↓
Apply new financial effect
 ↓
Update transaction
 ↓
Recalculate dependent state
 ↓
COMMIT
```

### Transaction Delete

```text
BEGIN
 ↓
Find transaction
 ↓
Verify ownership
 ↓
Reverse financial effect
 ↓
Delete/deactivate transaction
 ↓
Recalculate dependent state
 ↓
COMMIT
```

## 10. Money Handling

Use Python:

```python
Decimal
```

and PostgreSQL:

```text
NUMERIC(14,2)
```

Never use floating-point arithmetic for authoritative financial calculations.

## 11. Date and Time

Use timezone-aware Python datetimes.

Database:

```text
TIMESTAMPTZ
```

Internal representation:

```text
UTC
```

API timestamps use ISO 8601.

## 12. Pydantic Schemas

Keep API schemas separate from database models.

Examples:

```text
TransactionCreate
TransactionUpdate
TransactionResponse
TransactionListResponse
TransactionFilter
```

Do not expose SQLAlchemy models directly.

## 13. Dashboard

The backend calculates authoritative:

- Total balance
- Income
- Expenses
- Net savings
- Savings percentage
- Budget summary
- Top categories
- Spending trend
- Recent transactions
- Tracking streak

The mobile app displays the response and should not independently calculate authoritative financial values.

## 14. Reports

Use database aggregation where practical:

```text
SUM(amount)
GROUP BY category
GROUP BY date
GROUP BY account
```

Avoid fetching large transaction datasets into Python merely for basic SQL aggregation.

## 15. Budget Architecture

Budget spending is derived from transactions.

The backend is authoritative for:

```text
spent
remaining
percentage_used
status
```

The frontend should not independently determine authoritative budget status.

## 16. Gamification

Gamification is triggered by backend business operations.

Example:

```text
Transaction created
        ↓
GamificationService
        ↓
Update streak
        ↓
Check achievements
        ↓
Unlock achievement if eligible
        ↓
Create notification
```

The mobile app cannot directly unlock achievements.

## 17. Notifications

Notifications are generated by backend events such as:

```text
Budget warning
Budget exceeded
Achievement unlocked
Recurring transaction
Monthly summary
Tracking reminder
```

The client must not generate authoritative financial notifications.

## 18. Recurring Transactions

Recurring definitions contain:

```text
frequency
start_date
next_occurrence
end_date
is_active
```

Processing:

```text
Find active records
where next_occurrence <= today
        ↓
Create transaction
        ↓
Update next_occurrence
        ↓
Commit atomically
```

Processing must be idempotent.

Do not build an always-running background process unless the deployment platform reliably supports it.

## 19. Database Sessions

Use request-scoped database sessions where appropriate.

Conceptually:

```text
Request
  ↓
get_db()
  ↓
Database Session
  ↓
Router
  ↓
Service
  ↓
Repository
  ↓
Commit / Rollback
  ↓
Close Session
```

Financial multi-step operations must share the same transaction/session boundary.

## 20. Error Handling

Create application-specific exceptions:

```text
AuthenticationError
AuthorizationError
ResourceNotFoundError
ConflictError
ValidationError
FinancialOperationError
```

Map these to the standard API error format defined in `API_SPEC.md`.

Never expose stack traces, SQL errors, or infrastructure details to clients.

## 21. Configuration

Configuration must come from environment variables.

Recommended:

```env
DATABASE_URL=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ORIGINS=
ENVIRONMENT=development
```

Never commit secrets.

## 22. CORS

Development may allow the required Expo development origins.

Production must use an explicit allowlist.

Do not use unrestricted origins for authenticated production APIs without a deliberate security reason.

## 23. Docker

The backend must be containerizable.

Conceptually:

```text
Docker Container
┌─────────────────────────────┐
│ FastAPI                     │
│ Uvicorn / ASGI server       │
│ Application code            │
│ Python dependencies         │
└──────────────┬──────────────┘
               │
               ↓
       Supabase PostgreSQL
```

The database is external and must not run inside the production application container.

The container should:

- Use a maintained Python base image.
- Install dependencies reproducibly.
- Run as non-root where practical.
- Exclude development-only tooling from production.
- Respect the deployment platform's `PORT`.

## 24. Docker Compose

`docker-compose.yml` is for local development.

It may run FastAPI while using Supabase PostgreSQL externally.

A local PostgreSQL container is optional.

## 25. Deployment

Target architecture:

```text
Expo Mobile App
        │
       HTTPS
        ▼
FastAPI Docker Deployment
        │
        ▼
Supabase PostgreSQL
```

If a serverless deployment is used, recurring jobs and long-running processes must be designed specifically for that platform.

## 26. Health Check

Provide:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

A separate readiness check may be added when deployment infrastructure requires it.

## 27. Logging

Use structured logging where practical.

Useful fields:

```text
timestamp
level
request_id
route
status_code
duration
```

Never log:

- Passwords
- Access tokens
- Refresh tokens
- JWT secrets
- Database credentials
- Sensitive personal data unnecessarily

## 28. Testing Architecture

Use three levels:

```text
Unit Tests
    ↓
Business logic

Integration Tests
    ↓
Database + repositories + services

API Tests
    ↓
FastAPI endpoints
```

Critical financial behavior must have automated tests.

Test at minimum:

```text
Password hashing
JWT validation
Money calculations
Budget calculations
Savings calculation
Streak calculation
Recurring date calculation
Transaction financial effects
User ownership
Account balance updates
Refresh token revocation
```

## 29. Security Tests

Verify:

```text
User A cannot access User B's accounts.
User A cannot access User B's transactions.
User A cannot modify User B's budgets.
Invalid JWT is rejected.
Expired JWT is rejected.
Revoked refresh token is rejected.
Inactive user cannot authenticate.
Invalid account ownership is rejected.
Invalid category ownership is rejected.
```

## 30. API Documentation

FastAPI must expose:

```text
/docs
/redoc
/openapi.json
```

Every endpoint should document:

- Summary
- Description
- Authentication
- Request schema
- Response schema
- Error responses
- Query parameters

## 31. Dependency Management

Use:

```text
pyproject.toml
```

Core dependencies include compatible versions of:

```text
fastapi
uvicorn
sqlalchemy
asyncpg
alembic
pydantic
pydantic-settings
argon2
pyjwt
pytest
httpx
```

Use current stable compatible versions when implementation begins.

## 32. Architecture Rules

1. Routers do not contain business logic.
2. Services do not depend on HTTP request objects.
3. Repositories do not depend on FastAPI.
4. Database models are not API schemas.
5. Financial calculations use `Decimal`.
6. All user-owned resources are user-scoped.
7. Financial mutations are atomic.
8. Authentication secrets come from environment variables.
9. No secrets are committed.
10. API versioning is mandatory.
11. Business logic must have tests.
12. Do not introduce unnecessary abstractions.
13. Do not add future features unless explicitly requested.
14. Do not change the API contract silently.
15. Database schema changes require Alembic migrations.

## 33. Avoid Over-Engineering

For the MVP, do not introduce:

- Microservices
- Kubernetes
- Event buses
- Redis without a concrete requirement
- Kafka
- Complex CQRS
- GraphQL
- Multiple databases
- Excessive generic base classes
- Complex domain-event infrastructure

Keep the architecture modular but simple.

## 34. Dependency Direction

```text
API
 ↓
Services
 ↓
Repositories
 ↓
Database
```

Supporting dependencies:

```text
API → Schemas
Services → Schemas / Domain logic
Repositories → DB models
Core → Shared infrastructure
```

Avoid circular dependencies.

## 35. Feature Implementation Pattern

Implement each feature generally in this order:

```text
1. Database Model
        ↓
2. Alembic Migration
        ↓
3. Repository
        ↓
4. Pydantic Schemas
        ↓
5. Service
        ↓
6. API Router
        ↓
7. Tests
        ↓
8. OpenAPI Verification
```

## 36. Recommended Development Order

```text
Phase 1  Project foundation
Phase 2  Database + migrations
Phase 3  Authentication
Phase 4  Accounts
Phase 5  Categories
Phase 6  Transactions
Phase 7  Budgets
Phase 8  Recurring transactions
Phase 9  Dashboard
Phase 10 Reports
Phase 11 Notifications
Phase 12 Gamification
Phase 13 Testing hardening
Phase 14 Docker
Phase 15 Deployment
Phase 16 Expo integration
```

## 37. Architecture Acceptance Criteria

The architecture is ready when:

- FastAPI has clear versioned API routing.
- Routers contain HTTP concerns only.
- Services contain business logic.
- Repositories contain database access.
- SQLAlchemy models are separate from Pydantic schemas.
- JWT authentication is implemented through dependencies.
- Refresh tokens are persisted securely.
- User ownership is enforced.
- Financial mutations are atomic.
- Decimal is used for financial calculations.
- PostgreSQL is accessed through SQLAlchemy.
- Alembic manages schema changes.
- Configuration comes from environment variables.
- Docker can run the backend.
- Automated tests cover critical business logic.
- OpenAPI documentation is available.
- The architecture matches `BACKEND_PRD.md`, `DATABASE_SCHEMA.md`, and `API_SPEC.md`.

## 38. Final Principle

The goal is not the most complicated architecture.

The goal is a backend that is:

```text
Secure
   +
Correct
   +
Testable
   +
Maintainable
   +
Deployable
   +
Simple enough for an MVP
```

When a simpler design satisfies the requirements, prefer the simpler design.
