"""
FastAPI Admin Panel - Web interface for bot management
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
from datetime import datetime
from loguru import logger

from database.mongodb import db
from config.settings import config

app = FastAPI(title="NexusAI Bot Admin Panel", version="2.0.0")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

security_http = HTTPBasic()

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_PANEL_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PANEL_PASSWORD", "nexusai2024")


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security_http)):
    """Verify admin panel credentials"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.on_event("startup")
async def startup():
    await db.connect()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(verify_credentials)):
    """Main dashboard"""
    stats = await db.get_bot_statistics()
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "username": username,
    })


@app.get("/api/stats")
async def get_stats(username: str = Depends(verify_credentials)):
    """Get bot statistics API"""
    stats = await db.get_bot_statistics()
    return stats


@app.get("/api/users")
async def get_users(
    skip: int = 0, 
    limit: int = 50,
    username: str = Depends(verify_credentials)
):
    """Get users list API"""
    users = await db.get_all_users(skip=skip, limit=limit)
    # Convert ObjectId to string
    for user in users:
        if "_id" in user:
            user["_id"] = str(user["_id"])
        if user.get("subscription", {}).get("expires_at"):
            user["subscription"]["expires_at"] = str(user["subscription"]["expires_at"])
        if user.get("created_at"):
            user["created_at"] = str(user["created_at"])
        if user.get("last_seen"):
            user["last_seen"] = str(user["last_seen"])
    return {"users": users, "total": len(users)}


@app.post("/api/users/{user_id}/ban")
async def ban_user_api(user_id: int, reason: str = Form("Banned by admin"), 
                        username: str = Depends(verify_credentials)):
    """Ban a user via API"""
    admin_user = await db.users.find_one({"user_id": int(username)}) if username.isdigit() else None
    admin_id = int(username) if username.isdigit() else 0
    await db.ban_user(user_id, reason, admin_id)
    return {"success": True, "message": f"User {user_id} banned"}


@app.post("/api/users/{user_id}/unban")
async def unban_user_api(user_id: int, username: str = Depends(verify_credentials)):
    """Unban a user via API"""
    admin_id = int(username) if username.isdigit() else 0
    await db.unban_user(user_id, admin_id)
    return {"success": True, "message": f"User {user_id} unbanned"}


@app.post("/api/users/{user_id}/premium")
async def grant_premium_api(user_id: int, days: int = Form(30),
                              username: str = Depends(verify_credentials)):
    """Grant premium to user"""
    await db.upgrade_subscription(user_id, "premium", days)
    return {"success": True, "message": f"Premium granted to {user_id} for {days} days"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "NexusAI", "version": config.BOT_VERSION}
