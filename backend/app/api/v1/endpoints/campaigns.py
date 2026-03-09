import math
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.campaign import Campaign, CampaignStep
from app.models.enrollment import LeadCampaignEnrollment, EnrollmentStatus
from app.models.lead import Lead
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignStepCreate, CampaignStepUpdate, CampaignStepResponse,
)
from app.schemas.enrollment import EnrollmentCreate, EnrollmentResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = Campaign(
        name=data.name,
        description=data.description,
        type=data.type,
        target_criteria=data.target_criteria,
        created_by=user.id,
        settings=data.settings or Campaign.settings.default.arg,
    )
    db.add(campaign)
    db.flush()

    for step_data in data.steps:
        step = CampaignStep(
            campaign_id=campaign.id,
            step_number=step_data.step_number,
            channel=step_data.channel,
            delay_days=step_data.delay_days,
            delay_hours=step_data.delay_hours,
            subject_template=step_data.subject_template,
            body_template=step_data.body_template,
            ai_personalization_enabled=step_data.ai_personalization_enabled,
            ai_personalization_instructions=step_data.ai_personalization_instructions,
            condition=step_data.condition,
            variant_group=step_data.variant_group,
            variant_label=step_data.variant_label,
        )
        db.add(step)

    db.commit()
    db.refresh(campaign)
    campaign = db.query(Campaign).options(joinedload(Campaign.steps)).filter(Campaign.id == campaign.id).first()
    return CampaignResponse.model_validate(campaign)


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(
    status_filter: str = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Campaign).options(joinedload(Campaign.steps))
    if status_filter:
        query = query.filter(Campaign.status == status_filter)
    campaigns = query.order_by(Campaign.created_at.desc()).all()
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = (
        db.query(Campaign)
        .options(joinedload(Campaign.steps))
        .filter(Campaign.id == campaign_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse.model_validate(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(campaign, key, val)
    db.commit()
    campaign = db.query(Campaign).options(joinedload(Campaign.steps)).filter(Campaign.id == campaign_id).first()
    return CampaignResponse.model_validate(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(campaign)
    db.commit()


# Campaign Steps
@router.post("/{campaign_id}/steps", response_model=CampaignStepResponse, status_code=status.HTTP_201_CREATED)
def add_step(
    campaign_id: str,
    data: CampaignStepCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    step = CampaignStep(campaign_id=campaign_id, **data.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return CampaignStepResponse.model_validate(step)


@router.put("/{campaign_id}/steps/{step_id}", response_model=CampaignStepResponse)
def update_step(
    campaign_id: str,
    step_id: str,
    data: CampaignStepUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    step = db.query(CampaignStep).filter(
        CampaignStep.id == step_id, CampaignStep.campaign_id == campaign_id
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(step, key, val)
    db.commit()
    db.refresh(step)
    return CampaignStepResponse.model_validate(step)


@router.delete("/{campaign_id}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(
    campaign_id: str, step_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    step = db.query(CampaignStep).filter(
        CampaignStep.id == step_id, CampaignStep.campaign_id == campaign_id
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(step)
    db.commit()


# Enrollment
@router.post("/{campaign_id}/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_lead(
    campaign_id: str,
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = db.query(Campaign).options(joinedload(Campaign.steps)).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "active":
        raise HTTPException(status_code=400, detail="Campaign is not active")

    lead = db.query(Lead).filter(Lead.id == data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    existing = db.query(LeadCampaignEnrollment).filter(
        LeadCampaignEnrollment.lead_id == data.lead_id,
        LeadCampaignEnrollment.campaign_id == campaign_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lead already enrolled")

    first_step = min(campaign.steps, key=lambda s: s.step_number) if campaign.steps else None
    delay = timedelta(days=first_step.delay_days, hours=first_step.delay_hours) if first_step else timedelta(hours=1)

    enrollment = LeadCampaignEnrollment(
        lead_id=data.lead_id,
        campaign_id=campaign_id,
        current_step=0,
        status=EnrollmentStatus.active,
        next_step_at=datetime.now(timezone.utc) + delay,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return EnrollmentResponse.model_validate(enrollment)


@router.post("/{campaign_id}/enroll-bulk")
def bulk_enroll(
    campaign_id: str,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lead_ids = body.get("lead_ids", [])
    campaign = db.query(Campaign).options(joinedload(Campaign.steps)).filter(Campaign.id == campaign_id).first()
    if not campaign or campaign.status != "active":
        raise HTTPException(status_code=400, detail="Campaign not active")

    first_step = min(campaign.steps, key=lambda s: s.step_number) if campaign.steps else None
    delay = timedelta(days=first_step.delay_days, hours=first_step.delay_hours) if first_step else timedelta(hours=1)

    enrolled = 0
    skipped = 0
    for lead_id in lead_ids:
        existing = db.query(LeadCampaignEnrollment).filter(
            LeadCampaignEnrollment.lead_id == lead_id,
            LeadCampaignEnrollment.campaign_id == campaign_id,
        ).first()
        if existing:
            skipped += 1
            continue
        enrollment = LeadCampaignEnrollment(
            lead_id=lead_id,
            campaign_id=campaign_id,
            current_step=0,
            status=EnrollmentStatus.active,
            next_step_at=datetime.now(timezone.utc) + delay,
        )
        db.add(enrollment)
        enrolled += 1

    db.commit()
    return {"enrolled": enrolled, "skipped": skipped}


@router.get("/{campaign_id}/enrollments", response_model=list[EnrollmentResponse])
def list_enrollments(
    campaign_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    enrollments = (
        db.query(LeadCampaignEnrollment)
        .filter(LeadCampaignEnrollment.campaign_id == campaign_id)
        .all()
    )
    return [EnrollmentResponse.model_validate(e) for e in enrollments]


@router.get("/{campaign_id}/stats")
def campaign_stats(campaign_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    from app.models.interaction import Interaction, InteractionType
    from sqlalchemy import func

    total_enrolled = db.query(LeadCampaignEnrollment).filter(
        LeadCampaignEnrollment.campaign_id == campaign_id
    ).count()

    emails_sent = db.query(Interaction).filter(
        Interaction.campaign_id == campaign_id,
        Interaction.type == InteractionType.email_sent,
    ).count()

    opens = db.query(Interaction).filter(
        Interaction.campaign_id == campaign_id,
        Interaction.type == InteractionType.email_opened,
    ).count()

    clicks = db.query(Interaction).filter(
        Interaction.campaign_id == campaign_id,
        Interaction.type == InteractionType.email_clicked,
    ).count()

    replies = db.query(Interaction).filter(
        Interaction.campaign_id == campaign_id,
        Interaction.type == InteractionType.email_received,
    ).count()

    return {
        "total_enrolled": total_enrolled,
        "emails_sent": emails_sent,
        "opens": opens,
        "clicks": clicks,
        "replies": replies,
        "open_rate": (opens / emails_sent * 100) if emails_sent > 0 else 0,
        "click_rate": (clicks / emails_sent * 100) if emails_sent > 0 else 0,
        "reply_rate": (replies / emails_sent * 100) if emails_sent > 0 else 0,
    }
