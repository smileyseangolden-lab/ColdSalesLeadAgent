from fastapi import APIRouter
from app.api.v1.endpoints import auth, leads, campaigns, agents, handoffs, email_accounts, users, dashboard, webhooks

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(campaigns.router)
api_router.include_router(agents.router)
api_router.include_router(handoffs.router)
api_router.include_router(email_accounts.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(webhooks.router)
