# Expense Tracker — API Specification

Version: 1.0
Status: MVP
Base URL: `/api/v1`
Backend: FastAPI
Authentication: JWT Access Token + Refresh Token

---

# 1. Purpose

This document defines the HTTP API contract between the Expense Tracker Expo application and the FastAPI backend.

The API specification is the contract between:

```text
React Native / Expo
        ↓
API Client
        ↓ HTTPS
FastAPI
        ↓
Service Layer
        ↓
PostgreSQL / Supabase
```

The frontend must not depend on FastAPI's internal implementation details.

Changes to the API contract must be deliberate and versioned.

---

# 2. API Conventions

## Base URL

All MVP endpoints use:

```text
/api/v1
```

Examples:

```text
/api/v1/auth/login
/api/v1/accounts
/api/v1/transactions
```

## Content Type

Requests containing a body should use:

```http
Content-Type: application/json
```

Responses use:

```http
Content-Type: application/json
```

## Authentication

Authenticated endpoints require:

```http
Authorization: Bearer <access_token>
```

Authentication endpoints such as registration and login do not require an access token.

---

# 3. Standard HTTP Status Codes

Use:

| Status | Meaning |
|---|---|
| `200` | Successful request |
| `201` | Resource created |
| `204` | Successful request with no response body |
| `400` | Invalid request |
| `401` | Authentication required/invalid |
| `403` | Authenticated but not allowed |
| `404` | Resource not found |
| `409` | Resource conflict |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

# 4. Standard Error Format

Application errors should use:

```json
{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction not found"
  }
}
```

Validation errors should provide enough information for the frontend to identify invalid fields without exposing internal implementation details.

Example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "fields": {
      "amount": "Amount must be greater than zero"
    }
  }
}
```

Never expose:

- Stack traces
- SQL errors
- Password hashes
- JWT secrets
- Database credentials
- Internal infrastructure details

---

# 5. Authentication API

## 5.1 Register

```http
POST /api/v1/auth/register
```

Authentication:

```text
Not required
```

Request:

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!"
}
```

Validation:

- Name is required.
- Email must be valid.
- Email must be normalized.
- Email must be unique.
- Password must satisfy password-strength requirements.
- `confirm_password` must match `password`.

Backend actions:

1. Validate request.
2. Normalize email.
3. Check duplicate email.
4. Hash password using Argon2id.
5. Create user.
6. Create default categories.
7. Return safe user information.

Email verification is not implemented in MVP.

Response:

```http
201 Created
```

```json
{
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

Possible errors:

```text
409 USER_ALREADY_EXISTS
422 VALIDATION_ERROR
```

---

# 6. Login

```http
POST /api/v1/auth/login
```

Authentication:

```text
Not required
```

Request:

```json
{
  "email": "john@example.com",
  "password": "StrongPassword123!"
}
```

Response:

```http
200 OK
```

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "refresh-token",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

Invalid credentials:

```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

Return:

```http
401 Unauthorized
```

Do not reveal whether the email exists.

---

# 7. Refresh Access Token

```http
POST /api/v1/auth/refresh
```

Authentication:

```text
Access token not required.
Valid refresh token required.
```

Request:

```json
{
  "refresh_token": "refresh-token"
}
```

Response:

