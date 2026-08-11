# Expense Tracker — Database Schema

Version: 1.0  
Status: MVP  
Database: PostgreSQL  
Provider: Supabase

## 1. Purpose

This document defines the database structure for the Expense Tracker backend.

The database must support:

- Users
- Authentication sessions
- Financial accounts
- Categories
- Transactions
- Monthly budgets
- Recurring transactions
- Notifications
- Gamification
- Achievements

The schema must remain simple for the MVP while allowing future features to be added through migrations.

## 2. Database Technology

Use:

- PostgreSQL
- Supabase PostgreSQL
- SQLAlchemy 2.x
- Alembic

Architecture:

```text
FastAPI
   ↓
SQLAlchemy
   ↓
Supabase PostgreSQL
```

## 3. Core Design Principles

### 3.1 User Ownership

Every user-owned resource must be associated with a user:

- `accounts.user_id`
- `categories.user_id`
- `transactions.user_id`
- `budgets.user_id`
- `recurring_transactions.user_id`
- `notifications.user_id`

### 3.2 Financial Data Integrity

Financial operations must be atomic. Creating an expense must update the transaction and account balance inside one database transaction. If one operation fails, the entire operation must roll back.

### 3.3 MVP Simplicity

The MVP intentionally does NOT include:

- Subcategories
- Hierarchical categories
- Contexts
- Tags
- Locations
- Projects
- Transfers
- Multi-currency

These may be introduced later through database migrations.

## 4. Entity Overview

```text
users
    │
    ├── accounts
    │       │
    │       └── transactions
    │
    ├── categories
    │       │
    │       └── transactions
    │
    ├── budgets
    │       │
    │       └── budget_categories
    │
    ├── recurring_transactions
    │
    ├── notifications
    │
    ├── user_streaks
    │
    └── user_achievements
                │
                ↓
          achievements

users
  │
  └── refresh_tokens
```

## 5. `users`

Stores application users.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `name` | VARCHAR(100) | No | User's name |
| `email` | VARCHAR(255) | No | Unique email |
| `password_hash` | TEXT | No | Argon2id password hash |
| `is_active` | BOOLEAN | No | Account status |
| `created_at` | TIMESTAMPTZ | No | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | No | Last update timestamp |

Constraints:

```text
PRIMARY KEY (id)
UNIQUE (email)
```

Normalize email consistently before storage and uniqueness checks.

## 6. `refresh_tokens`

Stores refresh-token sessions.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `token_hash` | TEXT | No | Hash of refresh token |
| `expires_at` | TIMESTAMPTZ | No | Expiration |
| `revoked_at` | TIMESTAMPTZ | Yes | Revocation timestamp |
| `created_at` | TIMESTAMPTZ | No | Creation timestamp |
| `last_used_at` | TIMESTAMPTZ | Yes | Last refresh timestamp |

Relationship:

```text
refresh_tokens.user_id
        ↓
users.id
```

Do not store reusable raw refresh tokens.

## 7. `accounts`

Represents the user's financial accounts.

Examples:

- HDFC Bank
- SBI Savings
- Cash
- PhonePe
- Paytm
- Credit Card

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `name` | VARCHAR(100) | No | Account name |
| `type` | VARCHAR/ENUM | No | Account type |
| `balance` | NUMERIC(14,2) | No | Current balance |
| `currency` | VARCHAR(3) | No | Currency |
| `is_active` | BOOLEAN | No | Whether account is active |
| `created_at` | TIMESTAMPTZ | No | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | No | Last update |

Account types:

```text
CASH
BANK
UPI_WALLET
CREDIT_CARD
DEBIT_CARD
OTHER
```

MVP currency:

```text
INR
```

## 8. Account Balance

The `balance` field represents the current calculated balance.

Example:

```text
Starting balance = ₹50,000
Expense = ₹500
Current balance = ₹49,500
```

The backend is authoritative for this value.

Balance modifications must occur inside database transactions and be safe against concurrent updates.

## 9. `categories`

MVP categories are flat.

There is NO parent category and NO subcategory.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `name` | VARCHAR(100) | No | Category name |
| `type` | VARCHAR/ENUM | No | Income or expense |
| `icon` | VARCHAR(100) | Yes | Icon identifier |
| `color` | VARCHAR(20) | Yes | UI color |
| `is_active` | BOOLEAN | No | Active state |
| `created_at` | TIMESTAMPTZ | No | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | No | Last update |

