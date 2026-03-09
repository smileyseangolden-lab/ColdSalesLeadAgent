from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.lead import Lead
from app.models.interaction import Interaction, InteractionType
from app.models.handoff import Handoff
from app.models.agent import AIAgent
from app.models.campaign import Campaign
from app.models.enrollment import LeadCampaignEnrollment
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    # Pipeline
    pipeline = {}
    for status_val, count in db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all():
        pipeline[status_val] = count

    # Today's activity
    emails_today = db.query(Interaction).filter(
        Interaction.type == InteractionType.email_sent,
        Interaction.created_at >= today_start,
    ).count()

    emails_week = db.query(Interaction).filter(
        Interaction.type == InteractionType.email_sent,
        Interaction.created_at >= week_start,
    ).count()

    replies_today = db.query(Interaction).filter(
        Interaction.type == InteractionType.email_received,
        Interaction.created_at >= today_start,
    ).count()

    total_leads = db.query(Lead).count()
    avg_score = db.query(func.avg(Lead.lead_score)).scalar() or 0

    handoffs_week = db.query(Handoff).filter(Handoff.created_at >= week_start).count()

    # Agent statuses
    agents = db.query(AIAgent).all()
    agent_statuses = [
        {
            "id": a.id,
            "name": a.name,
            "type": a.type,
            "status": a.status,
            "last_active_at": a.last_active_at.isoformat() if a.last_active_at else None,
            "stats": a.stats,
        }
        for a in agents
    ]

    # Recent activity
    recent = (
        db.query(Interaction)
        .filter(Interaction.created_at >= today_start)
        .order_by(Interaction.created_at.desc())
        .limit(50)
        .all()
    )
    activity_feed = [
        {
            "id": i.id,
            "type": i.type,
            "channel": i.channel,
            "direction": i.direction,
            "lead_id": i.lead_id,
            "body": i.body[:200] if i.body else "",
            "created_at": i.created_at.isoformat(),
        }
        for i in recent
    ]

    return {
        "pipeline": pipeline,
        "metrics": {
            "total_active_leads": total_leads,
            "emails_sent_today": emails_today,
            "emails_sent_week": emails_week,
            "replies_today": replies_today,
            "average_lead_score": round(float(avg_score), 1),
            "handoffs_this_week": handoffs_week,
        },
        "agents": agent_statuses,
        "activity_feed": activity_feed,
    }


@router.get("/campaign-performance")
def campaign_performance(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaigns = db.query(Campaign).filter(Campaign.status == "active").all()
    results = []
    for c in campaigns:
        enrolled = db.query(LeadCampaignEnrollment).filter(
            LeadCampaignEnrollment.campaign_id == c.id
        ).count()
        sent = db.query(Interaction).filter(
            Interaction.campaign_id == c.id,
            Interaction.type == InteractionType.email_sent,
        ).count()
        opens = db.query(Interaction).filter(
            Interaction.campaign_id == c.id,
            Interaction.type == InteractionType.email_opened,
        ).count()
        replies = db.query(Interaction).filter(
            Interaction.campaign_id == c.id,
            Interaction.type == InteractionType.email_received,
        ).count()
        results.append({
            "id": c.id,
            "name": c.name,
            "enrolled": enrolled,
            "sent": sent,
            "opens": opens,
            "replies": replies,
            "open_rate": round((opens / sent * 100), 1) if sent > 0 else 0,
            "reply_rate": round((replies / sent * 100), 1) if sent > 0 else 0,
        })
    return results
