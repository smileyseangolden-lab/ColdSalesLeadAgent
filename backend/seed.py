"""Database seeding script with realistic sample data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password, encrypt_value
from app.models import *


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already seeded. Skipping.")
            return

        # --- Users ---
        users = [
            User(
                email="admin@leadflow.ai",
                name="Alex Admin",
                password_hash=hash_password("password123"),
                role="admin",
                team="Management",
            ),
            User(
                email="sarah@leadflow.ai",
                name="Sarah Martinez",
                password_hash=hash_password("password123"),
                role="manager",
                team="West",
            ),
            User(
                email="john@leadflow.ai",
                name="John Chen",
                password_hash=hash_password("password123"),
                role="sales_rep",
                team="East",
            ),
            User(
                email="maria@leadflow.ai",
                name="Maria Johnson",
                password_hash=hash_password("password123"),
                role="sales_rep",
                team="Central",
            ),
        ]
        for u in users:
            db.add(u)
        db.flush()

        # --- AI Agents ---
        agents = [
            AIAgent(
                name="Outbound Email Agent",
                type="outbound_email",
                status="active",
                persona="You are a knowledgeable sales development representative for E Tech Group, an industrial automation company. You are helpful, consultative, and focus on understanding the prospect's challenges before pitching solutions.",
                system_prompt="You are an AI sales development representative for E Tech Group. Your goal is to engage prospects in meaningful conversations about their industrial automation challenges. Be professional, knowledgeable about PLC programming, SCADA systems, robotics integration, and data analytics for manufacturing.",
            ),
            AIAgent(
                name="Reply Handler Agent",
                type="reply_handler",
                status="active",
                persona="You are an intelligent reply handler that analyzes prospect responses and determines the best course of action. You understand nuance in business communication.",
                system_prompt="You are an AI that analyzes email replies from sales prospects. You classify intent, sentiment, and determine appropriate next actions. Always be accurate and thoughtful in your analysis.",
            ),
            AIAgent(
                name="Lead Scoring Agent",
                type="lead_scorer",
                status="active",
                persona="You are a data-driven lead scoring engine that evaluates prospects based on engagement signals and firmographic data.",
                system_prompt="You are a lead scoring AI. Evaluate leads based on their engagement history, company fit, and behavioral signals. Provide accurate scores and clear reasoning.",
            ),
            AIAgent(
                name="Research Agent",
                type="research_agent",
                status="active",
                persona="You are a research analyst that gathers intelligence about prospects and their companies.",
                system_prompt="You are a research AI that enriches lead data with relevant company information, industry trends, and prospect insights. Be thorough but concise.",
            ),
        ]
        for a in agents:
            db.add(a)
        db.flush()

        outbound_agent = agents[0]

        # --- Sample Leads ---
        sample_leads = [
            Lead(
                first_name="James", last_name="Wilson", full_name="James Wilson",
                email="jwilson@pfizer.com", company_name="Pfizer", job_title="VP Manufacturing",
                industry="Pharmaceutical", company_size="5000+",
                location_city="New York", location_state="NY", location_country="US",
                source="csv_upload", status="new", lead_score=15,
                assigned_to=users[2].id, assigned_agent_id=outbound_agent.id,
                tags=["life_sciences", "enterprise", "high_value"],
            ),
            Lead(
                first_name="Emily", last_name="Chang", full_name="Emily Chang",
                email="echang@tesla.com", company_name="Tesla", job_title="Director of Automation",
                industry="Automotive", company_size="5000+",
                location_city="Fremont", location_state="CA", location_country="US",
                source="linkedin_import", status="contacted", lead_score=42,
                assigned_to=users[1].id, assigned_agent_id=outbound_agent.id,
                tags=["automotive", "robotics", "enterprise"],
            ),
            Lead(
                first_name="Michael", last_name="Torres", full_name="Michael Torres",
                email="mtorres@generalmills.com", company_name="General Mills",
                job_title="Plant Manager", industry="Food & Beverage", company_size="5000+",
                location_city="Minneapolis", location_state="MN", location_country="US",
                source="manual_entry", status="engaged", lead_score=58,
                assigned_to=users[3].id, assigned_agent_id=outbound_agent.id,
                tags=["food_bev", "plant_manager"],
            ),
            Lead(
                first_name="Rachel", last_name="Kim", full_name="Rachel Kim",
                email="rkim@medtronic.com", company_name="Medtronic",
                job_title="Sr. Controls Engineer", industry="Medical Devices", company_size="5000+",
                location_city="Dublin", location_state="OH", location_country="US",
                source="csv_upload", status="warm", lead_score=71,
                assigned_to=users[2].id, assigned_agent_id=outbound_agent.id,
                tags=["medical_devices", "controls"],
            ),
            Lead(
                first_name="David", last_name="Okonkwo", full_name="David Okonkwo",
                email="dokonkwo@dow.com", company_name="Dow Chemical",
                job_title="Automation Manager", industry="Chemicals", company_size="5000+",
                location_city="Midland", location_state="MI", location_country="US",
                source="referral", status="hot", lead_score=85,
                assigned_to=users[3].id, assigned_agent_id=outbound_agent.id,
                tags=["chemicals", "automation", "high_value"],
            ),
            Lead(
                first_name="Lisa", last_name="Nakamura", full_name="Lisa Nakamura",
                email="lnakamura@boeing.com", company_name="Boeing",
                job_title="Systems Integration Lead", industry="Aerospace", company_size="5000+",
                location_city="Seattle", location_state="WA", location_country="US",
                source="csv_upload", status="new", lead_score=10,
                assigned_to=users[1].id, tags=["aerospace", "systems"],
            ),
            Lead(
                first_name="Robert", last_name="Singh", full_name="Robert Singh",
                email="rsingh@abinbev.com", company_name="AB InBev",
                job_title="Director of Engineering", industry="Food & Beverage", company_size="5000+",
                location_city="St. Louis", location_state="MO", location_country="US",
                source="manual_entry", status="contacted", lead_score=28,
                assigned_to=users[3].id, tags=["food_bev", "director"],
            ),
            Lead(
                first_name="Amanda", last_name="Foster", full_name="Amanda Foster",
                email="afoster@rockwellautomation.com", company_name="Rockwell Automation",
                job_title="Business Development Manager", industry="Industrial Automation",
                company_size="1001-5000",
                location_city="Milwaukee", location_state="WI", location_country="US",
                source="linkedin_import", status="new", lead_score=5,
                assigned_to=users[2].id, tags=["rockwell", "partner"],
            ),
            Lead(
                first_name="Carlos", last_name="Mendez", full_name="Carlos Mendez",
                email="cmendez@jnj.com", company_name="Johnson & Johnson",
                job_title="Manufacturing Excellence Lead", industry="Pharmaceutical",
                company_size="5000+",
                location_city="New Brunswick", location_state="NJ", location_country="US",
                source="csv_upload", status="engaged", lead_score=52,
                assigned_to=users[2].id, tags=["pharma", "manufacturing"],
            ),
            Lead(
                first_name="Patricia", last_name="O'Brien", full_name="Patricia O'Brien",
                email="pobrien@3m.com", company_name="3M",
                job_title="VP Operations", industry="Manufacturing", company_size="5000+",
                location_city="St. Paul", location_state="MN", location_country="US",
                source="referral", status="warm", lead_score=67,
                assigned_to=users[1].id, tags=["manufacturing", "vp", "high_value"],
            ),
        ]
        for lead in sample_leads:
            db.add(lead)
        db.flush()

        # --- Sample Campaign ---
        campaign = Campaign(
            name="Industrial Automation Cold Outreach Q1",
            description="Multi-step email campaign targeting manufacturing decision-makers about automation solutions",
            type="email_sequence",
            status="active",
            target_criteria={"industry": ["Manufacturing", "Pharmaceutical", "Automotive"], "company_size": ["1001-5000", "5000+"]},
            created_by=users[0].id,
            settings={
                "sending_schedule": {"days": ["mon", "tue", "wed", "thu", "fri"]},
                "timezone": "America/New_York",
                "daily_send_limit": 50,
                "min_wait_minutes": 60,
            },
        )
        db.add(campaign)
        db.flush()

        steps = [
            CampaignStep(
                campaign_id=campaign.id, step_number=1, channel="email",
                delay_days=0, delay_hours=0,
                subject_template="Quick question about {{company_name}}'s automation strategy",
                body_template="""Hi {{first_name}},

