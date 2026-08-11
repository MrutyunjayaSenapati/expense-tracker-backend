# Expense Tracker — Backend Development Plan

Version: 1.0
Status: MVP
Backend: FastAPI
Database: Supabase PostgreSQL
ORM: SQLAlchemy 2.x
Migrations: Alembic
Authentication: JWT Access + Refresh Token
Deployment: Docker + Vercel-compatible deployment

---

# 1. Purpose

This document defines the implementation order for the Expense Tracker backend.

The goal is to build the backend incrementally, with each phase producing a working and testable result.

The implementation must follow these documents:

```text
BACKEND_PRD.md
DATABASE_SCHEMA.md
API_SPEC.md
ARCHITECTURE.md
```

Do not skip directly to advanced features.

---

# 2. Development Philosophy

Build in vertical slices.

For every feature:

```text
Database
   ↓
Migration
   ↓
Repository
   ↓
Schema
   ↓
Service
   ↓
API
   ↓
Tests
   ↓
Swagger verification
```

Do not implement large amounts of untested code and postpone testing until the end.

---

# 3. Phase 0 — Project Foundation

## Goal

Create a clean FastAPI project that starts successfully.

## Tasks

- Initialize Python project.
- Configure `pyproject.toml`.
- Install FastAPI and required dependencies.
- Create application package.
- Create `main.py`.
- Add `/health`.
- Add basic configuration.
- Add `.env.example`.
- Add `.gitignore`.
- Add README.
- Configure formatting/linting/testing tools.

## Expected structure

```text
app/
├── main.py
├── api/
├── core/
├── db/
├── schemas/
├── repositories/
├── services/
└── utils/
```

## Acceptance Criteria

```text
uvicorn app.main:app --reload
```

starts successfully.

The following works:

```text
GET /health
GET /docs
GET /redoc
```

---

# 4. Phase 1 — Database Foundation

## Goal

Connect FastAPI to Supabase PostgreSQL.

## Tasks

- Configure `DATABASE_URL`.
- Configure SQLAlchemy async engine.
- Configure async session factory.
- Create declarative base.
- Configure Alembic.
- Verify database connectivity.
- Create initial migration infrastructure.

## Acceptance Criteria

- FastAPI can connect to Supabase PostgreSQL.
- SQLAlchemy session works.
- Alembic can inspect metadata.
- No credentials are committed to Git.

---

# 5. Phase 2 — Database Models

Implement SQLAlchemy models according to `DATABASE_SCHEMA.md`.

Order:

```text
1. users
2. refresh_tokens
3. accounts
4. categories
5. transactions
6. budgets
7. budget_categories
8. recurring_transactions
9. notifications
10. user_streaks
11. achievements
12. user_achievements
```

## Tasks

- Create SQLAlchemy models.
- Add primary keys.
- Add foreign keys.
- Add constraints.
- Add indexes.
- Add relationships where useful.
- Configure timestamps.
- Generate Alembic migration.
- Apply migration.

## Acceptance Criteria

The schema can be created from an empty database using Alembic.

---

# 6. Phase 3 — Core Configuration

## Goal

Centralize application configuration.

Create:

```text
app/core/config.py
```

Configuration should include:

```text
DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
CORS_ORIGINS
ENVIRONMENT
```

## Acceptance Criteria

- Development configuration loads from `.env`.
- Production configuration loads from environment variables.
- Missing required secrets fail clearly.
- Secrets are never logged.

---

# 7. Phase 4 — Security Foundation

## Goal

Implement authentication primitives before building auth endpoints.

## Tasks

Implement:

```text
Password hashing
Password verification
JWT creation
JWT verification
Access-token validation
Refresh-token hashing
Refresh-token validation
```

Use:

```text
Argon2id
JWT
```

## Acceptance Criteria

- Passwords are never stored in plaintext.
- Password hash verification works.
- Invalid passwords fail.
- Expired JWTs fail.
- Invalid JWT signatures fail.
- Refresh tokens can be revoked.

---

# 8. Phase 5 — Authentication

## Goal

Complete MVP authentication.

Implement:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
DELETE /api/v1/auth/account
```

## Registration

Flow:

```text
Validate input
   ↓
Normalize email
   ↓
Check duplicate
   ↓
Hash password
   ↓
Create user
   ↓
Create default categories
   ↓
Commit
```

Email verification is not part of MVP.

Forgot-password functionality is not part of MVP.

Social login is not part of MVP.

## Acceptance Criteria

- User can register.
- Duplicate email is rejected.
- User can login.
- Invalid credentials are rejected.
- Access token works.
- Refresh token works.
- Logout revokes refresh token.
- `/auth/me` returns current user.
- Account deletion works according to the deletion policy.

---

# 9. Phase 6 — Current User Dependency

## Goal

Create reusable authentication dependency.

Implement:

```text
get_current_user()
```

Expected flow:

```text
Authorization header
        ↓
