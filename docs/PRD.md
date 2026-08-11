# Expense Tracker — Backend Product Requirements Document

Version: 1.0
Status: MVP
Backend: FastAPI
Database: Supabase PostgreSQL
Authentication: Email + Password + JWT
Containerization: Docker
Currency: INR

---

# 1. Document Purpose

This document defines the backend requirements for the Expense Tracker mobile application.

The existing mobile application is built using:

- React Native
- Expo
- TypeScript
- Expo Router
- TanStack Query
- Zustand
- Mock JSON/repositories

The purpose of this backend is to replace the mock data layer with a real production-structured API while keeping the existing frontend architecture intact.

The backend must provide:

- Authentication
- User management
- Financial accounts
- Income and expenses
- Categories
- Transaction notes
- Transaction search and filtering
- Monthly budgets
- Recurring transactions
- Dashboard calculations
- Weekly reports
- Notifications foundation
- Gamification
- Account deletion
- Secure authorization
- API documentation
- Automated tests
- Docker support
- Production deployment

---

# 2. Core Product Principle

The MVP should remain simple.

Do not introduce unnecessary data dimensions merely because they may be useful in the future.

The core transaction model is:

Transaction
├── Account
├── Category
├── Amount
├── Type
├── Merchant
├── Note
└── Date

The MVP does NOT use:

- Subcategories
- Hierarchical categories
- Contexts
- Tags

These may be introduced later if actual product usage demonstrates a need for them.

---

# 3. Technology Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- pytest

## Authentication

- Email/password
- Argon2id password hashing
- JWT access tokens
- Refresh tokens

## Database

- Supabase PostgreSQL

## File Storage

Supabase Storage may be used in a future phase.

Receipt uploads are NOT part of MVP.

## Infrastructure

- Docker
- Docker Compose
- GitHub Actions

## API Documentation

- OpenAPI
- Swagger UI
- ReDoc

---

# 4. High-Level Architecture

The system architecture is:

React Native / Expo
        ↓
TanStack Query
        ↓
Repository Interface
        ↓
API Repository
        ↓ HTTPS
FastAPI
        ↓
Service Layer
        ↓
Repository Layer
        ↓
SQLAlchemy
        ↓
Supabase PostgreSQL

Authentication:

Expo
 ↓
FastAPI Auth
 ↓
JWT
 ↓
Authenticated API requests

---

# 5. Frontend Architecture Preservation

The existing frontend repository architecture MUST remain intact.

Current:

Screen
 ↓
Hook
 ↓
Repository
 ↓
Mock Repository
 ↓
Mock JSON

Target:

Screen
 ↓
Hook
 ↓
Repository
 ↓
API Repository
 ↓
FastAPI
 ↓
PostgreSQL

The backend implementation must not require rewriting the existing screens.

The frontend should communicate with the backend through repositories and TanStack Query.

Screens should never directly contain API calls.

---

# 6. MVP Scope

## Included

### Authentication

- Registration
- Login
- JWT access token
- Refresh token
- Logout
- Current user
- Account deletion

### Financial Management

- Multiple accounts
- Starting balance
- Income
- Expenses
- Account balance updates
- Categories
- Transaction notes
- Merchant
- Transaction date

### Transactions

- Create
- Read
- Update
- Delete
- Search
- Filtering
- Sorting
- Pagination

### Budgeting

- Monthly overall budget
- Monthly category budgets
- Budget calculations
- Budget status

### Recurring Transactions

- Daily
- Monthly

### Analytics

- Dashboard
- Weekly reports
- Category aggregation
- Account aggregation
- Spending trends

### Product Features

- Notifications foundation
- Tracking streaks
- Achievements
- Gamification

### Infrastructure

- PostgreSQL
- Alembic migrations
- Docker
- API documentation
- Production-grade testing
- CI

---

# 7. Explicitly Out of MVP

Do NOT implement these during the initial backend phase:

- Email verification
- Forgot password
- Google login
- Apple login
- Profile photo
- Receipt image upload
- Account transfers
- Multi-currency
- Subcategories
- Hierarchical categories
- Contexts
- Tags
- Weekly recurring transactions
- Yearly recurring transactions
- Custom recurrence
- Monthly/yearly/custom reports
- Advanced AI analytics

