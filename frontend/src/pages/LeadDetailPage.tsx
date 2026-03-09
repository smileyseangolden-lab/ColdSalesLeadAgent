import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getLead, updateLead, getLeadInteractions, addLeadNote } from '../lib/api'
import { getStatusColor, getScoreColor, getScoreLabel, formatDateTime } from '../lib/utils'
import { ArrowLeft, Mail, MessageSquare, Phone, Activity, StickyNote, TrendingUp, Globe } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import type { Lead, Interaction } from '../types'

const interactionIcons: Record<string, React.ElementType> = {
  email_sent: Mail,
  email_received: Mail,
  email_opened: Mail,
  email_clicked: Globe,
  email_bounced: Mail,
  note_added: StickyNote,
  score_change: TrendingUp,
  status_change: Activity,
  phone_call: Phone,
  meeting_scheduled: MessageSquare,
  handoff: Activity,
}

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [note, setNote] = useState('')

  const { data: lead } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => getLead(id!).then(r => r.data as Lead),
  })

  const { data: interactions } = useQuery({
    queryKey: ['lead-interactions', id],
    queryFn: () => getLeadInteractions(id!).then(r => r.data as Interaction[]),
  })

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateLead(id!, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', id] })
      toast.success('Status updated')
    },
  })

  const noteMutation = useMutation({
    mutationFn: (text: string) => addLeadNote(id!, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead-interactions', id] })
      setNote('')
      toast.success('Note added')
    },
  })

  if (!lead) {
    return <div className="animate-pulse space-y-4"><div className="h-48 bg-gray-200 rounded-xl" /></div>
  }

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/leads')} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Leads
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 text-xl font-bold">
                {lead.first_name.charAt(0)}{lead.last_name.charAt(0)}
              </div>
              <div>
                <h2 className="text-xl font-bold">{lead.full_name}</h2>
                <p className="text-gray-500">{lead.job_title}</p>
              </div>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Company</span>
                <span className="font-medium">{lead.company_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Email</span>
                <a href={`mailto:${lead.email}`} className="text-primary-600">{lead.email}</a>
              </div>
              {lead.phone && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Phone</span>
                  <span>{lead.phone}</span>
                </div>
              )}
              {lead.industry && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Industry</span>
                  <span>{lead.industry}</span>
                </div>
              )}
              {lead.company_size && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Company Size</span>
                  <span>{lead.company_size}</span>
                </div>
              )}
              {(lead.location_city || lead.location_state) && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Location</span>
                  <span>{[lead.location_city, lead.location_state, lead.location_country].filter(Boolean).join(', ')}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">Source</span>
                <span>{lead.source.replace('_', ' ')}</span>
              </div>
              {lead.linkedin_url && (
                <div className="flex justify-between">
                  <span className="text-gray-500">LinkedIn</span>
                  <a href={lead.linkedin_url} target="_blank" rel="noreferrer" className="text-primary-600 truncate max-w-[180px]">
                    Profile
                  </a>
                </div>
              )}
            </div>

            {lead.tags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {lead.tags.map(tag => (
                  <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{tag}</span>
                ))}
              </div>
            )}
          </div>

          {/* Score & Status */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold mb-4">Lead Score & Status</h3>
            <div className="flex items-center gap-4 mb-4">
              <div className={`text-4xl font-bold ${getScoreColor(lead.lead_score).split(' ')[0]}`}>
                {lead.lead_score}
              </div>
              <div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(lead.lead_score)}`}>
                  {getScoreLabel(lead.lead_score)}
                </span>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
              <div
                className="h-3 rounded-full bg-gradient-to-r from-blue-500 via-yellow-500 to-red-500"
                style={{ width: `${lead.lead_score}%` }}
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium mb-2">Status</label>
              <select
                value={lead.status}
                onChange={(e) => statusMutation.mutate(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm"
              >
                {['new','contacted','engaged','warm','hot','qualified','handed_off','converted','lost','do_not_contact'].map(s => (
                  <option key={s} value={s}>{s.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Notes */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold mb-3">Add Note</h3>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm min-h-[80px]"
              placeholder="Add a note about this lead..."
            />
            <button
              onClick={() => note && noteMutation.mutate(note)}
              disabled={!note || noteMutation.isPending}
              className="mt-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm disabled:opacity-50"
            >
              Add Note
            </button>
          </div>
        </div>

        {/* Timeline */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold mb-4">Interaction Timeline</h3>
            <div className="space-y-4">
              {interactions?.map((interaction) => {
                const Icon = interactionIcons[interaction.type] || Activity
                const isInbound = interaction.direction === 'inbound'
                return (
                  <div key={interaction.id} className="flex gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isInbound ? 'bg-green-100 text-green-600' :
                      interaction.direction === 'internal' ? 'bg-gray-100 text-gray-600' :
                      'bg-blue-100 text-blue-600'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(interaction.type)}`}>
                          {interaction.type.replace(/_/g, ' ')}
                        </span>
                        <span className="text-xs text-gray-400">{formatDateTime(interaction.created_at)}</span>
                        {interaction.sentiment && (
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            interaction.sentiment === 'positive' ? 'bg-green-100 text-green-600' :
                            interaction.sentiment === 'negative' ? 'bg-red-100 text-red-600' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {interaction.sentiment}
                          </span>
                        )}
                      </div>
                      {interaction.subject && (
                        <p className="text-sm font-medium mb-1">{interaction.subject}</p>
                      )}
                      <p className="text-sm text-gray-600 whitespace-pre-wrap">{interaction.body}</p>
                      {interaction.ai_analysis && (
                        <details className="mt-2">
                          <summary className="text-xs text-primary-600 cursor-pointer">AI Analysis</summary>
                          <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                            {JSON.stringify(interaction.ai_analysis, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                )
              })}
              {(!interactions || interactions.length === 0) && (
                <p className="text-gray-400 text-center py-8">No interactions yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