Extract Bearer token
        ↓
Validate JWT
        ↓
Get user ID
        ↓
Load user
        ↓
Check active
        ↓
Return user
```

## Acceptance Criteria

Protected endpoints reject:

```text
Missing token
Invalid token
Expired token
Inactive user
```

---

# 10. Phase 7 — Accounts

## Goal

Implement financial account management.

Endpoints:

```text
GET    /api/v1/accounts
GET    /api/v1/accounts/{id}
POST   /api/v1/accounts
PATCH  /api/v1/accounts/{id}
DELETE /api/v1/accounts/{id}
```

## Tasks

- Account repository.
- Account schemas.
- Account service.
- Account router.
- Ownership checks.
- Account validation.
- Deactivation behavior.

## Acceptance Criteria

User can:

```text
Create HDFC account.
Create SBI account.
Create Cash account.
List accounts.
Update account name.
Deactivate account.
```

A user cannot access another user's account.

---

# 11. Phase 8 — Categories

## Goal

Implement category management.

Endpoints:

```text
GET    /api/v1/categories
POST   /api/v1/categories
PATCH  /api/v1/categories/{id}
DELETE /api/v1/categories/{id}
```

## Registration Integration

When a user registers:

```text
Create default expense categories
Create default income categories
```

## Acceptance Criteria

- Default categories exist after registration.
- User can create custom category.
- User can update category.
- Used categories are safely deactivated rather than breaking historical transactions.
- Category ownership is enforced.

No subcategories.

No contexts.

No tags.

No hierarchy.

---

# 12. Phase 9 — Transactions

This is the most important backend phase.

## Goal

Implement reliable financial transaction processing.

Endpoints:

```text
GET    /api/v1/transactions
GET    /api/v1/transactions/{id}
POST   /api/v1/transactions
PATCH  /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}
```

## Create Expense

```text
Validate user
   ↓
Validate account ownership
   ↓
Validate category ownership
   ↓
Validate amount
   ↓
BEGIN
   ↓
Create transaction
   ↓
Decrease account balance
   ↓
Update dependent budget state
   ↓
Update gamification
   ↓
COMMIT
```

## Create Income

Same process, but increase account balance.

## Critical Rule

Financial updates must be atomic.

## Acceptance Criteria

Test:

```text
Create ₹500 expense
Account balance decreases ₹500

Create ₹10,000 income
Account balance increases ₹10,000

Transaction failure
Account balance remains unchanged

Unauthorized account
Request rejected

Unauthorized category
Request rejected
```

---

# 13. Phase 10 — Transaction Filtering and Search

## Goal

Implement efficient transaction browsing.

Filters:

```text
category_id
account_id
type
start_date
end_date
min_amount
max_amount
search
```

Pagination:

```text
page
limit
```

Sorting:

```text
transaction_date
amount
created_at
```

## Search

Search:

```text
merchant
note
category name
```

Case-insensitive.

Example:

```text
GET /api/v1/transactions?category_id=<petrol-id>
```

must return all Petrol transactions for the authenticated user.

## Acceptance Criteria

- Category filtering works.
- Account filtering works.
- Date filtering works.
- Search works.
- Pagination works.
- Sorting works.
- User isolation works.

---

# 14. Phase 11 — Transaction Update and Delete

## Goal

Correctly handle financial corrections.

Example:

```text
Old:
HDFC expense ₹500

New:
SBI expense ₹700
```

Expected:

```text
HDFC +₹500
SBI  -₹700
```

This must happen atomically.

For deletion:

```text
Expense ₹500 deleted
        ↓
Account receives +₹500
```

## Acceptance Criteria

Automated tests must cover:

```text
Amount change
Account change
Category change
Type change
Delete expense
Delete income
Failed update rollback
```

---

# 15. Phase 12 — Budgets

## Goal

Implement monthly budgets.

Endpoints:

```text
GET    /api/v1/budgets
GET    /api/v1/budgets/{id}
POST   /api/v1/budgets
PATCH  /api/v1/budgets/{id}
DELETE /api/v1/budgets/{id}
```

## Calculations

Backend calculates:

```text
spent
remaining
percentage_used
status
```

Example:

```text
Budget = ₹45,000
Spent = ₹33,600

