"""Inbound webhook endpoints for email parsing (SendGrid, Mailgun, AWS SES)."""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lead import Lead
from app.models.interaction import Interaction, InteractionType, InteractionChannel, InteractionDirection

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/inbound-email/sendgrid")
async def sendgrid_inbound(request: Request, db: Session = Depends(get_db)):
    """Handle inbound emails from SendGrid Inbound Parse."""
    form = await request.form()
    from_email = form.get("from", "")
    subject = form.get("subject", "")
    body = form.get("text", "") or form.get("html", "")

    # Extract email from "Name <email>" format
    email = from_email
    if "<" in from_email:
        email = from_email.split("<")[1].rstrip(">")
    email = email.strip().lower()

    lead = db.query(Lead).filter(Lead.email == email).first()
    if not lead:
        return {"status": "ignored", "reason": "unknown sender"}

    interaction = Interaction(
        lead_id=lead.id,
        type=InteractionType.email_received,
        channel=InteractionChannel.email,
        direction=InteractionDirection.inbound,
        subject=subject,
        body=body,
        metadata_json={"source": "sendgrid", "from": from_email},
    )
    db.add(interaction)
    db.commit()

    # Trigger reply handler agent
    from app.tasks.agent_tasks import process_inbound_reply
    process_inbound_reply.delay(interaction.id)

    return {"status": "received", "interaction_id": interaction.id}


@router.post("/inbound-email/mailgun")
async def mailgun_inbound(request: Request, db: Session = Depends(get_db)):
    """Handle inbound emails from Mailgun."""
    form = await request.form()
    sender = form.get("sender", "").strip().lower()
    subject = form.get("subject", "")
    body = form.get("stripped-text", "") or form.get("body-plain", "")

    lead = db.query(Lead).filter(Lead.email == sender).first()
    if not lead:
        return {"status": "ignored"}

    interaction = Interaction(
        lead_id=lead.id,
        type=InteractionType.email_received,
        channel=InteractionChannel.email,
        direction=InteractionDirection.inbound,
        subject=subject,
        body=body,
        metadata_json={"source": "mailgun", "sender": sender},
    )
    db.add(interaction)
    db.commit()

    from app.tasks.agent_tasks import process_inbound_reply
    process_inbound_reply.delay(interaction.id)

    return {"status": "received", "interaction_id": interaction.id}


@router.post("/email-tracking/open/{tracking_id}")
def track_open(tracking_id: str, db: Session = Depends(get_db)):
    """Track email opens via tracking pixel."""
    original = db.query(Interaction).filter(
        Interaction.id == tracking_id,
        Interaction.type == InteractionType.email_sent,
    ).first()
    if not original:
        return {"status": "ignored"}

    # Don't double-count
    existing = db.query(Interaction).filter(
        Interaction.lead_id == original.lead_id,
        Interaction.type == InteractionType.email_opened,
        Interaction.metadata_json.contains({"original_id": tracking_id}),
    ).first()
    if existing:
        return {"status": "already_tracked"}

    open_event = Interaction(
        lead_id=original.lead_id,
        campaign_id=original.campaign_id,
        campaign_step_id=original.campaign_step_id,
        type=InteractionType.email_opened,
        channel=InteractionChannel.email,
        direction=InteractionDirection.inbound,
        body="Email opened",
        metadata_json={"original_id": tracking_id},
    )
    db.add(open_event)
    db.commit()
    return {"status": "tracked"}


@router.get("/email-tracking/click/{tracking_id}")
def track_click(tracking_id: str, url: str = "", db: Session = Depends(get_db)):
    """Track email link clicks via redirect."""
    original = db.query(Interaction).filter(
        Interaction.id == tracking_id,
        Interaction.type == InteractionType.email_sent,
    ).first()
    if original:
        click_event = Interaction(
            lead_id=original.lead_id,
            campaign_id=original.campaign_id,
            campaign_step_id=original.campaign_step_id,
            type=InteractionType.email_clicked,
            channel=InteractionChannel.email,
            direction=InteractionDirection.inbound,
            body=f"Clicked: {url}",
            metadata_json={"original_id": tracking_id, "url": url},
        )
        db.add(click_event)
        db.commit()

    from fastapi.responses import RedirectResponse
    if url:
        return RedirectResponse(url=url)
    return {"status": "tracked"}
