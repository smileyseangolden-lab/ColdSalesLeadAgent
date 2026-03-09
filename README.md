# LeadFlow AI - Autonomous Sales Lead Nurturing Platform

An AI-powered platform that autonomously nurtures cold sales leads through personalized email campaigns, intelligent reply handling, and automated lead scoring — designed for B2B industrial automation sales teams.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                   │
│  Dashboard │ Leads │ Campaigns │ Agents │ Handoffs    │
└──────────────────────┬──────────────────────────────┘
                       │ REST API + WebSocket
┌──────────────────────┴──────────────────────────────┐
│                Backend (FastAPI)                      │
│  Auth │ Lead CRUD │ Campaign Engine │ Webhooks        │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
    ┌──────┴──────┐        ┌──────┴──────┐
    │ PostgreSQL  │        │   Redis     │
    │  Database   │        │  Queue      │
    └─────────────┘        └──────┬──────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Celery Workers         │
                    │  ┌─────────────────────┐   │
                    │  │ Outbound Email Agent │   │
                    │  │ Reply Handler Agent  │   │
                    │  │ Lead Scoring Agent   │   │
                    │  │ Research Agent       │   │
                    │  └─────────┬───────────┘   │
                    └────────────┼───────────────┘
                                 │
                    ┌────────────┴───────────┐
                    │   Claude API (Sonnet)   │
                    │  Personalization │ NLU   │
                    └────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts, React Query |
| Backend | Python FastAPI, SQLAlchemy ORM |
| Database | PostgreSQL 16 |
| Queue | Celery + Redis |
| AI Engine | Anthropic Claude (claude-sonnet-4-20250514) |
| Email | SMTP with tracking pixels + link tracking |
| Real-time | Socket.IO |
| Auth | JWT with bcrypt |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- An Anthropic API key

### Setup

1. **Clone and configure:**
```bash
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **Seed the database:**
```bash
docker-compose exec backend python seed.py
```

4. **Access the application:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

5. **Login with seed data:**
- Email: `admin@leadflow.ai`
- Password: `password123`

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

**Worker:**
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Core Features

### Lead Management
- Manual entry with validation
- CSV upload with auto-column mapping and duplicate detection
- Filterable, searchable lead table
- Full lead detail view with interaction timeline
- Bulk operations (tag, assign, enroll)

### Campaign Engine
- Multi-step campaign wizard (name → sequence → schedule → review)
- Email template editor with variable substitution (`{{first_name}}`, `{{company_name}}`)
- AI personalization toggle per step — Claude rewrites templates for each lead
- Conditional branching (on open, click, reply, no engagement)
- A/B testing support via variant groups

### Autonomous AI Agents

| Agent | Schedule | Function |
|-------|----------|----------|
| **Outbound Email** | Every 5 min | Sends personalized campaign emails |
| **Reply Handler** | Every 2 min | Analyzes replies, classifies intent, auto-responds |
| **Lead Scorer** | Every 30 min | Recalculates scores from engagement signals |
| **Research Agent** | On demand | Enriches leads with company intelligence |

### Reply Handler Intelligence
When a lead replies, the AI:
1. Classifies intent (interested, question, objection, meeting request, unsubscribe, etc.)
2. Assesses sentiment and confidence
3. Takes autonomous action:
   - **Question** → Generates helpful, informed response
   - **Objection** → Crafts thoughtful rebuttal
   - **Interested/Meeting** → Triggers handoff to human rep
   - **Unsubscribe** → Immediately stops all outreach
   - **Out of Office** → Logs and maintains schedule
4. Max 5 autonomous replies before mandatory human handoff
5. Low confidence (< 0.7) → routes to human review

### Lead Scoring
- **0-20**: Cold
- **21-40**: Warming
- **41-60**: Engaged
- **61-80**: Warm (notify rep)
- **81-100**: Hot (auto-handoff)

Signals: opens (+2), clicks (+5), replies (+15), meetings (+25), bounces (-50), time decay

### Handoff System
When a lead is ready, the AI generates a comprehensive briefing:
- Interaction history summary
- Detected pain points
- Recommended talking points
- Objections raised and how they were addressed
- Suggested next steps

### Dashboard
- Real-time pipeline visualization
- Agent status monitoring
- Campaign performance metrics
- Activity feed of all agent actions

### Compliance
- CAN-SPAM: auto unsubscribe links, physical address footer
- One-click unsubscribe handling
- Rate limiting per email account
- Human override on any lead at any time
- Full audit trail of all agent actions

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/leads` | List leads (filterable) |
| POST | `/api/v1/leads` | Create lead |
| POST | `/api/v1/leads/bulk` | Bulk import |
| POST | `/api/v1/leads/upload` | CSV upload |
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create campaign |
| POST | `/api/v1/campaigns/{id}/enroll` | Enroll lead |
| GET | `/api/v1/agents` | List AI agents |
| GET | `/api/v1/handoffs` | List handoffs |
| GET | `/api/v1/dashboard/overview` | Dashboard data |
| POST | `/api/v1/webhooks/inbound-email/sendgrid` | Inbound email webhook |

## Database Schema

10 core tables: `users`, `leads`, `campaigns`, `campaign_steps`, `lead_campaign_enrollments`, `interactions`, `ai_agents`, `email_accounts`, `handoffs`, `lead_score_history`

All tables include UUIDs, timestamps, proper indexes, and foreign key constraints.

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `ANTHROPIC_API_KEY` — Required for AI features
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis for Celery queue
- `JWT_SECRET` — Change in production
- `ENCRYPTION_KEY` — For SMTP password encryption