Remaining = ₹11,400
Percentage = 74.67%
```

## Acceptance Criteria

- Monthly budget can be created.
- Category allocations work.
- Spending is derived from transactions.
- Budget status is calculated by backend.
- User isolation works.

---

# 16. Phase 13 — Dashboard

## Goal

Create a single API optimized for the Home screen.

Endpoint:

```text
GET /api/v1/dashboard
```

Return:

```text
Balance
Income
Expenses
Savings
Savings percentage
Budget summary
Top categories
Recent transactions
Streak
```

## Important Rule

Do not force the mobile app to make many requests for basic dashboard data if a combined dashboard response is appropriate.

## Acceptance Criteria

Dashboard values match database calculations.

---

# 17. Phase 14 — Reports

## Goal

Implement weekly financial reports.

Endpoint:

```text
GET /api/v1/reports?period=week
```

Calculate using database aggregation where practical.

Return:

```text
Income
Expenses
Savings
Category breakdown
Account breakdown
Trend
```

## Acceptance Criteria

Report totals match transaction data.

---

# 18. Phase 15 — Recurring Transactions

## Goal

Support:

```text
DAILY
MONTHLY
```

Examples:

```text
Daily petrol
Monthly rent
Monthly electricity
```

Endpoints:

```text
GET    /api/v1/recurring-transactions
GET    /api/v1/recurring-transactions/{id}
POST   /api/v1/recurring-transactions
PATCH  /api/v1/recurring-transactions/{id}
DELETE /api/v1/recurring-transactions/{id}
```

## Processing

The backend must process due recurring records.

```text
next_occurrence <= today
        ↓
Create transaction
        ↓
Advance next_occurrence
```

## Critical Requirement

Processing must be idempotent.

Running the job twice must not create duplicate financial transactions.

## Acceptance Criteria

- Daily recurrence works.
- Monthly recurrence works.
- End date works.
- Deactivation works.
- Duplicate processing is prevented.

---

# 19. Phase 16 — Notifications

Implement:

```text
GET /api/v1/notifications
PATCH /api/v1/notifications/{id}/read
PATCH /api/v1/notifications/read-all
```

Backend notification events:

```text
Budget warning
Budget exceeded
Achievement unlocked
Recurring transaction
Monthly summary
Tracking reminder
```

## Acceptance Criteria

- Notifications are user-scoped.
- Read state works.
- Mark-all-read works.
- Notification creation is deterministic.

---

# 20. Phase 17 — Gamification

Implement:

```text
GET /api/v1/gamification
```

Features:

```text
Current streak
Longest streak
Achievements
Achievement unlock state
```

Initial achievements:

```text
FIRST_TRANSACTION
SEVEN_DAY_STREAK
BUDGET_ACHIEVED
FIFTY_TRANSACTIONS
MONTHLY_GOAL
SAVINGS_MILESTONE
```

## Acceptance Criteria

- First transaction achievement works.
- Streak calculation works.
- Seven-day achievement works.
- Duplicate achievement unlock is prevented.
- Achievement notification can be generated.

---

# 21. Phase 18 — Testing Hardening

Before deployment, run the complete test suite.

## Unit Tests

Cover:

```text
Password hashing
JWT
Money
Budget calculations
Savings
Streaks
Recurrence dates
Financial calculations
```

## Integration Tests

Cover:

```text
Database
Repositories
Services
Transaction boundaries
```

## API Tests

Cover all public endpoints.

## Security Tests

Especially:

```text
Cross-user access
Invalid JWT
Expired JWT
Revoked refresh token
Inactive user
Invalid account ownership
Invalid category ownership
```

---

# 22. Phase 19 — Docker

Create:

```text
Dockerfile
docker-compose.yml
```

## Docker Requirements

- Small maintained Python image.
- Reproducible dependency installation.
- Non-root runtime where practical.
- Environment-based configuration.
- Production ASGI command.
- Respect deployment `PORT`.

## Local Verification

Build:

```bash
docker build -t expense-tracker-api .
```

Run:

```bash
docker run --env-file .env -p 8000:8000 expense-tracker-api
```

Verify:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

---

# 23. Phase 20 — Deployment

Target:

```text
Expo
  ↓ HTTPS
FastAPI Docker deployment
  ↓
Supabase PostgreSQL
```

Before deployment verify:

```text
Environment variables
Database connectivity
CORS
Health endpoint
Swagger
JWT
Migrations
Logs
```

Do not deploy with development secrets.

---

# 24. Phase 21 — Expo Integration

After the backend is stable, connect the existing Expo application.

Integration order:

```text
Authentication
    ↓
Accounts
    ↓
Categories
    ↓
Transactions
    ↓
Dashboard
    ↓
Budgets
    ↓
Reports
    ↓
Recurring
    ↓
Notifications
    ↓
Gamification
```

The frontend should replace mock JSON incrementally.

Do not replace every mock API at once.

---

# 25. Mock-to-API Migration Strategy

Current:

```text
Expo
 ↓
Mock JSON
```

Target:

```text
Expo
 ↓
API Client
 ↓
FastAPI
 ↓
Supabase
```

For each feature:

```text
Existing UI
    ↓