```json
{
  "access_token": "new-access-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

The backend must:

1. Validate the refresh token.
2. Verify it is not expired.
3. Verify it is not revoked.
4. Verify the associated user is active.
5. Issue a new access token.

Possible errors:

```text
401 AUTH_INVALID_REFRESH_TOKEN
401 AUTH_REFRESH_TOKEN_EXPIRED
401 AUTH_REFRESH_TOKEN_REVOKED
```

---

# 8. Logout

```http
POST /api/v1/auth/logout
```

Authentication:

```text
Access token required.
```

Request:

```json
{
  "refresh_token": "refresh-token"
}
```

Backend:

1. Authenticate user.
2. Revoke the supplied refresh-token session.
3. Return success.

Response:

```http
204 No Content
```

The Expo client must also remove stored tokens.

---

# 9. Current User

```http
GET /api/v1/auth/me
```

Authentication:

```text
Required
```

Response:

```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john@example.com"
}
```

---

# 10. Delete Account

```http
DELETE /api/v1/auth/account
```

Authentication:

```text
Required
```

Response:

```http
204 No Content
```

The backend must:

- Invalidate authentication sessions.
- Prevent future access.
- Remove or anonymize user-owned data according to the application's deletion policy.
- Ensure deleted users cannot access the API.

---

# 11. Accounts API

Accounts represent:

- Bank accounts
- Cash
- UPI wallets
- Credit cards
- Debit cards
- Other financial accounts

---

# 12. List Accounts

```http
GET /api/v1/accounts
```

Authentication:

```text
Required
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "HDFC Bank",
      "type": "BANK",
      "balance": 50000.00,
      "currency": "INR",
      "is_active": true,
      "created_at": "2026-08-10T10:00:00Z",
      "updated_at": "2026-08-10T10:00:00Z"
    }
  ]
}
```

Only accounts belonging to the authenticated user may be returned.

---

# 13. Get Account

```http
GET /api/v1/accounts/{account_id}
```

Authentication:

```text
Required
```

Response:

```json
{
  "id": "uuid",
  "name": "HDFC Bank",
  "type": "BANK",
  "balance": 50000.00,
  "currency": "INR",
  "is_active": true,
  "created_at": "2026-08-10T10:00:00Z",
  "updated_at": "2026-08-10T10:00:00Z"
}
```

A user must never be able to retrieve another user's account.

---

# 14. Create Account

```http
POST /api/v1/accounts
```

Request:

```json
{
  "name": "HDFC Bank",
  "type": "BANK",
  "starting_balance": 50000.00
}
```

MVP currency is always:

```text
INR
```

Response:

```http
201 Created
```

```json
{
  "id": "uuid",
  "name": "HDFC Bank",
  "type": "BANK",
  "balance": 50000.00,
  "currency": "INR",
  "is_active": true,
  "created_at": "2026-08-10T10:00:00Z",
  "updated_at": "2026-08-10T10:00:00Z"
}
```

---

# 15. Update Account

```http
PATCH /api/v1/accounts/{account_id}
```

Request:

```json
{
  "name": "HDFC Salary Account"
}
```

Do not allow arbitrary balance modification through the normal update endpoint.

Financial balance changes must happen through financial operations.

Response:

```json
{
  "id": "uuid",
  "name": "HDFC Salary Account",
  "type": "BANK",
  "balance": 50000.00,
  "currency": "INR",
  "is_active": true,
  "created_at": "2026-08-10T10:00:00Z",
  "updated_at": "2026-08-10T10:00:00Z"
}
```

---

# 16. Delete / Deactivate Account

```http
DELETE /api/v1/accounts/{account_id}
```

If the account has historical transactions, prefer deactivation.

Response:

```http
204 No Content
```

Historical transactions must remain valid.

---

# 17. Categories API

Categories are flat in MVP.

There are no:

- Subcategories
- Parent categories
- Category hierarchy

---

# 18. List Categories

```http
GET /api/v1/categories
```

Optional filter:

```text
type=EXPENSE
type=INCOME
```

Examples:

```text
GET /api/v1/categories?type=EXPENSE
GET /api/v1/categories?type=INCOME
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Petrol",
      "type": "EXPENSE",
      "icon": "fuel",
      "color": "#7C5CFC",
      "is_active": true,
      "created_at": "2026-08-10T10:00:00Z",
      "updated_at": "2026-08-10T10:00:00Z"
    }
  ]
}
```

---

# 19. Create Category

```http
POST /api/v1/categories
```

Request:

```json
{
  "name": "Coffee",
  "type": "EXPENSE",
  "icon": "coffee",
  "color": "#8B5CF6"
}
```

Response:

```http
201 Created
```

---

# 20. Update Category

```http
PATCH /api/v1/categories/{category_id}
```

Request:

```json
{
  "name": "Coffee & Drinks",
  "icon": "coffee"
}
```

Existing transactions must continue referencing the same category.

---

# 21. Delete / Deactivate Category

```http
DELETE /api/v1/categories/{category_id}
```

If historical transactions use the category, prefer deactivation.

Response:

```http
204 No Content
```

---

# 22. Transactions API

Transactions are the central financial resource.

Supported types:

```text
EXPENSE
INCOME
```

A transaction contains:

```text
Account
Category
Amount
Type
Merchant
Note
Date
```

---

# 23. List Transactions

```http
GET /api/v1/transactions
```

Authentication:

```text
Required
```

Default:

```text
page=1
limit=20
sort=transaction_date
order=desc
```

Example:

```http
GET /api/v1/transactions?page=1&limit=20&sort=transaction_date&order=desc
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "account": {
        "id": "uuid",
        "name": "HDFC Bank"
      },
      "category": {
        "id": "uuid",
        "name": "Petrol",
        "type": "EXPENSE"
      },
      "amount": 500.00,
      "type": "EXPENSE",
      "merchant": "Indian Oil",
      "note": "Filled petrol before office",
      "transaction_date": "2026-08-10T08:30:00Z",
      "created_at": "2026-08-10T08:30:00Z",
      "updated_at": "2026-08-10T08:30:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1,
  "total_pages": 1
}
```

---

# 24. Transaction Filters

Supported query parameters:

```text
page
limit
category_id
account_id
type
start_date
end_date
min_amount
max_amount
search
sort
order
```

Example:

```http
GET /api/v1/transactions?category_id=uuid
```

Returns transactions for the selected category.

Example:

```http
GET /api/v1/transactions?account_id=uuid
```

Returns transactions for the selected account.

Example:

```http
GET /api/v1/transactions?type=EXPENSE
```

Returns expenses only.

Example:

```http
GET /api/v1/transactions?start_date=2026-08-01&end_date=2026-08-31
```

Returns transactions in the specified date range.

---

# 25. Transaction Search

Search parameter:

```text
search
```

Search should initially cover:

- Merchant
- Note
- Category name

Example:

```http
GET /api/v1/transactions?search=hostel
```

This can find a transaction such as:

```text
Category: Electricity
Merchant: Hostel
Note: August electricity bill
```

Search must be case-insensitive.

---

# 26. Transaction Sorting

Supported fields:

```text
transaction_date
amount
created_at
```

Example:

```http
GET /api/v1/transactions?sort=amount&order=desc
```

Allowed order:

```text
asc
desc
```

---

# 27. Pagination

Default:

```text
page=1
limit=20
```

Maximum:

```text
limit=100
```

The server must enforce the maximum.

Response:

```json
{
  "items": [],
  "page": 1,
  "limit": 20,
  "total": 100,
  "total_pages": 5
}
```

---

# 28. Get Transaction

```http
GET /api/v1/transactions/{transaction_id}
```

Response:

```json
{
  "id": "uuid",
  "account": {
    "id": "uuid",
    "name": "HDFC Bank"
  },
  "category": {
    "id": "uuid",
    "name": "Petrol",
    "type": "EXPENSE"
  },
  "amount": 500.00,
  "type": "EXPENSE",
  "merchant": "Indian Oil",
  "note": "Filled petrol before office",
  "transaction_date": "2026-08-10T08:30:00Z",
  "created_at": "2026-08-10T08:30:00Z",
  "updated_at": "2026-08-10T08:30:00Z"
}
```

---

# 29. Create Expense

```http
POST /api/v1/transactions
```

Request:

```json
{
  "account_id": "account-uuid",
  "category_id": "category-uuid",
  "amount": 500.00,
  "type": "EXPENSE",
  "merchant": "Indian Oil",
  "note": "Filled petrol before office",
  "transaction_date": "2026-08-10T08:30:00+05:30"
}
```

Backend must:

1. Authenticate user.
2. Validate account ownership.
3. Validate category ownership.
4. Validate amount.
5. Create transaction.
6. Decrease account balance.
7. Update relevant budget/gamification state where required.
8. Commit atomically.

Response:

```http
201 Created
```

---

# 30. Create Income

Use the same endpoint:

```http
POST /api/v1/transactions
```

Request:

```json
{
  "account_id": "account-uuid",
  "category_id": "salary-category-uuid",
  "amount": 50000.00,
  "type": "INCOME",
  "merchant": "Company",
  "note": "August salary",
  "transaction_date": "2026-08-01T10:00:00+05:30"
}
```

Backend must increase the account balance atomically.

---

# 31. Update Transaction

```http
PATCH /api/v1/transactions/{transaction_id}
```

Request:

```json
{
  "amount": 550.00,
  "category_id": "new-category-uuid",
  "merchant": "Indian Oil",
  "note": "Updated note"
}
```

If the update changes:

- Amount
- Type
- Account

the backend must correctly reverse the old financial effect and apply the new financial effect inside one database transaction.

Example:

```text
Old:
HDFC
Expense
₹500