Category types:

```text
EXPENSE
INCOME
```

## 10. Default Categories

When a user registers, create default categories.

### Expense

```text
Food
Petrol
Transport
Electricity
Rent
Shopping
Internet
Medical
Entertainment
Groceries
Subscriptions
Other
```

### Income

```text
Salary
Freelance
Business
Investment
Gift
Other
```

Default categories belong to the user.

## 11. `transactions`

This is the central financial entity.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `account_id` | UUID | No | Financial account |
| `category_id` | UUID | No | Transaction category |
| `amount` | NUMERIC(14,2) | No | Transaction amount |
| `type` | VARCHAR/ENUM | No | EXPENSE or INCOME |
| `merchant` | VARCHAR(200) | Yes | Merchant |
| `note` | TEXT | Yes | User note |
| `transaction_date` | TIMESTAMPTZ | No | Actual transaction time |
| `created_at` | TIMESTAMPTZ | No | Record creation |
| `updated_at` | TIMESTAMPTZ | No | Last update |

The MVP transaction model is intentionally:

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

## 12. Transaction Amount

Amount must:

- Be greater than zero.
- Use `NUMERIC`, never floating point.
- Support two decimal places.

## 13. Transaction Category Relationship

Each transaction belongs to one category.

The category must belong to the same user as the transaction.

## 14. Transaction Account Relationship

Each transaction belongs to one account.

The account must belong to the authenticated user.

## 15. Merchant

Merchant is optional.

Examples:

- Indian Oil
- Amazon
- Swiggy
- Uber
- HDFC

Merchant is separate from category.

Example:

```text
Category: Petrol
Merchant: Indian Oil
```

## 16. Note

The transaction contains an optional free-text `note`.

Example:

```text
Category: Petrol
Merchant: Indian Oil
Note: Filled petrol before going to office
```

The note is searchable.

## 17. Transaction Date

Store the transaction timestamp using:

```text
TIMESTAMPTZ
```

Use UTC internally where appropriate. The client can display dates in the user's local timezone.

## 18. Transaction Indexes

Recommended:

```text
transactions(user_id)
transactions(account_id)
transactions(category_id)
transactions(transaction_date)
transactions(type)
transactions(user_id, transaction_date)
transactions(user_id, category_id)
```

## 19. Transaction Search

Search should initially support:

- Merchant
- Note
- Category name

Search must be case-insensitive.

Example:

```text
search = "office"
```

may match:

```text
Merchant: Office Cafe
```

or:

```text
Note: Lunch with office team
```

## 20. `budgets`

Stores monthly budget definitions.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `name` | VARCHAR(100) | No | Budget name |
| `amount` | NUMERIC(14,2) | No | Budget amount |
| `period` | VARCHAR/ENUM | No | Budget period |
| `start_date` | DATE | No | Start |
| `end_date` | DATE | No | End |
| `created_at` | TIMESTAMPTZ | No | Creation |
| `updated_at` | TIMESTAMPTZ | No | Last update |

MVP period:

```text
MONTHLY
```

## 21. `budget_categories`

Connects a budget to one or more categories.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `budget_id` | UUID | No | Budget |
| `category_id` | UUID | No | Category |
| `amount` | NUMERIC(14,2) | No | Category budget |

Example:

```text
Budget
  ├── Food ₹10,000
  ├── Petrol ₹4,000
  └── Shopping ₹5,000
```

A budget may also exist without category allocations as an overall monthly budget.

## 22. Budget Constraints

The backend must ensure:

- Budget belongs to the authenticated user.
- Category belongs to the same user.
- Budget category belongs to the same budget.
- Amount > 0.
- Date range is valid.

## 23. `recurring_transactions`

Stores recurring transaction definitions.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `account_id` | UUID | No | Account |
| `category_id` | UUID | No | Category |
| `type` | VARCHAR/ENUM | No | Income/Expense |
| `amount` | NUMERIC(14,2) | No | Amount |
| `merchant` | VARCHAR(200) | Yes | Merchant |
| `note` | TEXT | Yes | Note |
| `frequency` | VARCHAR/ENUM | No | DAILY/MONTHLY |
| `start_date` | DATE | No | Start |
| `end_date` | DATE | Yes | Optional end |
| `next_occurrence` | DATE | No | Next processing date |
| `is_active` | BOOLEAN | No | Active state |
| `created_at` | TIMESTAMPTZ | No | Creation |
| `updated_at` | TIMESTAMPTZ | No | Last update |

