from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import AIAgent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.api.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    data: AgentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "manager")),
):
    agent = AIAgent(
        name=data.name,
        type=data.type,
        config=data.config or AIAgent.config.default.arg,
        persona=data.persona or AIAgent.persona.default.arg,
        system_prompt=data.system_prompt or AIAgent.system_prompt.default.arg,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.get("", response_model=list[AgentResponse])
def list_agents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    agents = db.query(AIAgent).order_by(AIAgent.created_at.desc()).all()
    return [AgentResponse.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    data: AgentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "manager")),
):
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(agent, key, val)
    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