New:
SBI
Expense
₹550
```

The backend must:

1. Reverse ₹500 from HDFC.
2. Apply ₹550 to SBI.
3. Update the transaction.
4. Commit atomically.

---

# 32. Delete Transaction

```http
DELETE /api/v1/transactions/{transaction_id}
```

The backend must reverse the transaction's financial effect before deleting it.

Example:

```text
Original expense:
₹500

Delete transaction:

Account balance:
+₹500
```

All operations must be atomic.

Response:

```http
204 No Content
```

---

# 33. Budgets API

## List Budgets

```http
GET /api/v1/budgets
```

Optional:

```text
start_date
end_date
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "August Budget",
      "amount": 45000.00,
      "period": "MONTHLY",
      "start_date": "2026-08-01",
      "end_date": "2026-08-31",
      "spent": 33600.00,
      "remaining": 11400.00,
      "percentage_used": 74.67,
      "status": "HEALTHY"
    }
  ]
}
```

---

# 34. Create Budget

```http
POST /api/v1/budgets
```

Request:

```json
{
  "name": "August Budget",
  "amount": 45000.00,
  "period": "MONTHLY",
  "start_date": "2026-08-01",
  "end_date": "2026-08-31",
  "categories": [
    {
      "category_id": "food-category-uuid",
      "amount": 10000.00
    },
    {
      "category_id": "petrol-category-uuid",
      "amount": 4000.00
    }
  ]
}
```

Response:

```http
201 Created
```

---

# 35. Get Budget

```http
GET /api/v1/budgets/{budget_id}
```

Response should include:

- Budget amount
- Amount spent
- Remaining amount
- Percentage used
- Status
- Category allocations
- Category spending

---

# 36. Update Budget

```http
PATCH /api/v1/budgets/{budget_id}
```

Request:

```json
{
  "amount": 50000.00
}
```

The backend recalculates the resulting budget status.

---

# 37. Delete Budget

```http
DELETE /api/v1/budgets/{budget_id}
```

Response:

```http
204 No Content
```

---

# 38. Budget Status

Backend-calculated statuses:

```text
HEALTHY
WARNING
NEAR_LIMIT
OVER_BUDGET
```

The exact thresholds should be defined centrally in backend business logic.

The frontend must not independently calculate the authoritative budget status.

---

# 39. Recurring Transactions API

## List

```http
GET /api/v1/recurring-transactions
```

## Get

```http
GET /api/v1/recurring-transactions/{id}
```

## Create

```http
POST /api/v1/recurring-transactions
```

## Update

```http
PATCH /api/v1/recurring-transactions/{id}
```

## Delete / Deactivate

```http
DELETE /api/v1/recurring-transactions/{id}
```

---

# 40. Create Recurring Transaction

Request:

```json
{
  "account_id": "account-uuid",
  "category_id": "petrol-category-uuid",
  "type": "EXPENSE",
  "amount": 500.00,
  "merchant": "Indian Oil",
  "note": "Daily petrol",
  "frequency": "DAILY",
  "start_date": "2026-08-10"
}
```

Monthly example:

```json
{
  "account_id": "account-uuid",
  "category_id": "rent-category-uuid",
  "type": "EXPENSE",
  "amount": 12000.00,
  "merchant": "Landlord",
  "note": "Monthly rent",
  "frequency": "MONTHLY",
  "start_date": "2026-08-01"
}
```

---

# 41. Dashboard API

```http
GET /api/v1/dashboard
```

Authentication:

```text
Required
```

The backend calculates:

- Total balance
- Total income
- Total expenses
- Net savings
- Savings percentage
- Budget summary
- Top categories
- Spending trend
- Recent transactions
- Tracking streak

Response:

```json
{
  "balance": 87450.00,
  "income": 109000.00,
  "expenses": 39219.00,
  "savings": 69781.00,
  "savings_percentage": 63.93,
  "budget": {
    "amount": 45000.00,
    "spent": 33600.00,
    "remaining": 11400.00,
    "percentage_used": 74.67,
    "status": "HEALTHY"
  },
  "top_categories": [],
  "recent_transactions": [],
  "streak": {
    "current": 7,
    "longest": 12
  }
}
```

Values are examples only. The backend must calculate real values.

---

# 42. Reports API

MVP supports weekly reports.

```http
GET /api/v1/reports?period=week
```

Response should include:

```json
{
  "period": {
    "type": "week",
    "start_date": "2026-08-03",
    "end_date": "2026-08-09"
  },
  "income": 25000.00,
  "expenses": 9200.00,
  "savings": 15800.00,
  "categories": [],
  "accounts": [],
  "trend": []
}
```

---

# 43. Report Aggregations

Reports must support aggregation by:

- Category
- Account
- Date

Example category aggregation:

```json
[
  {
    "category_id": "uuid",
    "category_name": "Petrol",
    "amount": 3500.00,
    "percentage": 12.5
  },
  {
    "category_id": "uuid",
    "category_name": "Food",
    "amount": 7200.00,
    "percentage": 25.7
  }
]
```

---

# 44. Notifications API

## List

```http
GET /api/v1/notifications
```

Optional:

```text
is_read=true
is_read=false
page=1
limit=20
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "type": "BUDGET_WARNING",
      "title": "Budget almost reached",
      "message": "Your Food budget is 85% used.",
      "data": {},
      "is_read": false,
      "created_at": "2026-08-10T10:00:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1,
  "total_pages": 1
}
```

## Mark Read

```http
PATCH /api/v1/notifications/{notification_id}/read
```

Response:

```http
204 No Content
```

## Mark All Read

```http
PATCH /api/v1/notifications/read-all
```

Response:

```http
204 No Content
```

---

# 45. Gamification API

## Get Gamification Summary

```http
GET /api/v1/gamification
```

Response:

```json
{
  "streak": {
    "current": 7,
    "longest": 12
  },
  "achievements": [
    {
      "code": "SEVEN_DAY_STREAK",
      "name": "7 Day Streak",
      "description": "Tracked expenses for seven consecutive days.",
      "unlocked": true,
      "unlocked_at": "2026-08-10T10:00:00Z"
    }
  ]
}
```

Achievement unlocking is controlled by the backend.

---

# 46. Health API

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

This endpoint does not require authentication.

A separate readiness endpoint may be added for production infrastructure.

---

# 47. Authentication Requirements

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

The backend must:

1. Validate JWT signature.
2. Validate expiration.
3. Validate token type.
4. Resolve user.
5. Verify user is active.
6. Attach authenticated user to request context.

---

# 48. Authorization Requirements

Every user-owned resource must be scoped to the authenticated user.

Example:

```text
User A
  ↓
