from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import encrypt_value
from app.models.email_account import EmailAccount
from app.schemas.email_account import EmailAccountCreate, EmailAccountUpdate, EmailAccountResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/email-accounts", tags=["email-accounts"])


@router.post("", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
def create_email_account(
    data: EmailAccountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if db.query(EmailAccount).filter(EmailAccount.email_address == data.email_address).first():
        raise HTTPException(status_code=400, detail="Email account already exists")

    account = EmailAccount(
        user_id=user.id,
        email_address=data.email_address,
        smtp_host=data.smtp_host,
        smtp_port=data.smtp_port,
        smtp_username=data.smtp_username,
        smtp_password_encrypted=encrypt_value(data.smtp_password),
        imap_host=data.imap_host,
        imap_port=data.imap_port,
        daily_send_limit=data.daily_send_limit,
        warmup_enabled=data.warmup_enabled,
        warmup_daily_increment=data.warmup_daily_increment,
        signature_html=data.signature_html,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return EmailAccountResponse.model_validate(account)


@router.get("", response_model=list[EmailAccountResponse])
def list_email_accounts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    accounts = db.query(EmailAccount).filter(EmailAccount.user_id == user.id).all()
    return [EmailAccountResponse.model_validate(a) for a in accounts]


@router.put("/{account_id}", response_model=EmailAccountResponse)
def update_email_account(
    account_id: str,
    data: EmailAccountUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id, EmailAccount.user_id == user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")

    update_data = data.model_dump(exclude_unset=True)
    if "smtp_password" in update_data:
        account.smtp_password_encrypted = encrypt_value(update_data.pop("smtp_password"))
    for key, val in update_data.items():
        setattr(account, key, val)
    db.commit()
    db.refresh(account)
    return EmailAccountResponse.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_account(
    account_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = db.query(EmailAccount).filter(
        EmailAccount.id == account_id, EmailAccount.user_id == user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    db.delete(account)
    db.commit()
