# Expense Tracker — AI Implementation Rules

Version: 1.0
Status: MVP
Applies to: Antigravity, Claude Code, Codex, OpenCode, and other AI coding agents

---

# 1. Purpose

This document defines how an AI coding agent must work on the Expense Tracker backend.

The agent must treat the backend documentation as the source of truth:

```text
docs/BACKEND_PRD.md
docs/DATABASE_SCHEMA.md
docs/API_SPEC.md
docs/ARCHITECTURE.md
docs/DEVELOPMENT_PLAN.md
```

The agent must not treat its own assumptions as product requirements.

---

# 2. First Action: Read the Documentation

Before writing or modifying backend code, read all available backend documentation.

Required:

```text
BACKEND_PRD.md
DATABASE_SCHEMA.md
API_SPEC.md
ARCHITECTURE.md
DEVELOPMENT_PLAN.md
```

Then inspect the existing repository structure.

Do not start implementation after reading only one document.

---

# 3. Source-of-Truth Hierarchy

When information is consistent:

```text
BACKEND_PRD
DATABASE_SCHEMA
API_SPEC
ARCHITECTURE
DEVELOPMENT_PLAN
```

When there is a conflict:

1. Identify the conflict.
2. Do not silently choose an interpretation.
3. Explain which documents conflict.
4. Ask for clarification if the conflict changes product behavior, API behavior, database behavior, or security.
5. If the conflict is only an implementation detail and the product/API requirements are unambiguous, choose the simplest technically sound implementation.

Never silently introduce a breaking change.

---

# 4. Do Not Invent Requirements

Do not add features because they are common in expense applications.

Examples that must not be added without explicit approval:

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
UPI import
Investment tracking
Credit score
```

The MVP is intentionally limited.

---

# 5. Current Transaction Model

The current transaction model is:

```text
Transaction
├── Account
├── Category
├── Amount
├── Type
├── Merchant
├── Note
└── Date
```

Do not introduce:

```text
Subcategory
Context
Tags
Location
Project
```

unless the product documentation is explicitly changed.

---

# 6. Current Authentication Model

MVP authentication is:

```text
Email
+
Password
+
JWT Access Token
+
Refresh Token
```

Do not implement social login in the MVP.

Do not implement email verification.

Do not implement forgot-password flow.

Future authentication must be introduced deliberately.

---

# 7. Work in Phases

Follow:

```text
DEVELOPMENT_PLAN.md
```

Do not jump directly to later phases unless explicitly requested.

The preferred sequence is:

```text
Foundation
↓
Database
↓
Security
↓
Authentication
↓
Accounts
↓
Categories
↓
Transactions
↓
Filtering/Search
↓
Budgets
↓
Dashboard
↓
Reports
↓
Recurring Transactions
↓
Notifications
↓
Gamification
↓
Testing
↓
Docker
↓
Deployment
↓
Expo Integration
```

---

# 8. Before Editing Code

Before implementing a feature:

1. Identify the relevant requirements.
2. Identify affected database models.
3. Identify affected API endpoints.
4. Identify affected services.
5. Identify required migrations.
6. Identify required tests.
7. Inspect existing implementation before changing it.

Avoid blind rewrites.

---

# 9. Make Small, Reviewable Changes

Prefer focused changes.

Good:

```text
Implement authentication foundation
```

then:

```text
Implement registration
```

then:

```text
Implement login
```

Avoid:

```text
Rewrite the entire backend
```

unless explicitly requested.

---

# 10. Do Not Rewrite Working Code Without Reason

If existing code already satisfies the documented requirements:

- Keep it.
- Improve only where necessary.
- Avoid unnecessary refactoring.
- Avoid changing public behavior without reason.

Refactoring must have a concrete benefit.

---

# 11. Architecture Rules

Follow:

```text
Router
   ↓
Service
   ↓
Repository
   ↓
Database
```

Routers:

- HTTP concerns only.
- Request/response handling.
- Dependency injection.
- Status codes.

Services:

- Business logic.
- Financial logic.
- Cross-repository operations.

Repositories:

- Database access.

Do not put complex financial logic inside routers.

---

# 12. Database Rules

Use:

```text
PostgreSQL
SQLAlchemy 2.x
Alembic
```

All schema changes require migrations.

Never silently modify production schema manually.

Migration flow:

```text
Modify model
↓
Create Alembic migration
↓
Review migration
↓
Apply migration
↓
Run tests
```

Never modify an already-applied production migration.

---

# 13. Financial Data Rules

Financial correctness is the highest priority.

Use:

```python
Decimal
```

for Python financial calculations.

Use:

```text
NUMERIC(14,2)
```

in PostgreSQL.

Never use:

```python
float
```

for authoritative money calculations.

---

# 14. Atomic Financial Operations

Transaction operations must be atomic.

Create:

```text
Create transaction
+
Update account balance
+
Update dependent state
```

inside the same database transaction where required.

If any operation fails:

```text
ROLLBACK
```

The account balance must never become inconsistent with transactions.

---

# 15. Transaction Update Rule

If an existing transaction changes amount, account, or type, the old financial effect must be reversed before applying the new effect.

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

This must be atomic.

Never simply update the transaction row.

---

# 16. Transaction Delete Rule

Deleting an expense must restore the amount to the account balance.

Example:

```text
Expense = ₹500