GET /transactions/{User B transaction}
```

Must never return User B's data.

Use ownership-aware queries rather than fetching a resource globally and checking ownership later where practical.

---

# 49. API Security

Authentication endpoints should have reasonable rate limiting.

Especially:

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
```

Never expose:

- Passwords
- Password hashes
- JWT secrets
- Raw refresh tokens
- Database credentials

---

# 50. CORS

Development may allow the required Expo development origins.

Production must use an explicit allowlist.

Do not use unrestricted:

```python
allow_origins=["*"]
```

for authenticated production APIs unless there is a deliberate reason.

---

# 51. API Idempotency

Financial mutation endpoints must be designed carefully against duplicate requests.

Especially:

```text
POST /transactions
POST /recurring-transactions processing
```

The backend should support an idempotency strategy where needed so network retries cannot accidentally create duplicate financial transactions.

The exact mechanism may be implemented using an idempotency key/request identifier.

---

# 52. Financial Mutation Rules

Creating, updating, or deleting a transaction must execute financial changes atomically.

Example:

```text
Create Expense
    ↓
Validate account
    ↓
Validate category
    ↓
Create transaction
    ↓
Decrease account balance
    ↓
Update related budget/gamification state
    ↓
Commit
```

Failure anywhere must roll back the entire operation.

