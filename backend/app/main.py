from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.api.routes import auth, users, groups, expenses, settlements

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Slice - Group Expense Tracker",
    description="A FastAPI backend for tracking shared expenses within groups",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["expenses"])
app.include_router(settlements.router, prefix="/api/settlements", tags=["settlements"])

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to Slice - Group Expense Tracker",
        "version": "1.0.0",
        "docs": "http://localhost:8080/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
