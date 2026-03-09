"""Background agent tasks for autonomous lead nurturing."""
import structlog
from datetime import datetime, timedelta, timezone
from celery import shared_task
from sqlalchemy.orm import Session, joinedload
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.lead import Lead, LeadStatus
from app.models.campaign import Campaign, CampaignStep, CampaignStatus
from app.models.enrollment import LeadCampaignEnrollment, EnrollmentStatus
from app.models.interaction import (
    Interaction, InteractionType, InteractionChannel, InteractionDirection,
    Sentiment, Intent,
)
from app.models.agent import AIAgent, AgentType, AgentStatus
from app.models.email_account import EmailAccount
from app.models.handoff import Handoff, HandoffStatus
from app.models.score_history import LeadScoreHistory, ScoredBy
from app.services.ai_service import personalize_email, analyze_reply, generate_handoff_context, score_lead
from app.services.email_service import send_email, substitute_variables

logger = structlog.get_logger()


def _get_db() -> Session:
    return SessionLocal()


def _get_agent(db: Session, agent_type: str) -> AIAgent | None:
    return db.query(AIAgent).filter(
        AIAgent.type == agent_type,
        AIAgent.status == AgentStatus.active,
    ).first()


def _lead_to_dict(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "full_name": lead.full_name,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "email": lead.email,
        "company_name": lead.company_name,
        "job_title": lead.job_title,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "lead_score": lead.lead_score,
        "tags": lead.tags,
        "custom_fields": lead.custom_fields,
    }


def _interactions_to_list(interactions: list[Interaction]) -> list[dict]:
    return [
        {
            "type": i.type,
            "direction": i.direction,
            "channel": i.channel,
            "subject": i.subject,
            "body": i.body,
            "sentiment": i.sentiment,
            "intent": i.intent,
            "created_at": i.created_at.isoformat() if i.created_at else "",
        }
        for i in interactions
    ]


def _update_lead_score(db: Session, lead: Lead, old_score: int, new_score: int, reason: str, scored_by: str = "ai_agent"):
    new_score = max(0, min(100, new_score))
    if new_score == old_score:
        return
    lead.lead_score = new_score
    history = LeadScoreHistory(
        lead_id=lead.id,
        old_score=old_score,
        new_score=new_score,
        reason=reason,
        scored_by=scored_by,
    )
    db.add(history)

    # Update status based on score
    if new_score >= 81:
        lead.status = LeadStatus.hot
    elif new_score >= 61:
        lead.status = LeadStatus.warm
    elif new_score >= 41:
        lead.status = LeadStatus.engaged
    elif new_score >= 21:
        if lead.status == LeadStatus.new:
            lead.status = LeadStatus.contacted


def _create_handoff(db: Session, lead: Lead, agent: AIAgent, reason: str):
    """Create a handoff to the lead's assigned human rep."""
    if not lead.assigned_to:
        logger.warning("no_assigned_user_for_handoff", lead_id=lead.id)
        return

    interactions = (
        db.query(Interaction)
        .filter(Interaction.lead_id == lead.id)
        .order_by(Interaction.created_at.asc())
        .all()
    )
    context = generate_handoff_context(_lead_to_dict(lead), _interactions_to_list(interactions))

    handoff = Handoff(
        lead_id=lead.id,
        from_agent_id=agent.id,
        to_user_id=lead.assigned_to,
        reason=reason,
        lead_score_at_handoff=lead.lead_score,
        context_summary=context,
        status=HandoffStatus.pending,
    )
    db.add(handoff)
    lead.status = LeadStatus.handed_off
    lead.handoff_at = datetime.now(timezone.utc)

    # Pause all enrollments
    enrollments = db.query(LeadCampaignEnrollment).filter(
        LeadCampaignEnrollment.lead_id == lead.id,
        LeadCampaignEnrollment.status == EnrollmentStatus.active,
    ).all()
    for e in enrollments:
        e.status = EnrollmentStatus.handed_off

    logger.info("handoff_created", lead_id=lead.id, to_user=lead.assigned_to)


