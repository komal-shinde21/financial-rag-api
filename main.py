"""
Financial Document Management API
==================================
FastAPI + SQLAlchemy (SQLite/PostgreSQL) + Qdrant + LangChain RAG
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import get_settings
from database import engine, SessionLocal, Base
from models import User, Role, Document          # noqa: F401 – needed for table creation
from routers import auth, documents, roles, rag
from utils.security import hash_password

settings = get_settings()


# ── Startup: create tables + seed default roles & admin user ─────────────────

def seed_default_roles(db: Session) -> None:
    """Create the four standard roles if they don't already exist."""
    default_roles = [
        {
            "name": "admin",
            "description": "Full system access",
            "permissions": "all",
        },
        {
            "name": "analyst",
            "description": "Upload and edit financial documents",
            "permissions": "upload,edit,view",
        },
        {
            "name": "auditor",
            "description": "Review and read documents",
            "permissions": "view",
        },
        {
            "name": "client",
            "description": "View company documents",
            "permissions": "view",
        },
    ]
    for r in default_roles:
        if not db.query(Role).filter(Role.name == r["name"]).first():
            db.add(Role(**r))
    db.commit()


def seed_admin_user(db: Session) -> None:
    """Create a default admin user if none exists."""
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing and admin_role:
        admin = User(
            username="admin",
            email="admin@financialrag.com",
            hashed_password=hash_password("Admin@1234"),
        )
        admin.roles.append(admin_role)
        db.add(admin)
        db.commit()
        print("✅  Default admin user created  (username=admin  password=Admin@1234)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    db: Session = SessionLocal()
    try:
        seed_default_roles(db)
        seed_admin_user(db)
    finally:
        db.close()

    print(f"🚀  {settings.APP_NAME} is running")
    yield
    print("👋  Shutting down")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Financial Document Management API",
    description=(
        "Store, manage, and semantically search financial documents "
        "(invoices, reports, contracts) using AI-powered RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(roles.router)
app.include_router(rag.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
