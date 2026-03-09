from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.handoff import Handoff, HandoffStatus
from app.models.lead import Lead, LeadStatus
from app.schemas.handoff import HandoffUpdate, HandoffResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/handoffs", tags=["handoffs"])


@router.get("", response_model=list[HandoffResponse])
def list_handoffs(
    status_filter: str = Query(None, alias="status"),
    assigned_to: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Handoff)
    if status_filter:
        query = query.filter(Handoff.status == status_filter)
    if assigned_to:
        query = query.filter(Handoff.to_user_id == assigned_to)
    handoffs = query.order_by(Handoff.created_at.desc()).all()
    return [HandoffResponse.model_validate(h) for h in handoffs]


@router.get("/{handoff_id}", response_model=HandoffResponse)
def get_handoff(handoff_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    handoff = db.query(Handoff).filter(Handoff.id == handoff_id).first()
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return HandoffResponse.model_validate(handoff)


@router.put("/{handoff_id}", response_model=HandoffResponse)
def update_handoff(
    handoff_id: str,
    data: HandoffUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    handoff = db.query(Handoff).filter(Handoff.id == handoff_id).first()
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    update_data = data.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == "accepted":
            handoff.accepted_at = now
            # Update lead status
            lead = db.query(Lead).filter(Lead.id == handoff.lead_id).first()
            if lead:
                lead.status = LeadStatus.handed_off
        elif new_status in ("converted", "lost"):
            handoff.completed_at = now
            lead = db.query(Lead).filter(Lead.id == handoff.lead_id).first()
            if lead:
                lead.status = LeadStatus.converted if new_status == "converted" else LeadStatus.lost

    for key, val in update_data.items():
        setattr(handoff, key, val)
    db.commit()
    db.refresh(handoff)
    return HandoffResponse.model_validate(handoff)