These belong to future phases.

---

# 8. Authentication

## 8.1 Registration

The signup screen contains:

- Name
- Email
- Password
- Confirm Password

Profile photo is not part of MVP.

Endpoint:

POST /api/v1/auth/register

Request:

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "********",
  "confirm_password": "********"
}

Backend must:

1. Validate name.
2. Normalize email.
3. Validate email format.
4. Check whether email already exists.
5. Validate password strength.
6. Verify password and confirm-password match.
7. Hash the password using Argon2id.
8. Create the user.
9. Create default categories.
10. Return safe user information.

Never store plain-text passwords.

---

# 9. Email Verification

Email verification is NOT implemented in MVP.

Users can log in immediately after registration.

The architecture should remain extensible for future email verification.

---

# 10. Forgot Password

Forgot password is NOT implemented in MVP.

The architecture should allow it to be added later.

---

# 11. Login

Endpoint:

POST /api/v1/auth/login

Request:

{
  "email": "john@example.com",
  "password": "********"
}

Response:

{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "...",
    "name": "John Doe",
    "email": "john@example.com"
  }
}

---

# 12. JWT Strategy

Use a production-oriented access-token + refresh-token architecture.

## Access Token

Short-lived.

Recommended expiration:

15–30 minutes.

The JWT should contain:

- user ID
- token type
- issued-at timestamp
- expiration timestamp

## Refresh Token

Long-lived.

Recommended initial expiration:

30 days.

Refresh tokens must be revocable.

The backend must NOT rely only on access-token expiration.

---

# 13. Refresh Token

Endpoint:

POST /api/v1/auth/refresh

Request:

{
  "refresh_token": "..."
}

Response:

{
  "access_token": "...",
  "expires_in": 1800,
  "token_type": "bearer"
}

Refresh tokens must be validated and checked for revocation.

Prefer storing a secure representation/hash of refresh tokens server-side rather than storing reusable raw refresh tokens in plaintext.

---

# 14. Logout

Endpoint:

POST /api/v1/auth/logout

Logout must perform both:

1. Server-side refresh-token invalidation.
2. Client-side removal of authentication tokens.

Expo should remove authentication tokens from secure device storage.

---

# 15. Current User

Endpoint:

GET /api/v1/auth/me

Response:

{
  "id": "...",
  "name": "John Doe",
  "email": "john@example.com"
}

---

# 16. Delete Account

Endpoint:

DELETE /api/v1/auth/account

Users must be able to delete their account.

After deletion:

- User authentication must no longer work.
- Existing refresh sessions must be invalidated.
- User-owned financial data must no longer be accessible.
- Personal data should be deleted or anonymized according to the application's retention policy.

---

# 17. Future Social Authentication

Social login is not implemented in MVP.

Future providers:

- Google
- Apple

The architecture should allow:

User
 ├── Password
 ├── Google
 └── Apple

without changing transaction, budget, reporting, or account APIs.

Future social authentication can provide:

- Name
- Email
- Profile photo

---

# 18. User Model

Initial database model:

users

- id
- name
- email
- password_hash
- is_active
- created_at
- updated_at

Do not add profile photo in MVP.

---

# 19. Financial Accounts

Users can have multiple accounts.

Examples:

- HDFC Bank
- SBI Bank
- Cash
- Paytm
- PhonePe
- Credit Card
- Debit Card

The user defines the account name.

Example:

Type:
BANK

Name:
HDFC Salary Account

Another:

Type:
BANK

Name:
SBI Savings

---

# 20. Account Types

Initial supported types:

- CASH
- BANK
- UPI_WALLET
- CREDIT_CARD
- DEBIT_CARD
- OTHER

---

# 21. Account Model

accounts

- id
- user_id
- name
- type
- balance
- currency
- is_active
- created_at
- updated_at

Currency is INR for MVP.

---

# 22. Starting Balance

When creating an account, the user can provide a starting balance.

Example:

HDFC Bank
Starting balance: ₹50,000

This becomes the initial account balance.

---

# 23. Account Balance Rules

The backend owns account balance calculations.

When an expense is created:

balance decreases.

When income is created:

balance increases.

Example:

Starting balance:
₹50,000

Expense:
₹500

Result:
₹49,500

Income:
₹10,000

Result:
₹59,500

