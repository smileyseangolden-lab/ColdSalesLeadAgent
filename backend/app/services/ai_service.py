"""Service for all Claude API interactions."""
import json
import structlog
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings

logger = structlog.get_logger()

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

MODEL = "claude-sonnet-4-20250514"


class AIServiceError(Exception):
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_claude(system_prompt: str, user_prompt: str, json_output: bool = False) -> str:
    """Call Claude API with retry logic."""
    if not client:
        raise AIServiceError("ANTHROPIC_API_KEY not configured")

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = message.content[0].text
        logger.info(
            "claude_api_call",
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
        return content
    except Exception as e:
        logger.error("claude_api_error", error=str(e))
        raise AIServiceError(f"Claude API call failed: {e}")


def personalize_email(
    agent_persona: str,
    lead_context: dict,
    interaction_history: list[dict],
    campaign_description: str,
    step_instructions: str,
    body_template: str,
    subject_template: str | None = None,
) -> dict:
    """Use Claude to personalize an email for a specific lead."""
    history_text = "\n".join(
        f"[{i.get('created_at', '')}] {i.get('direction', '')}: {i.get('body', '')[:200]}"
        for i in interaction_history[-10:]
    ) or "No prior interactions."

    system_prompt = f"""You are a sales development representative. Your persona: {agent_persona}

You are writing an email to:
- Name: {lead_context.get('full_name', '')}
- Title: {lead_context.get('job_title', '')}
- Company: {lead_context.get('company_name', '')}
- Industry: {lead_context.get('industry', 'Unknown')}
- Company Size: {lead_context.get('company_size', 'Unknown')}

Previous interactions with this lead:
{history_text}

Campaign context: {campaign_description}
Step instructions: {step_instructions or 'None provided'}

Rules:
- Rewrite the template to feel personally crafted for this specific person
- Reference their industry challenges naturally
- Keep it concise (under 150 words for cold outreach, under 100 for follow-ups)
- Use a natural, conversational tone — avoid sounding like a mass email
- Include a clear, low-friction call-to-action
- Do not use exclamation points excessively
- Do not use filler phrases like "I hope this email finds you well"
- Match the tone specified in the persona"""

    user_prompt = f"""Base template to personalize:
{body_template}

Respond with JSON:
{{"subject": "personalized subject line", "body": "personalized email body"}}"""

    if subject_template:
        user_prompt = f"""Subject template: {subject_template}

Body template to personalize:
{body_template}

Respond with JSON:
{{"subject": "personalized subject line", "body": "personalized email body"}}"""

    response = call_claude(system_prompt, user_prompt, json_output=True)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
        return {"subject": subject_template or "Following up", "body": response}


def analyze_reply(
    lead_context: dict,
    interaction_history: list[dict],
    reply_subject: str,
    reply_body: str,
) -> dict:
    """Analyze an inbound reply from a prospect."""
    history_text = "\n".join(
        f"[{i.get('created_at', '')}] {i.get('type', '')} ({i.get('direction', '')}): "
        f"Subject: {i.get('subject', 'N/A')}\n{i.get('body', '')[:300]}"
        for i in interaction_history[-15:]
    ) or "No prior interactions."

    system_prompt = """You are analyzing an email reply from a sales prospect. You must respond with valid JSON only."""

    user_prompt = f"""Lead profile:
- Name: {lead_context.get('full_name', '')}
- Title: {lead_context.get('job_title', '')}
- Company: {lead_context.get('company_name', '')}
- Industry: {lead_context.get('industry', 'Unknown')}
- Current Score: {lead_context.get('lead_score', 0)}

Complete interaction history (most recent first):
{history_text}

New reply from lead:
Subject: {reply_subject}
Body: {reply_body}

Analyze this reply and respond with a JSON object:
{{
  "intent": "interested|not_interested|question|objection|meeting_request|out_of_office|auto_reply|unsubscribe|referral|spam",
  "sentiment": "positive|neutral|negative",
  "confidence": 0.0-1.0,
  "summary": "One sentence summary of what the lead said",
  "extracted_questions": ["list of specific questions they asked"],
  "extracted_objections": ["list of specific objections they raised"],
  "recommended_action": "reply|handoff|pause|do_not_contact|create_referral_lead",
  "recommended_reply": "If action is reply, draft the full reply text here. Be helpful, consultative, and natural. Reference their specific points.",
  "score_adjustment": -20,
  "score_reason": "Why the score should change",
  "handoff_urgency": "none|low|medium|high|immediate"
}}"""

    response = call_claude(system_prompt, user_prompt, json_output=True)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
        return {
            "intent": "unknown",
            "sentiment": "unknown",
            "confidence": 0.0,
            "summary": "Could not analyze reply",
            "recommended_action": "pause",
            "score_adjustment": 0,
            "handoff_urgency": "none",
        }


def generate_handoff_context(lead_context: dict, interaction_history: list[dict]) -> str:
    """Generate a comprehensive handoff briefing for human sales rep."""
    history_text = "\n".join(
        f"[{i.get('created_at', '')}] {i.get('type', '')} ({i.get('direction', '')}): "
        f"{i.get('body', '')[:500]}"
        for i in interaction_history
    )

    system_prompt = "You are preparing a handoff briefing for a human sales representative."
    user_prompt = f"""Lead: {lead_context.get('full_name', '')}
Title: {lead_context.get('job_title', '')} at {lead_context.get('company_name', '')}
Industry: {lead_context.get('industry', 'Unknown')}
Score: {lead_context.get('lead_score', 0)}/100

Complete interaction history:
{history_text}

Create a comprehensive handoff briefing including:
1. Executive summary (2-3 sentences)
2. Key pain points or interests identified
3. Objections raised and how they were addressed
4. Recommended talking points for the first call
5. Suggested next steps
6. Any red flags or important notes

Keep it actionable and concise."""

    return call_claude(system_prompt, user_prompt)


def score_lead(lead_context: dict, interaction_history: list[dict], current_score: int) -> dict:
    """Use AI to evaluate lead score for ambiguous cases."""
    history_summary = "\n".join(
        f"- {i.get('type', '')}: {i.get('body', '')[:100]}"
        for i in interaction_history[-20:]
    )

    system_prompt = "You are a lead scoring AI. Respond with JSON only."
    user_prompt = f"""Evaluate this lead's score:

Lead: {lead_context.get('full_name', '')}
Title: {lead_context.get('job_title', '')} at {lead_context.get('company_name', '')}
Industry: {lead_context.get('industry', 'Unknown')}
Company Size: {lead_context.get('company_size', 'Unknown')}
Current Score: {current_score}

Recent interactions:
{history_summary}

Respond with JSON:
{{
  "new_score": 0-100,
  "reasoning": "explanation",
  "status_recommendation": "new|contacted|engaged|warm|hot|qualified"
}}"""

    response = call_claude(system_prompt, user_prompt, json_output=True)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
        return {"new_score": current_score, "reasoning": "Unable to evaluate", "status_recommendation": "contacted"}


def enhance_template(template: str, context: str = "") -> dict:
    """AI-enhance an email template."""
    system_prompt = "You are an expert email copywriter for B2B sales."
    user_prompt = f"""Improve this email template for better engagement:

Template:
{template}

Additional context: {context or 'B2B sales outreach'}

Respond with JSON:
{{
  "improved_subject": "better subject line",
  "improved_body": "improved email body",
  "suggestions": ["list of specific improvements made"]
}}"""

    response = call_claude(system_prompt, user_prompt, json_output=True)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
        return {"improved_subject": "", "improved_body": response, "suggestions": []}