MVP frequencies:

```text
DAILY
MONTHLY
```

Future:

```text
WEEKLY
YEARLY
CUSTOM
```

Do not create all future transactions upfront.

The recurrence processor must be idempotent so repeated execution cannot create duplicates.

## 24. `notifications`

Stores in-app notifications.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | Owner |
| `type` | VARCHAR(50) | No | Notification type |
| `title` | VARCHAR(200) | No | Title |
| `message` | TEXT | No | Message |
| `data` | JSONB | Yes | Additional structured data |
| `is_read` | BOOLEAN | No | Read state |
| `created_at` | TIMESTAMPTZ | No | Creation time |

Initial types:

```text
BUDGET_WARNING
BUDGET_EXCEEDED
TRACKING_REMINDER
MONTHLY_SUMMARY
RECURRING_TRANSACTION
ACHIEVEMENT_UNLOCKED
```

## 25. `user_streaks`

Stores financial tracking streak information.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | User |
| `current_streak` | INTEGER | No | Current streak |
| `longest_streak` | INTEGER | No | Longest streak |
| `last_activity_date` | DATE | Yes | Last activity |
| `created_at` | TIMESTAMPTZ | No | Creation |
| `updated_at` | TIMESTAMPTZ | No | Last update |

There should be one streak record per user.

## 26. `achievements`

Stores available achievements.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `code` | VARCHAR(100) | No | Unique achievement code |
| `name` | VARCHAR(150) | No | Display name |
| `description` | TEXT | No | Description |
| `icon` | VARCHAR(100) | Yes | Icon identifier |

Examples:

```text
FIRST_TRANSACTION
SEVEN_DAY_STREAK
BUDGET_ACHIEVED
FIFTY_TRANSACTIONS
MONTHLY_GOAL
SAVINGS_MILESTONE
```

## 27. `user_achievements`

Maps users to unlocked achievements.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | User |
| `achievement_id` | UUID | No | Achievement |
| `unlocked_at` | TIMESTAMPTZ | No | Unlock time |

Constraint:

```text
UNIQUE(user_id, achievement_id)
```

## 28. Foreign Key Relationships

```text
users.id
   ↓
accounts.user_id

users.id
   ↓
categories.user_id

users.id
   ↓
transactions.user_id

accounts.id
   ↓
transactions.account_id

categories.id
   ↓
transactions.category_id

users.id
   ↓
budgets.user_id

budgets.id
   ↓
budget_categories.budget_id

categories.id
   ↓
budget_categories.category_id

users.id
   ↓
recurring_transactions.user_id

accounts.id
   ↓
recurring_transactions.account_id

categories.id
   ↓
recurring_transactions.category_id

users.id
   ↓
notifications.user_id

users.id
   ↓
user_streaks.user_id

users.id
   ↓
user_achievements.user_id

achievements.id
   ↓
user_achievements.achievement_id

users.id
   ↓
refresh_tokens.user_id
```

## 29. UUID Strategy

Use UUIDs for primary keys.

Generate IDs server-side or database-side using a PostgreSQL-supported UUID strategy.

## 30. Timestamps

Use:

```text
TIMESTAMPTZ
```

for timestamps.

Standard fields:

```text
created_at
updated_at
```

Use UTC internally.

## 31. Soft Delete vs Hard Delete

Use explicit `is_active` fields where deactivation is useful:

```text
users.is_active
accounts.is_active
categories.is_active
recurring_transactions.is_active
```

For financial records, avoid destructive deletion when historical integrity would be compromised.

## 32. Delete Behavior

### User deletion

User deletion must ensure no user-owned information remains accessible.

### Account deletion

An account with historical transactions should generally be deactivated rather than physically deleted.

```text
is_active = false
```

Historical transactions remain associated with the account.

### Category deletion

If a category has existing transactions, prefer deactivation rather than destructive deletion.

Historical transactions must remain valid.

## 33. Financial Integrity Rules

The backend must guarantee:

1. Transaction amount is positive.
2. Transaction belongs to the authenticated user.
3. Account belongs to the same user.
4. Category belongs to the same user.
5. Income and expense values are never negative.
6. Account balance updates are atomic.
7. Financial operations use database transactions.
8. Concurrent balance updates are handled safely.

## 34. Data Validation

Database constraints should complement Pydantic validation.

Examples:

