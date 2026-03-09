import csv
import io
import math
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
from app.core.database import get_db
from app.models.lead import Lead
from app.models.interaction import Interaction, InteractionType, InteractionChannel, InteractionDirection
from app.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse, LeadBulkCreate,
    LeadListResponse, LeadFilter,
)
from app.schemas.interaction import InteractionResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/leads", tags=["leads"])


def _build_lead(data: LeadCreate) -> Lead:
    return Lead(
        first_name=data.first_name,
        last_name=data.last_name,
        full_name=f"{data.first_name} {data.last_name}",
        email=data.email.lower(),
        phone=data.phone,
        linkedin_url=data.linkedin_url,
        company_name=data.company_name,
        job_title=data.job_title,
        industry=data.industry,
        company_size=data.company_size,
        location_city=data.location_city,
        location_state=data.location_state,
        location_country=data.location_country,
        source=data.source,
        tags=data.tags,
        custom_fields=data.custom_fields,
        notes=data.notes,
        assigned_to=data.assigned_to,
    )


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(data: LeadCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Lead).filter(Lead.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Lead with this email already exists")
    lead = _build_lead(data)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_leads(
    data: LeadBulkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    created = []
    duplicates = []
    errors = []
    for i, lead_data in enumerate(data.leads):
        try:
            if db.query(Lead).filter(Lead.email == lead_data.email.lower()).first():
                duplicates.append({"index": i, "email": lead_data.email})
                continue
            lead_data.source = data.source
            if data.tags:
                lead_data.tags = list(set(lead_data.tags + data.tags))
            lead = _build_lead(lead_data)
            db.add(lead)
            db.flush()
            created.append(lead.id)
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    db.commit()
    return {
        "created": len(created),
        "duplicates": len(duplicates),
        "errors": len(errors),
        "duplicate_details": duplicates,
        "error_details": errors,
    }


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    # Auto-detect column mapping
    field_map = {}
    common_mappings = {
        "first_name": ["first_name", "first name", "firstname", "first"],
        "last_name": ["last_name", "last name", "lastname", "last"],
        "email": ["email", "email address", "e-mail", "emailaddress"],
        "phone": ["phone", "phone number", "telephone", "mobile"],
        "company_name": ["company", "company_name", "company name", "organization"],
        "job_title": ["title", "job_title", "job title", "position", "role"],
        "industry": ["industry", "sector"],
        "linkedin_url": ["linkedin", "linkedin_url", "linkedin url", "linkedin profile"],
        "location_city": ["city", "location_city"],
        "location_state": ["state", "location_state", "province"],
        "location_country": ["country", "location_country"],
    }

    if reader.fieldnames:
        for field, aliases in common_mappings.items():
            for col in reader.fieldnames:
                if col.lower().strip() in aliases:
                    field_map[field] = col
                    break

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    created = 0
    duplicates = 0
    errors_list = []
    preview_rows = []
    row_count = 0

    for row in reader:
        row_count += 1
        try:
            email = row.get(field_map.get("email", "email"), "").strip().lower()
            if not email:
                errors_list.append({"row": row_count, "error": "Missing email"})
                continue

            first_name = row.get(field_map.get("first_name", "first_name"), "").strip()
            last_name = row.get(field_map.get("last_name", "last_name"), "").strip()
            company = row.get(field_map.get("company_name", "company_name"), "").strip()
            title = row.get(field_map.get("job_title", "job_title"), "").strip()

            if not first_name or not last_name:
                # Try to split full name
                full = row.get("name", row.get("full_name", row.get("Name", ""))).strip()
                if full:
                    parts = full.split(" ", 1)
                    first_name = first_name or parts[0]
                    last_name = last_name or (parts[1] if len(parts) > 1 else parts[0])

            if not first_name:
                errors_list.append({"row": row_count, "error": "Missing first name"})
                continue

            if db.query(Lead).filter(Lead.email == email).first():
                duplicates += 1
                continue

            lead = Lead(
                first_name=first_name,
                last_name=last_name or "",
                full_name=f"{first_name} {last_name}".strip(),
                email=email,
                phone=row.get(field_map.get("phone", "phone"), "").strip() or None,
                linkedin_url=row.get(field_map.get("linkedin_url", "linkedin_url"), "").strip() or None,
                company_name=company or "Unknown",
                job_title=title or "Unknown",
                industry=row.get(field_map.get("industry", "industry"), "").strip() or None,
                location_city=row.get(field_map.get("location_city", "city"), "").strip() or None,
                location_state=row.get(field_map.get("location_state", "state"), "").strip() or None,
                location_country=row.get(field_map.get("location_country", "country"), "").strip() or None,
                source="csv_upload",
                tags=tag_list,
            )
            db.add(lead)
            created += 1

            if row_count <= 5:
                preview_rows.append(row)

        except Exception as e:
            errors_list.append({"row": row_count, "error": str(e)})

    db.commit()
    return {
        "total_rows": row_count,
        "created": created,
        "duplicates": duplicates,
        "errors": len(errors_list),
        "error_details": errors_list[:50],
        "preview_rows": preview_rows,
        "column_mapping": field_map,
    }


@router.get("", response_model=LeadListResponse)
def list_leads(
    status: Optional[str] = None,
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
    industry: Optional[str] = None,
    company_size: Optional[str] = None,
    assigned_to: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Lead)

    if status:
        query = query.filter(Lead.status == status)
    if score_min is not None:
        query = query.filter(Lead.lead_score >= score_min)
    if score_max is not None:
        query = query.filter(Lead.lead_score <= score_max)
    if industry:
        query = query.filter(Lead.industry == industry)
    if company_size:
        query = query.filter(Lead.company_size == company_size)
    if assigned_to:
        query = query.filter(Lead.assigned_to == assigned_to)
    if source:
        query = query.filter(Lead.source == source)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.full_name.ilike(term),
                Lead.email.ilike(term),
                Lead.company_name.ilike(term),
            )
        )
    if tags:
        for tag in tags.split(","):
            query = query.filter(Lead.tags.contains([tag.strip()]))

    total = query.count()
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    leads = query.offset((page - 1) * page_size).limit(page_size).all()

    return LeadListResponse(
        leads=[LeadResponse.model_validate(l) for l in leads],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: str, data: LeadUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    update_data = data.model_dump(exclude_unset=True)
    if "first_name" in update_data or "last_name" in update_data:
        fn = update_data.get("first_name", lead.first_name)
        ln = update_data.get("last_name", lead.last_name)
        update_data["full_name"] = f"{fn} {ln}"
    for key, val in update_data.items():
        setattr(lead, key, val)
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()


@router.get("/{lead_id}/interactions", response_model=list[InteractionResponse])
def get_lead_interactions(
    lead_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    interactions = (
        db.query(Interaction)
        .filter(Interaction.lead_id == lead_id)
        .order_by(Interaction.created_at.desc())
        .all()
    )
    return [InteractionResponse.model_validate(i) for i in interactions]


@router.get("/stats/pipeline")
def get_pipeline_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    return {status: count for status, count in results}


@router.post("/{lead_id}/notes")
def add_note(
    lead_id: str,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    note_text = body.get("note", "")
    interaction = Interaction(
        lead_id=lead_id,
        type=InteractionType.note_added,
        channel=InteractionChannel.internal,
        direction=InteractionDirection.internal,
        body=note_text,
    )
    db.add(interaction)
    if note_text:
        existing = lead.notes or ""
        lead.notes = f"{existing}\n\n[{user.name}]: {note_text}".strip()
    db.commit()
    return {"status": "ok"}