The frontend must not be the authoritative source of balances.

---

# 24. Financial Transactions

MVP transaction types:

- EXPENSE
- INCOME

---

# 25. Core Transaction Data Model

The transaction model is intentionally simple.

transactions

- id
- user_id
- account_id
- category_id
- amount
- type
- merchant
- note
- transaction_date
- created_at
- updated_at

Optional fields:

- merchant
- note

---

# 26. Transaction Category

Every transaction should have a category.

Examples:

Expense:

- Food
- Petrol
- Electricity
- Rent
- Shopping
- Internet
- Medical
- Entertainment
- Other

Income:

- Salary
- Freelance
- Business
- Investment
- Gift
- Other

Categories are flat in MVP.

There is NO parent/child category relationship.

---

# 27. Category Model

categories

- id
- user_id
- name
- type
- icon
- color
- is_active
- created_at
- updated_at

Where:

type:

- EXPENSE
- INCOME

---

# 28. Default Categories

New users receive default categories.

## Expense

- Food
- Petrol
- Transport
- Electricity
- Rent
- Shopping
- Internet
- Medical
- Entertainment
- Groceries
- Subscriptions
- Other

## Income

- Salary
- Freelance
- Business
- Investment
- Gift
- Other

Users can later create, rename, deactivate, or delete categories where safe.

---

# 29. Why Categories Are Flat

The MVP intentionally avoids:

Transport
 └── Petrol

or:

Bills
 └── Electricity

Instead:

Petrol
Electricity
Transport
Bills

can all be independent categories.

This keeps:

- Add Expense simple.
- Database simple.
- Filtering simple.
- Reports simple.
- API simple.

If future usage demonstrates a need for hierarchical categories, they can be introduced later through a migration.

---

# 30. Transaction Note

Every transaction may contain an optional note.

Use the field name:

note

Do not use `message` as the database field name.

Example:

Amount:
₹500

Category:
Petrol

Account:
HDFC Bank

Merchant:
Indian Oil

Note:
"Filled petrol before going to office"

The note is free text.

---

# 31. Merchant

A transaction may contain an optional merchant.

Examples:

- Indian Oil
- Uber
- Amazon
- Swiggy
- HDFC
- Electricity Board

Merchant is separate from category.

Example:

Category:
Petrol

Merchant:
Indian Oil

---

# 32. Transaction Date

Transactions must store the date/time when the expense or income occurred.

The backend must use a consistent timezone strategy.

Store timestamps in UTC where appropriate and convert to the user's local timezone for presentation.

For MVP, the primary user timezone should be configurable or derived from the client/application settings.

---

# 33. Transaction API

GET /api/v1/transactions

GET /api/v1/transactions/{id}

POST /api/v1/transactions

PATCH /api/v1/transactions/{id}

DELETE /api/v1/transactions/{id}

---

# 34. Transaction Filtering

The API must support:

- Category
- Account
- Type
- Date range
- Amount range
- Merchant
- Search
- Sorting

Examples:

GET /api/v1/transactions?category_id={petrol_id}

Returns all Petrol transactions.

Example:

GET /api/v1/transactions?account_id={hdfc_id}

Returns all HDFC transactions.

Example:

GET /api/v1/transactions?type=EXPENSE

Returns all expenses.

---

# 35. Transaction Search

Search should initially search:

- merchant
- note
- category name

Example:

GET /api/v1/transactions?search=office

Possible results:

₹500 Petrol
Merchant: Indian Oil
Note: Filled petrol before office

₹250 Food
Merchant: Cafe
Note: Lunch with office team

Search should be case-insensitive.

---

# 36. Pagination

Transactions must be paginated.

Default:

page = 1
limit = 20

Maximum limit should be enforced.

Response:

{
  "items": [],
  "page": 1,
  "limit": 20,
  "total": 100,
  "total_pages": 5
}

---

# 37. Sorting

Support sorting by:

- transaction_date
- amount
- created_at

Example:

GET /api/v1/transactions?sort=transaction_date&order=desc

Default:

transaction_date DESC

---

# 38. Accounts API

GET /api/v1/accounts

GET /api/v1/accounts/{id}

POST /api/v1/accounts

PATCH /api/v1/accounts/{id}

DELETE /api/v1/accounts/{id}