I've been following {{company_name}}'s growth in the {{industry}} space and noticed you're leading some interesting initiatives as {{job_title}}.

Many companies in your industry are finding that their legacy automation systems can't keep up with current demands — whether it's OEE optimization, real-time data analytics, or integrating robotics into existing lines.

I'd love to learn more about your current challenges. Would you be open to a brief 15-minute conversation this week?

Best regards""",
                ai_personalization_enabled=True,
                ai_personalization_instructions="Reference their specific industry challenges. Keep it casual and consultative.",
            ),
            CampaignStep(
                campaign_id=campaign.id, step_number=2, channel="email",
                delay_days=3, delay_hours=0,
                subject_template="Re: {{company_name}}'s automation strategy",
                body_template="""Hi {{first_name}},

Following up on my previous note. I wanted to share a quick insight:

We recently helped a {{industry}} company similar to {{company_name}} reduce their unplanned downtime by 40% through predictive maintenance integration with their existing PLC infrastructure.

The project took just 8 weeks from assessment to go-live. I'd be happy to walk through what that looked like.

Would a 15-minute call work this week?

Best""",
                ai_personalization_enabled=True,
                ai_personalization_instructions="Reference a specific value proposition relevant to their industry.",
            ),
            CampaignStep(
                campaign_id=campaign.id, step_number=3, channel="email",
                delay_days=5, delay_hours=0,
                subject_template="Thought you'd find this useful, {{first_name}}",
                body_template="""Hi {{first_name}},

I know things get busy, so I'll keep this brief.

We put together a case study on how {{industry}} companies are modernizing their automation infrastructure without ripping and replacing existing systems. It covers the ROI framework that companies like {{company_name}} typically find most relevant.

Happy to send it over if you're interested — just reply and I'll share the link.

Best""",
                ai_personalization_enabled=True,
            ),
            CampaignStep(
                campaign_id=campaign.id, step_number=4, channel="email",
                delay_days=7, delay_hours=0,
                subject_template="Last note from me, {{first_name}}",
                body_template="""Hi {{first_name}},

I don't want to clutter your inbox, so this will be my last note for now.

If automation optimization isn't a priority right now, I completely understand. But if it does become relevant, I'd be happy to be a resource.

You can always reach out directly — I genuinely enjoy talking about this stuff.

All the best""",
                ai_personalization_enabled=False,
            ),
        ]
        for step in steps:
            db.add(step)

        db.commit()
        print("Database seeded successfully!")
        print(f"  - {len(users)} users created (login: admin@leadflow.ai / password123)")
        print(f"  - {len(agents)} AI agents created")
        print(f"  - {len(sample_leads)} sample leads created")
        print(f"  - 1 campaign with {len(steps)} steps created")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