Delete expense
    ↓
Account balance +₹500
```

Deleting income must reverse the income effect.

---

# 17. User Isolation

Every user-owned resource must be scoped to the authenticated user.

Resources include:

```text
Accounts
Categories
Transactions
Budgets
Recurring Transactions
Notifications
Streaks
Achievements
Refresh Tokens
```

Never allow:

```text
User A → User B's data
```

Ownership checks must exist in backend logic.

---

# 18. Never Trust Client Ownership

Never accept a `user_id` from the mobile client as the source of authorization.

The backend must derive the user from:

```text
JWT → authenticated user
```

Example:

```text
current_user.id
```

Use that ID for user-scoped queries.

---

# 19. API Contract Rules

The API contract is defined in:

```text
docs/API_SPEC.md
```

Do not change:

```text
Endpoint paths
HTTP methods
Request fields
Response fields
Authentication requirements
```

without updating the API specification.

---

# 20. API Versioning

All MVP APIs use:

```text
/api/v1
```

Do not create unversioned feature endpoints.

Breaking API changes require a new version.

---

# 21. Pydantic and SQLAlchemy Separation

Do not return SQLAlchemy models directly as API contracts.

Use:

```text
SQLAlchemy
    ↓
Service
    ↓
Pydantic Response Schema
    ↓
FastAPI
```

This keeps persistence implementation separate from the public API.

---

# 22. Validation

Validate at multiple levels:

```text
API / Pydantic
       ↓
Business logic
       ↓
Database constraints
```

Never rely only on frontend validation.

---

# 23. Error Handling

Use consistent application errors.

Do not expose:

```text
Stack traces
SQL queries
Database errors
Internal filesystem paths
Secrets
```

Return documented API error responses.

---

# 24. Security Rules

Never commit:

```text
.env
JWT secrets
Database passwords
API keys
Private keys
Tokens
```

Use environment variables.

Provide:

```text
.env.example
```

with placeholders only.

---

# 25. Password Rules

Passwords must:

- Never be logged.
- Never be returned in API responses.
- Never be stored in plaintext.

Use:

```text
Argon2id
```

for password hashing.

---

# 26. JWT Rules

Access tokens should be short-lived.

Do not put sensitive data inside JWT claims.

Required concepts:

```text
sub
iat
exp
type
```

Validate:

```text
Signature
Expiration
Token type
User status
```

---

# 27. Refresh Token Rules

Store refresh-token hashes, not reusable raw refresh tokens.

Refresh tokens must support:

```text
Expiration
Revocation
User association
```

Logout must revoke the refresh-token session.

---

# 28. Logging Rules

Logs may contain:

```text
Request ID
Route
HTTP method
Status
Duration
Error category
```

Logs must not contain:

```text
Passwords
Access tokens
Refresh tokens
JWT secrets
Database passwords
Sensitive personal data
```

---

# 29. Dependency Rules

Do not add a dependency just because it is popular.

Before adding a dependency:

1. Check whether the standard library already solves the problem.
2. Check existing dependencies.
3. Check whether the requirement truly needs it.
4. Prefer a maintained, focused dependency.
5. Update dependency documentation/configuration if necessary.

Avoid dependency bloat.

---

# 30. Testing Rules

Every meaningful backend feature must have tests.

At minimum, test:

```text
Happy path
Validation failure
Authentication failure
Authorization failure
Not found
Conflict where applicable
Database failure where practical
```

Financial operations require additional edge-case testing.

---

# 31. Test Before Moving Forward

After each significant feature:

```text
Run tests
↓
Run lint/type checks
↓
Inspect failures
↓
Fix failures
↓
Run tests again
```

Do not continue building on top of known failing tests unless explicitly instructed.

---

# 32. Financial Test Cases

Transaction tests must cover:

```text
Create expense
Create income
Update amount
Update account
Update type
Delete expense
Delete income
Invalid account
Invalid category
Unauthorized transaction
Rollback on failure
```

Example:

```text
Starting balance = ₹10,000

Expense ₹500

Expected balance = ₹9,500
```

Then:

```text
Delete expense