---

# 53. API Response Consistency

Responses should use consistent naming.

Use:

```text
snake_case
```

for JSON fields.

Examples:

```text
user_id
account_id
category_id
transaction_date
created_at
updated_at
```

Do not mix:

```text
userId
user_id
```

within the same API.

---

# 54. Date and Time

API timestamps should use ISO 8601.

Example:

```text
2026-08-10T08:30:00Z
```

Timezone-aware input is allowed:

```text
2026-08-10T08:30:00+05:30
```

The backend normalizes timestamps according to the application's timezone policy.

---

# 55. Money Representation

Money values in JSON should be represented as numeric decimal values.

Example:

```json
{
  "amount": 500.00
}
```

The backend must use PostgreSQL `NUMERIC` and Python `Decimal` for financial calculations.

Do not use floating-point arithmetic for authoritative financial calculations.

---

# 56. API Validation

Pydantic schemas must validate:

- Required fields
- String lengths
- Enum values
- Positive amounts
- Date ranges
- Pagination limits
- Search length
- UUID formats

Database constraints provide a second layer of protection.

---

# 57. API Versioning

All MVP API routes use:

```text
/api/v1/
```

Breaking changes must use a new API version.

Example:

```text
/api/v2/
```

Do not silently break existing mobile clients.

---