All account operations must be scoped to the authenticated user.

---

# 39. Categories API

GET /api/v1/categories

POST /api/v1/categories

PATCH /api/v1/categories/{id}

DELETE /api/v1/categories/{id}

Users can manage their own categories.

---

# 40. Budget System

MVP supports monthly budgets.

Two types:

1. Overall monthly budget.
2. Category-specific monthly budget.

Example:

Overall:

₹45,000

Category:

Food:
₹10,000

Shopping:
₹5,000

Petrol:
₹4,000

---

# 41. Budget Model

budgets

- id
- user_id
- name
- amount
- period
- start_date
- end_date
- created_at
- updated_at

budget_categories

- id
- budget_id
- category_id
- amount

---

# 42. Budget Calculations

Backend calculates:

- budget amount
- amount spent
- remaining amount
- percentage used
- status

Statuses:

- HEALTHY
- WARNING
- NEAR_LIMIT
- OVER_BUDGET

Do not rely only on color to communicate the status.

---

# 43. Budget API

GET /api/v1/budgets

GET /api/v1/budgets/{id}

POST /api/v1/budgets

PATCH /api/v1/budgets/{id}

DELETE /api/v1/budgets/{id}

---

# 44. Recurring Transactions

Recurring transactions are included in MVP.

Supported frequencies:

- DAILY
- MONTHLY

Examples:

Petrol:
DAILY

Rent:
MONTHLY

Netflix:
MONTHLY

Salary:
MONTHLY

---

# 45. Recurring Transaction Model

recurring_transactions

- id
- user_id
- account_id
- category_id
- type
- amount
- merchant
- note
- frequency
- start_date
- end_date
- next_occurrence
- is_active
- created_at
- updated_at

---

# 46. Recurring Transaction Behavior

Do NOT generate unlimited future transactions.

Store the recurrence definition.

Example:

Petrol:

frequency:
DAILY

next_occurrence:
2026-08-11

When the occurrence is processed:

next_occurrence becomes:

2026-08-12

The system must prevent duplicate generation if the recurrence-processing job runs more than once.

---

# 47. Dashboard

Endpoint:

GET /api/v1/dashboard

The backend calculates:

- Total balance
- Total income
- Total expenses
- Net savings
- Savings percentage
- Budget summary
- Top spending categories
- Spending trend
- Recent transactions
- Tracking streak

Financial values must come from real database data.

Do not hardcode values from UI reference designs.

---

# 48. Dashboard Example

Conceptual response:

{
  "balance": 87450,
  "income": 109000,
  "expenses": 39219,
  "savings": 69781,
  "savings_percentage": 63.9,
  "budget": {
    "amount": 45000,
    "spent": 33600,
    "remaining": 11400,
    "percentage_used": 74.7,
    "status": "HEALTHY"
  },
  "top_categories": [],
  "recent_transactions": [],
  "streak": {
    "current": 7,
    "longest": 12
  }
}

The actual values must be calculated from the database.

---

# 49. Financial Calculations

Important financial calculations must be centralized in backend services.

Examples:

Savings:

income - expenses

Savings percentage:

savings / income × 100

Budget percentage:

spent / budget × 100

Account balance:

starting balance
+ income
- expenses

The backend is authoritative.

The frontend should display the results.

---

# 50. Weekly Reports

MVP supports weekly reports.

Endpoint:

GET /api/v1/reports?period=week

Report should include:

- Income
- Expenses
- Savings
- Category breakdown
- Spending trend
- Top categories
- Account breakdown

---

# 51. Report Aggregation

The backend should support aggregation by:

- Category
- Account
- Date

Example:

Category:

Petrol:
₹3,500

Food:
₹7,200

Electricity:
₹1,800

Account:

HDFC:
₹12,500

SBI:
₹5,200

Cash:
₹2,000

---

# 52. Future Reporting Dimensions

Future versions may support:

- Context
- Tags
- Subcategories
- Location
- Projects

These are NOT part of MVP.

The database should be designed cleanly enough that these can be added later.

---

# 53. Notifications

Notifications are part of the product roadmap.

Initial notification types:

- Budget approaching limit
- Budget exceeded
- Daily tracking reminder
- Monthly summary
- Recurring transaction reminder
- Achievement unlocked

