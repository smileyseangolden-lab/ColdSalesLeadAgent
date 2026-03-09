import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { createCampaign } from '../lib/api'
import { ArrowLeft, ArrowRight, Plus, Trash2, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'

interface StepForm {
  step_number: number
  channel: string
  delay_days: number
  delay_hours: number
  subject_template: string
  body_template: string
  ai_personalization_enabled: boolean
  ai_personalization_instructions: string
}

export default function CampaignCreatePage() {
  const navigate = useNavigate()
  const [wizardStep, setWizardStep] = useState(0)

  const [form, setForm] = useState({
    name: '',
    description: '',
    type: 'email_sequence',
    target_criteria: {} as Record<string, string[]>,
    settings: {
      sending_schedule: { days: ['mon', 'tue', 'wed', 'thu', 'fri'] },
      timezone: 'America/New_York',
      daily_send_limit: 50,
      min_wait_minutes: 60,
    },
  })

  const [steps, setSteps] = useState<StepForm[]>([
    {
      step_number: 1, channel: 'email', delay_days: 0, delay_hours: 0,
      subject_template: '', body_template: '',
      ai_personalization_enabled: true, ai_personalization_instructions: '',
    },
  ])

  const mutation = useMutation({
    mutationFn: () => createCampaign({ ...form, steps }),
    onSuccess: (res) => {
      toast.success('Campaign created!')
      navigate(`/campaigns/${res.data.id}`)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Error creating campaign'),
  })

  const addStep = () => {
    setSteps([...steps, {
      step_number: steps.length + 1, channel: 'email', delay_days: 3, delay_hours: 0,
      subject_template: '', body_template: '',
      ai_personalization_enabled: true, ai_personalization_instructions: '',
    }])
  }

  const removeStep = (index: number) => {
    if (steps.length <= 1) return
    const updated = steps.filter((_, i) => i !== index).map((s, i) => ({ ...s, step_number: i + 1 }))
    setSteps(updated)
  }

  const updateStep = (index: number, field: string, value: any) => {
    const updated = [...steps]
    ;(updated[index] as any)[field] = value
    setSteps(updated)
  }

  const wizardSteps = ['Basics', 'Sequence', 'Schedule', 'Review']

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <button onClick={() => navigate('/campaigns')} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Campaigns
      </button>

      <h1 className="text-2xl font-bold">Create Campaign</h1>

      {/* Wizard Progress */}
      <div className="flex items-center gap-2">
        {wizardSteps.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <button
              onClick={() => setWizardStep(i)}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                i <= wizardStep ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}
            >
              {i + 1}
            </button>
            <span className={`text-sm ${i <= wizardStep ? 'text-gray-900' : 'text-gray-400'}`}>{label}</span>
            {i < wizardSteps.length - 1 && <div className="w-8 h-0.5 bg-gray-200" />}
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {/* Step 1: Basics */}
        {wizardStep === 0 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Campaign Details</h2>
            <div>
              <label className="block text-sm font-medium mb-1">Campaign Name *</label>
              <input
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                placeholder="e.g., Q1 Manufacturing Outreach"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm min-h-[80px]"
                placeholder="What's the goal of this campaign?"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Campaign Type</label>
              <select
                value={form.type}
                onChange={e => setForm({ ...form, type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              >
                <option value="email_sequence">Email Sequence</option>
                <option value="linkedin_sequence">LinkedIn Sequence</option>
                <option value="multi_channel">Multi-Channel</option>
              </select>
            </div>
          </div>
        )}

        {/* Step 2: Sequence Builder */}
        {wizardStep === 1 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Email Sequence</h2>
              <button onClick={addStep} className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700">
                <Plus className="w-4 h-4" /> Add Step
              </button>
            </div>

            {steps.map((step, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">Step {step.step_number}</h3>
                  <div className="flex items-center gap-3">
                    {index > 0 && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-500">Wait</span>
                        <input
                          type="number" min={0}
                          value={step.delay_days}
                          onChange={e => updateStep(index, 'delay_days', parseInt(e.target.value) || 0)}
                          className="w-16 px-2 py-1 border rounded text-sm"
                        />
                        <span className="text-gray-500">days</span>
                      </div>
                    )}
                    {steps.length > 1 && (
                      <button onClick={() => removeStep(index)} className="text-red-400 hover:text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Subject Line</label>
                  <input
                    value={step.subject_template}
                    onChange={e => updateStep(index, 'subject_template', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                    placeholder="Use {{first_name}}, {{company_name}}, etc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email Body</label>
                  <textarea
                    value={step.body_template}
                    onChange={e => updateStep(index, 'body_template', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm min-h-[120px] font-mono"
                    placeholder="Write your email template here..."
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Variables: {'{{first_name}}'}, {'{{last_name}}'}, {'{{company_name}}'}, {'{{job_title}}'}, {'{{industry}}'}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={step.ai_personalization_enabled}
                      onChange={e => updateStep(index, 'ai_personalization_enabled', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-purple-500" /> AI Personalization
                    </span>
                  </label>
                </div>
                {step.ai_personalization_enabled && (
                  <div>
                    <label className="block text-sm font-medium mb-1">AI Instructions</label>
                    <input
                      value={step.ai_personalization_instructions}
                      onChange={e => updateStep(index, 'ai_personalization_instructions', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg text-sm"
                      placeholder="e.g., Reference their industry challenges, keep casual tone"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Step 3: Schedule */}
        {wizardStep === 2 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Schedule & Limits</h2>
            <div>
              <label className="block text-sm font-medium mb-1">Timezone</label>
              <select
                value={form.settings.timezone}
                onChange={e => setForm({ ...form, settings: { ...form.settings, timezone: e.target.value } })}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              >
                <option value="America/New_York">Eastern (ET)</option>
                <option value="America/Chicago">Central (CT)</option>
                <option value="America/Denver">Mountain (MT)</option>
                <option value="America/Los_Angeles">Pacific (PT)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Sending Days</label>
              <div className="flex gap-2">
                {['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].map(day => {
                  const active = form.settings.sending_schedule.days.includes(day)
                  return (
                    <button
                      key={day}
                      type="button"
                      onClick={() => {
                        const days = active
                          ? form.settings.sending_schedule.days.filter(d => d !== day)
                          : [...form.settings.sending_schedule.days, day]
                        setForm({ ...form, settings: { ...form.settings, sending_schedule: { days } } })
                      }}
                      className={`px-3 py-1.5 rounded text-sm font-medium ${
                        active ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {day.charAt(0).toUpperCase() + day.slice(1)}
                    </button>
                  )
                })}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Daily Send Limit</label>
              <input
                type="number" min={1} max={500}
                value={form.settings.daily_send_limit}
                onChange={e => setForm({ ...form, settings: { ...form.settings, daily_send_limit: parseInt(e.target.value) || 50 } })}
                className="w-32 px-3 py-2 border rounded-lg text-sm"
              />
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {wizardStep === 3 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Review & Create</h2>
            <div className="bg-gray-50 rounded-lg p-4 space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Name</span><span className="font-medium">{form.name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Type</span><span>{form.type.replace('_', ' ')}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Steps</span><span>{steps.length}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Timezone</span><span>{form.settings.timezone}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Daily Limit</span><span>{form.settings.daily_send_limit}</span></div>
            </div>
            <div className="space-y-2">
              <h3 className="font-medium">Sequence Steps:</h3>
              {steps.map((s, i) => (
                <div key={i} className="bg-gray-50 p-3 rounded text-sm">
                  <p className="font-medium">Step {s.step_number}: {s.channel}{i > 0 ? ` (after ${s.delay_days} days)` : ''}</p>
                  <p className="text-gray-500 truncate">{s.subject_template || '(no subject)'}</p>
                  {s.ai_personalization_enabled && <p className="text-purple-600 text-xs mt-1">AI Personalization enabled</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-4 border-t">
          <button
            onClick={() => setWizardStep(Math.max(0, wizardStep - 1))}
            disabled={wizardStep === 0}
            className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" /> Previous
          </button>
          {wizardStep < wizardSteps.length - 1 ? (
            <button
              onClick={() => setWizardStep(wizardStep + 1)}
              disabled={wizardStep === 0 && !form.name}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
            >
              Next <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
              className="px-6 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
            >
              {mutation.isPending ? 'Creating...' : 'Create Campaign'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
