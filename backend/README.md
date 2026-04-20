# Slice Backend - Group Expense Tracker

A FastAPI backend for managing shared expenses within groups.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Main FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py         # Authentication routes (OAuth, JWT)
│   │       ├── users.py        # User management routes
│   │       ├── groups.py       # Group management routes
│   │       └── expenses.py     # Expense tracking routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # OAuth configuration
│   │   └── auth.py             # JWT and auth utilities
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Database connection
│   │   └── models.py           # SQLAlchemy models
│   └── schemas/
│       ├── __init__.py
│       └── user.py             # Pydantic request/response schemas
├── requirements.txt
├── run.py
├── .env.example
└── .gitignore
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize database:**
   ```bash
   python ../init_db.py
   ```

4. **Run the development server:**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8080`
API documentation: `http://localhost:8080/docs`

## API Endpoints

### Authentication (`/api/auth`)
- `POST /login` - Log in with username/email and password
- `POST /register` - Register a password-based user
- `GET /google/login` - Initiate Google OAuth
- `GET /google/callback` - OAuth callback handler
- `GET /me` - Get current user info

### Users (`/api/users`)
- `GET /` - List all users
- `GET /{user_id}` - Get user by ID

### Groups (`/api/groups`)
- `GET /` - List user's groups
- `POST /` - Create new group
- `GET /{group_id}` - Get group details

### Expenses (`/api/expenses`)
- `GET /` - List expenses
- `POST /` - Create new expense
- `GET /{expense_id}` - Get expense details