---

# 54. Notification Model

notifications

- id
- user_id
- type
- title
- message
- data
- is_read
- created_at

---

# 55. Notification API

GET /api/v1/notifications

PATCH /api/v1/notifications/{id}/read

PATCH /api/v1/notifications/read-all

The notification system should be designed so push notifications can be added later.

---

# 56. Gamification

Gamification should encourage healthy financial behavior.

Initial features:

- Tracking streak
- Budget achieved
- Monthly goal
- Savings milestone
- Transaction milestone

Examples:

7 Day Tracking Streak

Budget Achieved

50 Transactions Tracked

Monthly Goal Completed

Savings Milestone

Gamification must never reward unnecessary spending.

---

# 57. Streaks

Track:

- Current streak
- Longest streak
- Last activity date

Example:

user_streaks

- id
- user_id
- current_streak
- longest_streak
- last_activity_date
- created_at
- updated_at

A tracking day is determined by meaningful expense/income tracking activity.

The same day must not increase the streak multiple times.

---

# 58. Achievements

achievements

- id
- code
- name
- description
- icon

user_achievements

- id
- user_id
- achievement_id
- unlocked_at

The backend is authoritative for achievement unlocking.

---

# 59. Currency

MVP supports only:

INR / ₹

Do not implement multi-currency.

The data model should still allow currency to be added later.

---

# 60. Receipt Upload

Receipt upload is NOT part of MVP.

Future architecture:

Expo
 ↓
FastAPI
 ↓
Supabase Storage
 ↓
Receipt path
 ↓
Transaction

Do not store receipt image binaries inside PostgreSQL.

---

# 61. Account Transfers

Transfers are NOT part of MVP.

Future:

HDFC Bank
₹5,000
 ↓
Cash
₹5,000

Do not model transfers as ordinary expenses.

---

# 62. API Versioning

All endpoints use:

/api/v1/

Examples:

/api/v1/auth/login

/api/v1/accounts

/api/v1/categories

/api/v1/transactions

/api/v1/budgets

/api/v1/recurring-transactions

/api/v1/dashboard

/api/v1/reports

/api/v1/notifications

Future breaking changes can use:

/api/v2/

---

# 63. Error Format

Use a consistent error format.

Example:

{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction not found"
  }
}

Common error codes should be documented.

Examples:

AUTH_INVALID_CREDENTIALS

AUTH_TOKEN_EXPIRED

AUTH_UNAUTHORIZED

USER_ALREADY_EXISTS

RESOURCE_NOT_FOUND

VALIDATION_ERROR

TRANSACTION_NOT_FOUND

ACCOUNT_NOT_FOUND

CATEGORY_NOT_FOUND

BUDGET_NOT_FOUND

---

# 64. Error Security

Never expose:

- SQL errors
- Database connection details
- Stack traces
- Password hashes
- JWT secrets
- Internal implementation details

Production responses must contain safe messages.

Detailed errors should be logged server-side.

---

# 65. Authorization

Every user-owned resource must be scoped to the authenticated user.

Example:

User A attempts:

GET /api/v1/transactions/{user_B_transaction}

The request must not expose User B's data.

Return:

403 or 404

Prefer 404 where appropriate to avoid leaking resource existence.

---

# 66. Database Transactions

Financial mutations must use database transactions.

Creating an expense should conceptually:

1. Validate request.
2. Validate account ownership.
3. Validate category ownership.
4. Insert transaction.
5. Update account balance.
6. Update relevant budget state if necessary.
7. Update gamification state if necessary.
8. Commit.

If any operation fails:

ROLLBACK

The system must never leave:

Transaction created
+
Account balance unchanged

or another inconsistent financial state.

---

# 67. Concurrency

Account balance updates must be safe against concurrent requests.

The implementation should use appropriate database transaction/isolation/locking strategies to prevent lost updates.

This is especially important when two expense requests are submitted quickly.

---

# 68. Database Schema

Initial core tables:

users

accounts

categories

transactions

budgets

budget_categories

recurring_transactions

notifications

user_streaks

achievements

user_achievements

refresh_tokens

---

# 69. Database Relationships

User:

1 → many Accounts

User:

1 → many Categories

User:

1 → many Transactions

User:

1 → many Budgets

User:

1 → many Recurring Transactions

User:

1 → many Notifications

User:

1 → one Streak

User:

many → many Achievements

Account:

1 → many Transactions

Category:

1 → many Transactions

Budget:

1 → many Budget Categories

---

# 70. Database Ownership

Every user-owned entity must contain user ownership information directly or through a trusted relationship.

Examples:

transactions.user_id

accounts.user_id

categories.user_id

budgets.user_id

recurring_transactions.user_id

notifications.user_id

This simplifies authorization queries and security enforcement.

---

# 71. Database Indexing

Create indexes for common access patterns.

At minimum consider indexes for:

transactions:

- user_id
- account_id
- category_id
- transaction_date
- type
- user_id + transaction_date

categories:

- user_id
- type

accounts:

- user_id

budgets:

- user_id
- start_date
- end_date

recurring_transactions:

- user_id
- next_occurrence
- is_active

notifications:

- user_id
- is_read
- created_at

The final index design should be based on actual query patterns.

---

# 72. Database Migrations

Use Alembic.

Example:

001_initial_schema

002_add_refresh_tokens

003_add_budgets

etc.

Never modify production schema manually without a corresponding migration.

Migrations must be committed to Git.

---

# 73. Backend Project Structure

Recommended:

backend/
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── dependencies.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── accounts.py
│   │       ├── categories.py
│   │       ├── transactions.py
│   │       ├── budgets.py
│   │       ├── recurring.py
│   │       ├── dashboard.py
│   │       ├── reports.py
│   │       ├── notifications.py
│   │       └── gamification.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── db/
│
├── alembic/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example

---

# 74. API Layer

Routers should be responsible for:

- Request parsing
- Authentication dependencies
- Calling services
- Returning responses

Routers should NOT contain complex business logic.

---

# 75. Service Layer

Services should contain business logic such as:

- Account balance updates
- Budget calculations
- Recurring transaction processing
- Dashboard calculations
- Report calculations
- Streak calculations
- Achievement unlocking

---

# 76. Repository Layer

Repositories should handle database access.

Example:

TransactionRepository

- create
- get_by_id
- list
- update
- delete

Services should not contain raw SQL unnecessarily.

---

# 77. Pydantic Schemas

Separate:

- Request schemas
- Response schemas
- Internal/domain models where appropriate

Do not expose SQLAlchemy models directly as API contracts.

---

# 78. Environment Variables

Example:

DATABASE_URL=

JWT_SECRET_KEY=

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

REFRESH_TOKEN_EXPIRE_DAYS=30

SUPABASE_URL=

SUPABASE_SERVICE_ROLE_KEY=

ENVIRONMENT=development

Never commit real secrets.

---

# 79. CORS

Configure CORS based on the actual clients.

Development may allow local Expo development origins.

Production must use an explicit allowlist.

Do not use unrestricted:

allow_origins=["*"]

for authenticated production APIs unless there is a deliberate reason.

---

# 80. Rate Limiting

Authentication endpoints should have reasonable rate limiting.

Especially:

POST /auth/register

POST /auth/login

POST /auth/refresh

This reduces brute-force and abuse risk.

---

# 81. Logging

Backend logs should include useful operational information without sensitive data.

Never log:

- passwords
- password hashes
- JWT secrets
- raw refresh tokens
- sensitive authentication credentials

Use structured logging where practical.

---

# 82. Health Check

Implement:

GET /health

Response:

{
  "status": "ok"
}

Optionally provide a separate readiness check for database connectivity.

---

# 83. OpenAPI / Swagger

FastAPI documentation is required.

Development:

/docs

/redoc

Every endpoint must define:

- Description
- Authentication requirement
- Request schema
- Response schema
- Error responses

Swagger must accurately reflect the API contract.

---

# 84. Testing Strategy

Production-grade testing is required.

## Unit Tests

Test:

- Password validation
- Password hashing
- JWT generation
- JWT validation
- Financial calculations
- Budget calculations
- Recurrence calculations
- Streak calculations
- Achievement rules

## API Tests

Test:

- Registration
- Login
- Refresh
- Logout
- Current user
- Delete account
- Account CRUD
- Category CRUD
- Transaction CRUD
- Budget CRUD
- Recurring transactions
- Dashboard
- Reports
- Notifications
- Gamification