# 58. API Documentation

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

Swagger/OpenAPI is the authoritative machine-readable representation of the API contract.

---

# 59. Endpoint Summary

```text
AUTH
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
DELETE /api/v1/auth/account

ACCOUNTS
GET    /api/v1/accounts
GET    /api/v1/accounts/{id}
POST   /api/v1/accounts
PATCH  /api/v1/accounts/{id}
DELETE /api/v1/accounts/{id}

CATEGORIES
GET    /api/v1/categories
POST   /api/v1/categories
PATCH  /api/v1/categories/{id}
DELETE /api/v1/categories/{id}

TRANSACTIONS
GET    /api/v1/transactions
GET    /api/v1/transactions/{id}
POST   /api/v1/transactions
PATCH  /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}

BUDGETS
GET    /api/v1/budgets
GET    /api/v1/budgets/{id}
POST   /api/v1/budgets
PATCH  /api/v1/budgets/{id}
DELETE /api/v1/budgets/{id}

RECURRING
GET    /api/v1/recurring-transactions
GET    /api/v1/recurring-transactions/{id}
POST   /api/v1/recurring-transactions
PATCH  /api/v1/recurring-transactions/{id}
DELETE /api/v1/recurring-transactions/{id}

DASHBOARD
GET    /api/v1/dashboard

REPORTS
GET    /api/v1/reports

NOTIFICATIONS
GET    /api/v1/notifications
PATCH  /api/v1/notifications/{id}/read
PATCH  /api/v1/notifications/read-all

GAMIFICATION
GET    /api/v1/gamification

HEALTH
GET    /health
```

---

# 60. API Acceptance Criteria

The API contract is ready when:

- All MVP endpoints are defined.
- Authentication requirements are defined.
- Request schemas are defined.
- Response schemas are defined.
- Error formats are defined.
- Pagination is defined.
- Filtering is defined.
- Sorting is defined.
- Search behavior is defined.
- Financial mutation behavior is defined.
- User ownership requirements are defined.
- JWT behavior is defined.
- Refresh-token behavior is defined.
- Account balance behavior is defined.
- API versioning is defined.
- OpenAPI/Swagger requirements are defined.
- The API matches `BACKEND_PRD.md`.
- The API data structures match `DATABASE_SCHEMA.md`.
- No subcategory, context, tag, or hierarchy requirements are introduced into the MVP API.

---

# 61. Implementation Rule

The backend implementation must treat:

```text
BACKEND_PRD.md
DATABASE_SCHEMA.md
API_SPEC.md
```

as the backend product and API contract.

If implementation details are unclear but the API contract is clear, choose a clean internal implementation without changing the API.

If a requirement conflicts between documents, stop and resolve the conflict before implementing the affected feature.

Do not silently invent API behavior.
