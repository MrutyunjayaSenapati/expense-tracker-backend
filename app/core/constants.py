from typing import List, Dict

# Default categories created for newly registered users
DEFAULT_EXPENSE_CATEGORIES: List[Dict[str, str]] = [
    {"name": "Food & Dining", "type": "EXPENSE", "icon": "restaurant", "color": "#FF6B6B"},
    {"name": "Petrol & Fuel", "type": "EXPENSE", "icon": "fuel", "color": "#7C5CFC"},
    {"name": "Transport", "type": "EXPENSE", "icon": "car", "color": "#4D7FE8"},
    {"name": "Electricity", "type": "EXPENSE", "icon": "flash", "color": "#F59E0B"},
    {"name": "Rent & Housing", "type": "EXPENSE", "icon": "home", "color": "#10B981"},
    {"name": "Shopping", "type": "EXPENSE", "icon": "bag-handle", "color": "#EC4899"},
    {"name": "Internet & Bills", "type": "EXPENSE", "icon": "wifi", "color": "#6366F1"},
    {"name": "Medical & Health", "type": "EXPENSE", "icon": "medkit", "color": "#EF4444"},
    {"name": "Entertainment", "type": "EXPENSE", "icon": "film", "color": "#8B5CF6"},
    {"name": "Groceries", "type": "EXPENSE", "icon": "cart", "color": "#14B8A6"},
    {"name": "Subscriptions", "type": "EXPENSE", "icon": "repeat", "color": "#3B82F6"},
    {"name": "Other Expense", "type": "EXPENSE", "icon": "ellipsis-horizontal-circle", "color": "#6B7280"},
]

DEFAULT_INCOME_CATEGORIES: List[Dict[str, str]] = [
    {"name": "Salary", "type": "INCOME", "icon": "cash", "color": "#10B981"},
    {"name": "Freelance", "type": "INCOME", "icon": "laptop", "color": "#3B82F6"},
    {"name": "Business", "type": "INCOME", "icon": "briefcase", "color": "#8B5CF6"},
    {"name": "Investment", "type": "INCOME", "icon": "trending-up", "color": "#F59E0B"},
    {"name": "Gift", "type": "INCOME", "icon": "gift", "color": "#EC4899"},
    {"name": "Other Income", "type": "INCOME", "icon": "wallet", "color": "#6B7280"},
]

# System achievements seeded automatically
SYSTEM_ACHIEVEMENTS: List[Dict[str, str]] = [
    {
        "code": "FIRST_TRANSACTION",
        "name": "First Step",
        "description": "Recorded your very first transaction.",
        "icon": "trophy",
    },
    {
        "code": "SEVEN_DAY_STREAK",
        "name": "7 Day Streak",
        "description": "Tracked expenses for 7 consecutive days.",
        "icon": "flame",
    },
    {
        "code": "BUDGET_ACHIEVED",
        "name": "Budget Master",
        "description": "Created and maintained a monthly spending budget.",
        "icon": "pie-chart",
    },
    {
        "code": "FIFTY_TRANSACTIONS",
        "name": "Super Tracker",
        "description": "Recorded 50 transactions.",
        "icon": "ribbon",
    },
    {
        "code": "MONTHLY_GOAL",
        "name": "Monthly Finisher",
        "description": "Stayed within budget for an entire month.",
        "icon": "shield-checkmark",
    },
    {
        "code": "SAVINGS_MILESTONE",
        "name": "Savvy Saver",
        "description": "Saved more than 30% of your income in a period.",
        "icon": "star",
    },
]