## Security Tests

Test:

- Missing JWT
- Invalid JWT
- Expired JWT
- Invalid refresh token
- Revoked refresh token
- User A accessing User B data
- Deleted account access
- Inactive account access

## Integration Tests

Test:

FastAPI
 ↓
SQLAlchemy
 ↓
PostgreSQL

---

# 85. CI/CD

GitHub Actions should eventually:

1. Install dependencies.
2. Run lint.
3. Run static/type checks.
4. Run unit tests.
5. Run integration/API tests.
6. Build Docker image.

The pipeline must fail when tests fail.

---

# 86. Docker

The backend must be containerized.

Target:

Docker
 ↓
FastAPI
 ↓
Supabase PostgreSQL

PostgreSQL does not need to run inside Docker because Supabase provides the hosted database.

Docker Compose should be available for local backend development.

---

# 87. Deployment

Deployment must prioritize:

1. Free tier.
2. Docker compatibility.
3. FastAPI compatibility.
4. HTTPS.
5. Environment variable support.
6. Reliability.

Vercel can be evaluated, but the backend must not depend on Vercel-specific architecture.

If another free Docker-compatible platform is technically better for FastAPI, use it.

The backend should eventually be accessible through:

https://api.<domain>

---

# 88. Expo Authentication Storage

The Expo app should use secure device storage for:

- Access token
- Refresh token

Do not store authentication credentials in ordinary unencrypted storage when secure storage is available.

---

# 89. Expo API Client

Create a centralized API client.

Responsibilities:

- Base URL
- Authorization header
- Request handling
- Response parsing
- Error handling
- Access-token refresh
- Retry after token refresh where appropriate

Do not manually attach JWT headers in every screen.

---

# 90. Expo Repository Integration

Create API repositories corresponding to the existing repository interfaces.

Example:

repositories/

interfaces/

mock/

api/

api/
├── authRepository.ts
├── accountRepository.ts
├── categoryRepository.ts
├── transactionRepository.ts
├── budgetRepository.ts
└── reportRepository.ts

Screens should continue using the same hooks/repository abstraction.

---

# 91. Implementation Order

Follow this order.

## Phase 1 — Backend Foundation

1. Create backend directory.
2. Initialize Python project.
3. Configure FastAPI.
4. Configure environment settings.
5. Configure logging.
6. Configure database.
7. Configure SQLAlchemy.
8. Configure Alembic.
9. Configure `/api/v1`.
10. Configure OpenAPI.

## Phase 2 — Authentication

11. User model.
12. Password hashing.
13. JWT access tokens.
14. Refresh tokens.
15. Register.
16. Login.
17. Refresh.
18. Logout.
19. `/auth/me`.
20. Authentication dependencies.
21. Delete account.

## Phase 3 — Financial Core

22. Accounts.
23. Categories.
24. Transactions.
25. Account balance updates.
26. Transaction filtering.
27. Transaction search.
28. Pagination.
29. Sorting.

## Phase 4 — Budgeting

30. Monthly budgets.
31. Category budgets.
32. Budget calculations.
33. Budget status.

## Phase 5 — Recurring

34. Recurring transaction model.
35. Daily recurrence.
36. Monthly recurrence.
37. Duplicate-processing protection.

## Phase 6 — Analytics

38. Dashboard.
39. Weekly reports.
40. Category aggregation.
41. Account aggregation.
42. Spending trends.

## Phase 7 — Product Features

43. Notifications.
44. Tracking streak.
45. Achievements.
46. Gamification.

## Phase 8 — Quality

47. Unit tests.
48. API tests.
49. Security tests.
50. Integration tests.
51. CI.

## Phase 9 — Infrastructure

52. Dockerfile.
53. Docker Compose.
54. Production configuration.
55. Deployment.
56. HTTPS.

## Phase 10 — Mobile Integration

57. API client.
58. Authentication integration.
59. Account API integration.
60. Category API integration.
61. Transaction API integration.
62. Budget API integration.
63. Dashboard API integration.
64. Reports API integration.
65. Remove production dependency on mock data.

---

# 92. MVP Definition of Done

The MVP backend is complete when:

## Authentication

