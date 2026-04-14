# Slice - Group Expense Tracker

A modern, minimalistic expense tracking application built with FastAPI and React.

## Features

- 🔐 Google OAuth Authentication
- 👥 Group expense management
- 💰 Split expenses with friends
- 📊 Balance tracking
- 🎨 Minimalistic UI

## Setup Instructions

### 1. Backend Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**

   Update your `.env` file with the following:

   ```env
   # Database
   DATABASE_URL=postgresql://postgres:YOUR_SUPABASE_PASSWORD@db.fffxxjfstaurikajseci.supabase.co:5432/postgres

   # Google OAuth (Get these from Google Cloud Console)
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

   # JWT Secret (generate a random string)
   SECRET_KEY=your_random_secret_key_here
   ```

3. **Create Database Tables**
   ```bash
   python init_db.py
   ```

### 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:8000/auth/google/callback`
7. Copy the Client ID and Client Secret to your `.env` file

### 3. Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

### 4. Backend Server

1. **Start the Backend**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

## Usage

1. Open `http://localhost:5173` in your browser
2. Click "Continue with Google" to authenticate
3. Start managing your group expenses!

## API Endpoints

- `GET /` - Welcome message
- `GET /auth/google/login` - Initiate Google OAuth
- `GET /auth/google/callback` - OAuth callback
- `GET /auth/me` - Get current user info
- `GET /users/` - List users
- `POST /users/` - Create user

## Database Schema

- **Users**: User accounts with OAuth integration
- **Groups**: Expense groups
- **UserGroupMapping**: Group memberships
- **Expenses**: Individual expenses
- **ExpenseSplits**: How expenses are split
- **Settlements**: Payment settlements
- **UserGroupBalance**: Balance tracking

## Technologies Used

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, TypeScript, Axios
- **Authentication**: Google OAuth 2.0, JWT
- **Database**: Supabase PostgreSQL
- **Styling**: CSS with modern design

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