```text
amount > 0
email unique
user_id NOT NULL
account_id NOT NULL
category_id NOT NULL
transaction type valid
account type valid
budget amount > 0
```

Do not rely solely on frontend validation.

## 35. Indexing Strategy

At minimum:

### users

```text
UNIQUE(email)
```

### accounts

```text
INDEX(user_id)
```

### categories

```text
INDEX(user_id)
INDEX(user_id, type)
```

### transactions

```text
INDEX(user_id)
INDEX(account_id)
INDEX(category_id)
INDEX(transaction_date)
INDEX(type)
INDEX(user_id, transaction_date)
INDEX(user_id, category_id)
```

### budgets

```text
INDEX(user_id)
INDEX(user_id, start_date, end_date)
```

### recurring_transactions

```text
INDEX(user_id)
INDEX(next_occurrence)
INDEX(is_active)
```

### notifications

```text
INDEX(user_id, created_at)
INDEX(user_id, is_read)
```

## 36. Database Migration Strategy

Use Alembic.

Initial migration:

```text
001_initial_schema
```

Future changes:

```text
002_add_feature
003_modify_feature
004_add_index
```

Never modify an already-applied production migration. Create a new migration for schema changes.

## 37. Database Environment

Development:

```text
FastAPI
   ↓
Supabase PostgreSQL
```

Production:

```text
FastAPI Docker Container
   ↓
Supabase PostgreSQL
```

Local PostgreSQL is optional and is not required for the initial development setup.

## 38. Database Security

Never expose the database directly to the mobile application.

Correct:

```text
Expo
 ↓ HTTPS
FastAPI
 ↓
Supabase PostgreSQL
```

Incorrect:

```text
Expo
 ↓
PostgreSQL
```

The backend is responsible for authorization and business rules.

## 39. Supabase Usage

Supabase provides:

- PostgreSQL
- Database hosting
- Future Storage capability

For MVP, FastAPI owns:

- Authentication
- Authorization
- Business logic
- Database access

Supabase PostgreSQL is the persistence layer.

Do not make the mobile application directly manipulate financial database tables.

## 40. Final MVP Tables

```text
users
refresh_tokens

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
```

## 41. Future Authentication Extensions

Future social login may introduce:

```text
auth_accounts
```

Potential fields:

```text
id
user_id
provider
provider_user_id
created_at
```

Providers:

```text
GOOGLE
APPLE
```

This table is NOT required for MVP.

## 42. Future Profile Extensions

Future user fields may include:

```text
profile_photo_url
timezone
currency
```

Do not add profile photo to MVP.

## 43. Future Transaction Extensions

Potential future fields/features:

```text
receipt_url
location
tags
context_id
subcategory_id
```

These are intentionally excluded from MVP.

## 44. Future Category Extensions

MVP:

```text
Category
```

Future:

```text
Category
  └── Subcategory
```

or a full category hierarchy.

Do not add `parent_id` to the MVP categories table.

## 45. Future Contexts

A future `contexts` table may support:

```text
Home
Hostel
Office
Travel
Personal
Family
Work
```

This is NOT part of the MVP.

The current application should use:

```text
Category
+
Merchant
+
Note
```

for flexible classification.

## 46. Future Tags

A future tagging system may use:

```text
tags
transaction_tags
```

Example:

```text
#essential
#monthly
#work
#travel
```

Not part of MVP.

## 47. Database Schema Acceptance Criteria

The database schema is considered ready when:

- All MVP entities are defined.
- All foreign keys are defined.
- User ownership is explicit.
- Financial amounts use NUMERIC.
- UUIDs are used for primary keys.
- Timestamps use TIMESTAMPTZ.
- Required constraints exist.
- Required indexes exist.
- Account balance integrity is defined.
- Category ownership is enforced.
- Account ownership is enforced.
- Transaction ownership is enforced.
- Budget ownership is enforced.
- Refresh tokens are revocable.
- Historical financial records are protected from destructive deletion.
- Alembic can create the complete schema from an empty database.
- The schema can support the current Expo application's backend requirements.

## 48. Important Implementation Rule

Do NOT add database tables or fields merely because they might be useful someday.

For MVP, implement exactly the required schema.

Future features must be introduced using explicit migrations.

The current transaction classification model is:

```text
Transaction
├── Category
├── Account
├── Merchant
├── Note
├── Amount
├── Type
└── Date
```

No subcategory.  
No context.  
No tags.  
No hierarchy.

This simplicity is intentional.