Expected balance = ₹10,000
```

---

# 33. Cross-User Security Tests

Create at least two test users:

```text
User A
User B
```

Verify:

```text
A cannot read B's account.
A cannot read B's transaction.
A cannot update B's transaction.
A cannot delete B's budget.
A cannot access B's notifications.
```

---

# 34. AI Agent Search Strategy

Before creating a new utility or abstraction:

1. Search the repository.
2. Check whether similar functionality already exists.
3. Reuse existing code if appropriate.
4. Avoid duplicate implementations.

Examples:

Before creating:

```text
money.py
security.py
pagination.py
```

search the existing project first.

---

# 35. AI Agent File Modification Rules

Before modifying a file:

- Read the relevant section.
- Understand its imports and dependencies.
- Preserve existing behavior unless change is required.
- Avoid unrelated formatting changes.
- Avoid modifying unrelated files.

Do not create large unrelated diffs.

---

# 36. Do Not Modify Frontend

This is the backend project.

Do not modify the Expo application unless the user explicitly asks for backend/frontend integration work.

The backend must remain independently runnable.

---

# 37. Do Not Modify Product Requirements

An AI coding agent must not rewrite:

```text
BACKEND_PRD.md
DATABASE_SCHEMA.md
API_SPEC.md
```

to make implementation easier.

If implementation conflicts with requirements:

```text
Stop
↓
Explain conflict
↓
Request decision
```

Only update product documentation when explicitly authorized or when the user confirms the change.

---

# 38. OpenAPI Verification

After implementing an endpoint:

Verify:

```text
/docs
/redoc
/openapi.json
```

Check:

- Path
- Method
- Request schema
- Response schema
- Status codes
- Authentication
- Query parameters

The generated OpenAPI contract must match `API_SPEC.md`.

---

# 39. Docker Verification

Before deployment:

```bash
docker build -t expense-tracker-api .
```

Then run the container with environment variables.

Verify:

```text
/health
/docs
Authentication
Database connection
```

The Docker image must not require local development-only files.

---

# 40. Migration Verification

For database changes:

```text
Create migration
↓
Apply migration
↓
Run application
↓
Run tests
↓
Verify schema
```

The complete database must be reproducible from migrations.

---

# 41. Deployment Rules

Production configuration must use environment variables.

Verify:

```text
DATABASE_URL
JWT_SECRET_KEY
CORS_ORIGINS
ENVIRONMENT
```

before deployment.

Do not use development credentials.

Do not expose PostgreSQL directly to the Expo app.

Correct:

```text
Expo
 ↓ HTTPS
FastAPI
 ↓
Supabase PostgreSQL
```

---

# 42. Recurring Transaction Rules

Recurring processing must be idempotent.

If the processing operation executes twice:

```text
One occurrence
```

must not become:

```text
Two transactions
```

Do not create all future recurring transactions upfront.

Only process due occurrences.

---

# 43. Gamification Rules

The client cannot decide authoritative achievement state.

The backend determines:

```text
Streak
Achievement unlock
Budget milestone
Savings milestone
```

The frontend only displays the result.

---

# 44. Dashboard Rules

Dashboard values are backend-authoritative.

Do not let the frontend calculate authoritative:

```text
Total balance
Income
Expenses
Savings
Budget spent
Budget remaining
Budget status
```

The frontend may perform presentation-only calculations such as chart dimensions or formatting.

---

# 45. Performance Rules

Do not optimize prematurely.

However:

- Use database aggregation for report totals.
- Add documented indexes.
- Paginate transactions.
- Avoid N+1 queries.
- Avoid loading unnecessary records.
- Avoid fetching an entire transaction history for dashboard calculations.

Measure before introducing infrastructure such as Redis.

---

# 46. Simplicity Rules

Do not introduce:

```text
Microservices
Kubernetes
Kafka
Redis
GraphQL
CQRS
Event sourcing
Multiple databases
```

unless a concrete requirement appears.

The MVP should remain a modular monolith.

---

# 47. AI Agent Communication

When completing a task, the coding agent should report:

```text
What changed
Files changed
Database changes
API changes
Tests run
Test result
Remaining issues
```

Example:

```text
Implemented transaction creation.

Changed:
- app/services/transaction.py
- app/repositories/transaction.py
- app/api/v1/transactions.py
- tests/api/test_transactions.py

Database:
- No migration required.

Tests:
- pytest tests/api/test_transactions.py
- Passed: 12

Remaining:
- None
```

Keep reports factual.

---

# 48. When to Ask the User

Ask the user before proceeding when:

- Two product documents conflict.
- A breaking API change is required.
- A database migration would destroy existing data.
- A security requirement is ambiguous.
- A financial rule is ambiguous.
- A new product feature is necessary to complete the requested task.
- The requested behavior conflicts with the documented MVP.

Do not ask for confirmation for routine implementation choices that are already determined by the documentation.

---

# 49. When NOT to Ask

Do not interrupt for trivial decisions such as:

```text
Variable names
Private helper names
Internal file organization consistent with architecture
SQL query formatting
Minor implementation details
```

Choose a conventional, maintainable implementation.

---

# 50. Definition of Done for AI Agents

Before saying a task is complete:

```text
[ ] Requirements read
[ ] Relevant existing code inspected
[ ] Implementation completed
[ ] Ownership/security checked
[ ] Validation implemented
[ ] Tests added
[ ] Tests passed
[ ] Lint/type checks passed where configured
[ ] API documentation verified
[ ] Migration created if needed
[ ] No secrets committed
[ ] No unrelated files changed
```

---

# 51. Final AI Agent Rule

The AI coding agent is an implementation assistant, not the product owner.

It may choose:

```text
How
```

to implement a documented requirement.

It must not independently choose:

```text
What
```

the product should do.

The final authority for product behavior is the project documentation and the user's explicit decisions.

When uncertain:

```text
Inspect
↓
Reason from documentation
↓
Implement if unambiguous
↓
Ask only when the decision changes product/security/data behavior
```