@shared_task(name="app.tasks.agent_tasks.run_outbound_email_agent")
def run_outbound_email_agent():
    """Process outbound email campaign steps for enrolled leads."""
    db = _get_db()
    try:
        agent = _get_agent(db, AgentType.outbound_email)
        if not agent:
            return {"status": "no_active_agent"}

        now = datetime.now(timezone.utc)
        agent.last_active_at = now

        # Find enrollments ready for next step
        enrollments = (
            db.query(LeadCampaignEnrollment)
            .filter(
                LeadCampaignEnrollment.status == EnrollmentStatus.active,
                LeadCampaignEnrollment.next_step_at <= now,
            )
            .limit(50)
            .all()
        )

        processed = 0
        errors = 0

        for enrollment in enrollments:
            try:
                campaign = (
                    db.query(Campaign)
                    .options(joinedload(Campaign.steps))
                    .filter(Campaign.id == enrollment.campaign_id)
                    .first()
                )
                if not campaign or campaign.status != CampaignStatus.active:
                    continue

                lead = db.query(Lead).filter(Lead.id == enrollment.lead_id).first()
                if not lead or lead.status in (LeadStatus.do_not_contact, LeadStatus.lost, LeadStatus.converted):
                    enrollment.status = EnrollmentStatus.completed
                    continue

                # Find current step
                next_step_num = enrollment.current_step + 1
                step = next(
                    (s for s in campaign.steps if s.step_number == next_step_num), None
                )
                if not step:
                    enrollment.status = EnrollmentStatus.completed
                    continue

                if step.channel != "email":
                    # Skip non-email steps (LinkedIn etc.)
                    enrollment.current_step = next_step_num
                    following = next(
                        (s for s in campaign.steps if s.step_number == next_step_num + 1), None
                    )
                    if following:
                        enrollment.next_step_at = now + timedelta(days=following.delay_days, hours=following.delay_hours)
                    else:
                        enrollment.status = EnrollmentStatus.completed
                    continue

                # Find email account
                email_account = db.query(EmailAccount).filter(
                    EmailAccount.is_active == True,
                    EmailAccount.sends_today < EmailAccount.daily_send_limit,
                ).first()
                if not email_account:
                    continue

                # Build email content
                lead_dict = _lead_to_dict(lead)
                interactions = (
                    db.query(Interaction)
                    .filter(Interaction.lead_id == lead.id)
                    .order_by(Interaction.created_at.desc())
                    .limit(10)
                    .all()
                )

                if step.ai_personalization_enabled:
                    result = personalize_email(
                        agent_persona=agent.persona,
                        lead_context=lead_dict,
                        interaction_history=_interactions_to_list(interactions),
                        campaign_description=campaign.description or campaign.name,
                        step_instructions=step.ai_personalization_instructions or "",
                        body_template=step.body_template,
                        subject_template=step.subject_template,
                    )
                    subject = result.get("subject", step.subject_template or "Following up")
                    body = result.get("body", step.body_template)
                else:
                    subject = substitute_variables(step.subject_template or "Following up", lead_dict)
                    body = substitute_variables(step.body_template, lead_dict)

                # Create interaction record first (for tracking ID)
                interaction = Interaction(
                    lead_id=lead.id,
                    campaign_id=campaign.id,
                    campaign_step_id=step.id,
                    agent_id=agent.id,
                    type=InteractionType.email_sent,
                    channel=InteractionChannel.email,
                    direction=InteractionDirection.outbound,
                    subject=subject,
                    body=body,
                )
                db.add(interaction)
                db.flush()

                # Send the email
                success = send_email(
                    smtp_host=email_account.smtp_host,
                    smtp_port=email_account.smtp_port,
                    smtp_username=email_account.smtp_username,
                    smtp_password_encrypted=email_account.smtp_password_encrypted,
                    from_email=email_account.email_address,
                    to_email=lead.email,
                    subject=subject,
                    body=body,
                    signature_html=email_account.signature_html or "",
                    tracking_id=interaction.id,
                )

                if success:
                    email_account.sends_today += 1
                    lead.last_contacted_at = now
                    if lead.status == LeadStatus.new:
                        lead.status = LeadStatus.contacted

                    enrollment.current_step = next_step_num
                    enrollment.last_step_executed_at = now

                    # Calculate next step time
                    following = next(
                        (s for s in campaign.steps if s.step_number == next_step_num + 1), None
                    )
                    if following:
                        enrollment.next_step_at = now + timedelta(
                            days=following.delay_days, hours=following.delay_hours
                        )
                    else:
                        enrollment.status = EnrollmentStatus.completed

                    processed += 1
                else:
                    errors += 1
                    interaction.type = InteractionType.email_bounced

            except Exception as e:
                logger.error("outbound_agent_error", lead_id=enrollment.lead_id, error=str(e))
                errors += 1

        # Update agent stats
        stats = agent.stats or {}
        stats["messages_sent_today"] = stats.get("messages_sent_today", 0) + processed
        stats["total_messages"] = stats.get("total_messages", 0) + processed
        stats["errors_today"] = stats.get("errors_today", 0) + errors
        agent.stats = stats

        db.commit()
        return {"processed": processed, "errors": errors}

    except Exception as e:
        logger.error("outbound_agent_fatal", error=str(e))
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.agent_tasks.process_inbound_reply")
def process_inbound_reply(interaction_id: str):
    """Process a single inbound reply — triggered immediately when email arrives."""
    db = _get_db()
    try:
        agent = _get_agent(db, AgentType.reply_handler)
        if not agent:
            return {"status": "no_active_reply_handler"}

        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return {"status": "interaction_not_found"}

        lead = db.query(Lead).filter(Lead.id == interaction.lead_id).first()
        if not lead:
            return {"status": "lead_not_found"}

        # Get full interaction history
        history = (
            db.query(Interaction)
            .filter(Interaction.lead_id == lead.id)
            .order_by(Interaction.created_at.desc())
            .limit(20)
            .all()
        )

        # Analyze reply with Claude
        analysis = analyze_reply(
            lead_context=_lead_to_dict(lead),
            interaction_history=_interactions_to_list(history),
            reply_subject=interaction.subject or "",
            reply_body=interaction.body,
        )

        # Update the interaction with analysis
        interaction.sentiment = analysis.get("sentiment", "unknown")
        interaction.intent = analysis.get("intent", "unknown")
        interaction.ai_analysis = analysis

        confidence = analysis.get("confidence", 0)
        action = analysis.get("recommended_action", "pause")
        intent = analysis.get("intent", "unknown")

        # Pause active campaign enrollments on reply
        enrollments = db.query(LeadCampaignEnrollment).filter(
            LeadCampaignEnrollment.lead_id == lead.id,
            LeadCampaignEnrollment.status == EnrollmentStatus.active,
        ).all()
        for e in enrollments:
            e.status = EnrollmentStatus.replied

        # Update score
        old_score = lead.lead_score
        adjustment = analysis.get("score_adjustment", 0)
        _update_lead_score(
            db, lead, old_score, old_score + adjustment,
            analysis.get("score_reason", "Reply received"),
        )

        # Low confidence → route to human review
        if confidence < settings.AI_CONFIDENCE_THRESHOLD:
            logger.info("low_confidence_reply", lead_id=lead.id, confidence=confidence)
            if lead.assigned_to:
                _create_handoff(db, lead, agent, f"Low confidence reply analysis ({confidence}). Manual review needed.")
            db.commit()
            return {"status": "routed_to_human", "confidence": confidence}

        # Take action based on intent
        if intent in ("out_of_office", "auto_reply"):
            # Log and continue — don't change sequence
            for e in enrollments:
                e.status = EnrollmentStatus.active
            logger.info("auto_reply_detected", lead_id=lead.id)

        elif intent == "unsubscribe" or action == "do_not_contact":
            lead.status = LeadStatus.do_not_contact
            _update_lead_score(db, lead, lead.lead_score, 0, "Unsubscribed")

        elif intent == "not_interested":
            lead.status = LeadStatus.lost
            _update_lead_score(db, lead, lead.lead_score, max(0, lead.lead_score - 30), "Not interested")

        elif intent in ("interested", "meeting_request") or action == "handoff":
            _update_lead_score(db, lead, lead.lead_score, min(100, lead.lead_score + 25), "Expressed interest")
            if lead.lead_score >= settings.HANDOFF_SCORE_THRESHOLD or intent == "meeting_request":
                _create_handoff(db, lead, agent, f"Lead expressed interest: {analysis.get('summary', '')}")
            elif analysis.get("recommended_reply"):
                _send_autonomous_reply(db, agent, lead, analysis["recommended_reply"], interaction)

        elif intent in ("question", "objection") and action == "reply":
            reply_text = analysis.get("recommended_reply", "")
            if reply_text:
                # Check max autonomous reply count
                auto_replies = db.query(Interaction).filter(
                    Interaction.lead_id == lead.id,
                    Interaction.agent_id == agent.id,
                    Interaction.type == InteractionType.email_sent,
                ).count()
                if auto_replies >= settings.MAX_AUTONOMOUS_REPLIES:
                    _create_handoff(db, lead, agent, "Maximum autonomous reply count reached.")
                else:
                    _send_autonomous_reply(db, agent, lead, reply_text, interaction)

        elif action == "handoff" or analysis.get("handoff_urgency") == "immediate":
            _create_handoff(db, lead, agent, analysis.get("summary", "Handoff requested by AI"))

        agent.last_active_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "processed", "intent": intent, "action": action}

    except Exception as e:
        logger.error("reply_handler_error", interaction_id=interaction_id, error=str(e))
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def _send_autonomous_reply(db: Session, agent: AIAgent, lead: Lead, reply_text: str, original: Interaction):
    """Send an autonomous reply email."""
    email_account = db.query(EmailAccount).filter(
        EmailAccount.is_active == True,
        EmailAccount.sends_today < EmailAccount.daily_send_limit,
    ).first()
    if not email_account:
        logger.warning("no_email_account_available", lead_id=lead.id)
        return

    subject = f"Re: {original.subject}" if original.subject else "Re: Following up"
    reply_interaction = Interaction(
        lead_id=lead.id,
        agent_id=agent.id,
        type=InteractionType.email_sent,
        channel=InteractionChannel.email,
        direction=InteractionDirection.outbound,
        subject=subject,
        body=reply_text,
    )
    db.add(reply_interaction)
    db.flush()

    success = send_email(
        smtp_host=email_account.smtp_host,
        smtp_port=email_account.smtp_port,
        smtp_username=email_account.smtp_username,
        smtp_password_encrypted=email_account.smtp_password_encrypted,
        from_email=email_account.email_address,
        to_email=lead.email,
        subject=subject,
        body=reply_text,
        signature_html=email_account.signature_html or "",
        tracking_id=reply_interaction.id,
    )
    if success:
        email_account.sends_today += 1
        lead.last_contacted_at = datetime.now(timezone.utc)
    else:
        reply_interaction.type = InteractionType.email_bounced