- User can register.
- User can login.
- Password is securely hashed.
- Access JWT works.
- Refresh token works.
- Logout invalidates refresh session.
- `/auth/me` works.
- User can delete account.
- Cross-user access is prevented.

## Accounts

- User can create accounts.
- User can edit accounts.
- User can deactivate/delete accounts safely.
- Starting balance works.
- Account balance updates correctly.

## Categories

- Default categories are created.
- User can create categories.
- User can edit categories.
- User can deactivate categories.

## Transactions

- User can create income.
- User can create expenses.
- User can edit transactions.
- User can delete transactions.
- Merchant works.
- Note works.
- Category works.
- Account works.
- Date works.
- Filtering works.
- Searching works.
- Pagination works.
- Sorting works.

## Budgets

- Monthly overall budget works.
- Category budgets work.
- Spending calculation works.
- Remaining amount works.
- Percentage works.
- Budget status works.

## Recurring

- Daily recurrence works.
- Monthly recurrence works.
- Duplicate generation is prevented.

## Analytics

- Dashboard works.
- Weekly reports work.
- Category aggregation works.
- Account aggregation works.
- Spending trends work.

## Product

- Notifications foundation works.
- Tracking streak works.
- Achievements work.
- Gamification works.

## Infrastructure

- Swagger works.
- Tests pass.
- Docker builds.
- FastAPI runs inside Docker.
- Database migrations work.
- Production environment works.

## Mobile

- Expo authentication works.
- Tokens are securely stored.
- API repository works.
- Mock repository can be replaced without rewriting screens.
- End-to-end transaction flow works.

---

# 93. Future Extensions

The architecture should remain extensible for:

### Authentication

- Email verification
- Forgot password
- Google login
- Apple login

### Profile

- Profile photo
- Additional profile settings

### Transactions

- Receipt images
- OCR
- Transfers
- Advanced recurrence

### Classification

- Subcategories
- Hierarchical categories
- Contexts
- Tags
- Locations
- Projects

### Currency

- Multi-currency

### Analytics

- Monthly reports
- Yearly reports
- Custom date ranges
- Advanced spending analytics
- Financial insights

### Product

- Push notifications
- Financial goals
- Advanced gamification
- AI-powered expense insights

---

# 94. Critical AI Implementation Rules

The implementation agent MUST:

1. Read this entire PRD before coding.
2. Inspect the existing Expo repository.
3. Inspect existing frontend repository interfaces.
4. Inspect existing mock data.
5. Preserve existing frontend architecture.
6. Preserve existing UI functionality.
7. Do not rewrite screens unnecessarily.
8. Do not invent API contracts.
9. Do not hardcode financial values.
10. Keep financial calculations authoritative on the backend.
11. Never store plain-text passwords.
12. Never expose secrets.
13. Never allow cross-user data access.
14. Use database transactions for financial mutations.
15. Protect account balance updates against concurrent modifications.
16. Write tests alongside implementation.
17. Keep migrations version-controlled.
18. Keep Docker configuration reproducible.
19. Keep mock repositories available until API integration is complete.
20. Do not implement future features unless explicitly requested.
21. If a product requirement is genuinely ambiguous, ask before making a permanent architectural decision.
22. Prefer the simplest implementation that satisfies the MVP requirements.

---

# 95. Final Product Data Model

The MVP intentionally uses a simple transaction model:

                    USER
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       ACCOUNTS   CATEGORIES   TRANSACTIONS
                                  │
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
                 ACCOUNT       CATEGORY        NOTE
                    │
                    ↓
                  AMOUNT
                    │
                    ↓
                  TYPE
                    │
                    ↓
                   DATE

A transaction can look like:

Amount:
₹500

Type:
EXPENSE

Category:
Petrol

Account:
HDFC Bank

Merchant:
Indian Oil

Note:
Filled petrol before going to office

Date:
2026-08-10

This is the canonical MVP transaction model.

---

# 96. Product Design Principle

Keep data entry simple.

A user should be able to add an expense quickly:

Amount
₹500

Category
Petrol

Account
HDFC Bank

Date
Today

Optional:
Merchant

Optional:
Note

The user should NOT be forced to fill:

- Context
- Subcategory
- Tags
- Location
- Project

unless those features are introduced in a future version.

The goal is:

Simple input
+
Powerful backend
+
Extensible architecture