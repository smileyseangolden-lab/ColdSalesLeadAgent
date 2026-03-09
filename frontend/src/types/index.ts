export interface User {
  id: string
  email: string
  name: string
  role: string
  team: string | null
  notification_preferences: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Lead {
  id: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone: string | null
  linkedin_url: string | null
  company_name: string
  job_title: string
  industry: string | null
  company_size: string | null
  location_city: string | null
  location_state: string | null
  location_country: string | null
  source: string
  status: string
  lead_score: number
  assigned_to: string | null
  assigned_agent_id: string | null
  tags: string[]
  custom_fields: Record<string, unknown>
  notes: string | null
  last_contacted_at: string | null
  next_action_at: string | null
  handoff_at: string | null
  created_at: string
  updated_at: string
}

export interface LeadListResponse {
  leads: Lead[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Campaign {
  id: string
  name: string
  description: string | null
  type: string
  status: string
  target_criteria: Record<string, unknown>
  created_by: string
  settings: Record<string, unknown>
  stats_cache: Record<string, number>
  steps: CampaignStep[]
  created_at: string
  updated_at: string
}

export interface CampaignStep {
  id: string
  campaign_id: string
  step_number: number
  channel: string
  delay_days: number
  delay_hours: number
  subject_template: string | null
  body_template: string
  ai_personalization_enabled: boolean
  ai_personalization_instructions: string | null
  condition: Record<string, unknown> | null
  variant_group: string | null
  variant_label: string | null
  created_at: string
  updated_at: string
}

export interface AIAgent {
  id: string
  name: string
  type: string
  status: string
  config: Record<string, unknown>
  persona: string
  system_prompt: string
  stats: Record<string, number>
  last_active_at: string | null
  created_at: string
  updated_at: string
}

export interface Interaction {
  id: string
  lead_id: string
  campaign_id: string | null
  campaign_step_id: string | null
  agent_id: string | null
  type: string
  channel: string
  direction: string
  subject: string | null
  body: string
  metadata_json: Record<string, unknown>
  sentiment: string | null
  intent: string | null
  ai_analysis: Record<string, unknown> | null
  created_at: string
}

export interface Handoff {
  id: string
  lead_id: string
  from_agent_id: string
  to_user_id: string
  reason: string
  lead_score_at_handoff: number
  context_summary: string
  status: string
  accepted_at: string | null
  completed_at: string | null
  outcome_notes: string | null
  created_at: string
  updated_at: string
}

export interface Enrollment {
  id: string
  lead_id: string
  campaign_id: string
  current_step: number
  status: string
  enrolled_at: string
  last_step_executed_at: string | null
  next_step_at: string | null
  created_at: string
  updated_at: string
}

export interface DashboardOverview {
  pipeline: Record<string, number>
  metrics: {
    total_active_leads: number
    emails_sent_today: number
    emails_sent_week: number
    replies_today: number
    average_lead_score: number
    handoffs_this_week: number
  }
  agents: {
    id: string
    name: string
    type: string
    status: string
    last_active_at: string | null
    stats: Record<string, number>
  }[]
  activity_feed: {
    id: string
    type: string
    channel: string
    direction: string
    lead_id: string
    body: string
    created_at: string
  }[]
}