@shared_task(name="app.tasks.agent_tasks.run_reply_handler_agent")
def run_reply_handler_agent():
    """Periodic scan for unprocessed inbound emails (backup to webhook)."""
    db = _get_db()
    try:
        agent = _get_agent(db, AgentType.reply_handler)
        if not agent:
            return {"status": "no_active_agent"}

        # Find unprocessed inbound emails (no ai_analysis yet)
        unprocessed = (
            db.query(Interaction)
            .filter(
                Interaction.type == InteractionType.email_received,
                Interaction.ai_analysis == None,
            )
            .limit(20)
            .all()
        )

        for interaction in unprocessed:
            process_inbound_reply.delay(interaction.id)

        agent.last_active_at = datetime.now(timezone.utc)
        db.commit()
        return {"queued": len(unprocessed)}
    except Exception as e:
        logger.error("reply_handler_scan_error", error=str(e))
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.agent_tasks.run_lead_scoring_agent")
def run_lead_scoring_agent():
    """Recalculate lead scores based on engagement signals."""
    db = _get_db()
    try:
        agent = _get_agent(db, AgentType.lead_scorer)
        if not agent:
            return {"status": "no_active_agent"}

        now = datetime.now(timezone.utc)
        agent.last_active_at = now

        # Get active leads
        leads = (
            db.query(Lead)
            .filter(Lead.status.notin_([
                LeadStatus.do_not_contact, LeadStatus.converted, LeadStatus.lost
            ]))
            .all()
        )

        updated = 0
        for lead in leads:
            old_score = lead.lead_score
            new_score = old_score

            # Count engagement signals
            interactions = (
                db.query(Interaction)
                .filter(Interaction.lead_id == lead.id)
                .order_by(Interaction.created_at.desc())
                .all()
            )

            # Rule-based scoring
            for i in interactions:
                if i.created_at and (now - i.created_at).days > 30:
                    continue  # Only consider recent interactions

                if i.type == InteractionType.email_opened:
                    new_score += 2
                elif i.type == InteractionType.email_clicked:
                    new_score += 5
                elif i.type == InteractionType.email_received and i.direction == InteractionDirection.inbound:
                    new_score += 15
                elif i.type == InteractionType.meeting_scheduled:
                    new_score += 25
                elif i.type == InteractionType.email_bounced:
                    new_score -= 50

            # Time decay: -1 per week without engagement
            if lead.last_contacted_at:
                days_since = (now - lead.last_contacted_at).days
                if days_since > 14:
                    decay = (days_since - 14) // 7
                    new_score -= decay

            # Count unanswered emails
            sent = sum(1 for i in interactions if i.type == InteractionType.email_sent)
            received = sum(1 for i in interactions if i.type == InteractionType.email_received)
            if sent >= 3 and received == 0:
                new_score -= 5

            new_score = max(0, min(100, new_score))
            if new_score != old_score:
                _update_lead_score(db, lead, old_score, new_score, "Periodic scoring update")
                updated += 1

                # Auto-handoff if score crosses threshold
                if new_score >= settings.HANDOFF_SCORE_THRESHOLD and old_score < settings.HANDOFF_SCORE_THRESHOLD:
                    _create_handoff(db, lead, agent, f"Lead score reached {new_score} (threshold: {settings.HANDOFF_SCORE_THRESHOLD})")

        db.commit()
        return {"leads_evaluated": len(leads), "scores_updated": updated}

    except Exception as e:
        logger.error("scoring_agent_error", error=str(e))
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@shared_task(name="app.tasks.agent_tasks.reset_daily_send_counts")
def reset_daily_send_counts():
    """Reset daily email send counters at midnight."""
    db = _get_db()
    try:
        db.query(EmailAccount).update({EmailAccount.sends_today: 0})

        # Reset agent daily stats
        agents = db.query(AIAgent).all()
        for agent in agents:
            stats = agent.stats or {}
            stats["messages_sent_today"] = 0
            stats["errors_today"] = 0
            agent.stats = stats

        db.commit()
        return {"status": "reset_complete"}
    except Exception as e:
        logger.error("reset_error", error=str(e))
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