Create API client function
    ↓
Connect endpoint
    ↓
Map response to UI model
    ↓
Remove mock data
    ↓
Test loading/error/empty states
```

---

# 26. Frontend Compatibility Rule

Do not modify the backend API merely to match an arbitrary frontend implementation.

If the API contract is already defined, adapt the frontend API client to it.

If a genuine product requirement requires an API change:

```text
Update BACKEND_PRD
        ↓
Update DATABASE_SCHEMA if required
        ↓
Update API_SPEC
        ↓
Update implementation
        ↓
Update tests
```

---

# 27. CI Quality Gates

Before merging backend changes, run:

```bash
pytest
```

plus the project's configured lint/type checks.

Recommended checks:

```text
Tests
Lint
Type checking
Migration validation
Docker build
```

A feature is not complete merely because the endpoint works manually.

---

# 28. Migration Rules

Every database schema change must use Alembic.

Never manually edit production tables as the normal development process.

Pattern:

```text
Change SQLAlchemy model
        ↓
Generate migration
        ↓
Review migration
        ↓
Apply locally
        ↓
Run tests
        ↓
Deploy migration
```

Never modify an already-applied production migration.

---

# 29. Definition of Done

A backend feature is complete only when:

- Database model exists if needed.
- Migration exists.
- Pydantic schemas exist.
- Repository exists if database access requires one.
- Service logic exists.
- API endpoint exists.
- Authentication/ownership is enforced.
- Validation exists.
- Error handling exists.
- Unit tests exist where appropriate.
- Integration/API tests exist where appropriate.
- Swagger is correct.
- No secrets are committed.
- Existing tests still pass.

---

# 30. MVP Completion Checklist

## Foundation

- [ ] FastAPI starts
- [ ] `/health`
- [ ] Swagger
- [ ] Configuration
- [ ] Database connection
- [ ] Alembic

## Authentication

- [ ] Register
- [ ] Login
- [ ] JWT access token
- [ ] Refresh token
- [ ] Logout
- [ ] Current user
- [ ] Delete account

## Financial Data

- [ ] Accounts
- [ ] Categories
- [ ] Transactions
- [ ] Transaction filtering
- [ ] Search
- [ ] Pagination
- [ ] Sorting
- [ ] Atomic balance updates

## Planning

- [ ] Monthly budgets
- [ ] Budget categories
- [ ] Budget calculations

## Automation

- [ ] Daily recurring transactions
- [ ] Monthly recurring transactions
- [ ] Idempotent processing

## Dashboard & Reports

- [ ] Dashboard
- [ ] Weekly reports
- [ ] Category aggregation
- [ ] Account aggregation
- [ ] Spending trend

## Engagement

- [ ] Notifications
- [ ] Streaks
- [ ] Achievements

## Production

- [ ] Automated tests
- [ ] Security tests
- [ ] Docker
- [ ] Environment configuration
- [ ] CORS
- [ ] Logging
- [ ] Deployment
- [ ] Expo integration

---

# 31. Explicit MVP Exclusions

Do not implement these unless the product requirements are changed:

```text
Email verification
Forgot password
Google login
Apple login
Profile photo
Receipt upload
OCR
Multiple currencies
Subcategories
Contexts
Tags
Category hierarchy
Bank API integration
UPI transaction import
Credit score
Investment tracking
Microservices
Kubernetes
Redis
Kafka
GraphQL
```

---

# 32. Implementation Rule for AI Coding Agents

When using Antigravity, Claude Code, Codex, OpenCode, or another coding agent:

1. Read all backend documentation before modifying code.
2. Follow the implementation order in this document.
3. Never invent missing product requirements.
4. Never silently change the API contract.
5. Never expose secrets.
6. Never skip ownership checks.
7. Never use floating-point arithmetic for money.
8. Never modify production schema without an Alembic migration.
9. Run tests after each meaningful feature.
10. Keep changes focused on the current phase.
11. Do not implement future features early.
12. Explain any conflict between documents before making a breaking decision.

---

# 33. Final Development Sequence

The complete sequence is:

```text
01 Foundation
       ↓
02 Database connection
       ↓
03 Models + migrations
       ↓
04 Security
       ↓
05 Authentication
       ↓
06 User dependency
       ↓
07 Accounts
       ↓
08 Categories
       ↓
09 Transactions
       ↓
10 Filtering/search
       ↓
11 Transaction corrections
       ↓
12 Budgets
       ↓
13 Dashboard
       ↓
14 Reports
       ↓
15 Recurring transactions
       ↓
16 Notifications
       ↓
17 Gamification
       ↓
18 Testing hardening
       ↓
19 Docker
       ↓
20 Deployment
       ↓
21 Expo integration
```

This sequence should be followed unless a concrete technical dependency requires a change.
