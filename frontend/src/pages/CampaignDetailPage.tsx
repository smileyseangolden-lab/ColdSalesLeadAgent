import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCampaign, updateCampaign, getCampaignStats } from '../lib/api'
import { getStatusColor, formatDate } from '../lib/utils'
import { ArrowLeft, Play, Pause, Mail, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import type { Campaign } from '../types'

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: campaign } = useQuery({
    queryKey: ['campaign', id],
    queryFn: () => getCampaign(id!).then(r => r.data as Campaign),
  })

  const { data: stats } = useQuery({
    queryKey: ['campaign-stats', id],
    queryFn: () => getCampaignStats(id!).then(r => r.data),
  })

  const toggleStatus = useMutation({
    mutationFn: () => {
      const newStatus = campaign?.status === 'active' ? 'paused' : 'active'
      return updateCampaign(id!, { status: newStatus })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign', id] })
      toast.success('Campaign status updated')
    },
  })

  if (!campaign) {
    return <div className="animate-pulse"><div className="h-64 bg-gray-200 rounded-xl" /></div>
  }

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/campaigns')} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Campaigns
      </button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{campaign.name}</h1>
          {campaign.description && <p className="text-gray-500 mt-1">{campaign.description}</p>}
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(campaign.status)}`}>
            {campaign.status}
          </span>
          <button
            onClick={() => toggleStatus.mutate()}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${
              campaign.status === 'active'
                ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {campaign.status === 'active' ? <><Pause className="w-4 h-4" /> Pause</> : <><Play className="w-4 h-4" /> Activate</>}
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {[
            { label: 'Enrolled', value: stats.total_enrolled },
            { label: 'Emails Sent', value: stats.emails_sent },
            { label: 'Opens', value: stats.opens },
            { label: 'Clicks', value: stats.clicks },
            { label: 'Replies', value: stats.replies },
            { label: 'Open Rate', value: `${stats.open_rate.toFixed(1)}%` },
            { label: 'Reply Rate', value: `${stats.reply_rate.toFixed(1)}%` },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl shadow-sm border p-4 text-center">
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Steps */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Sequence Steps</h2>
        <div className="space-y-4">
          {campaign.steps.map((step, index) => (
            <div key={step.id} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold">
                  {step.step_number}
                </div>
                {index < campaign.steps.length - 1 && (
                  <div className="w-0.5 flex-1 bg-gray-200 my-1" />
                )}
              </div>
              <div className="flex-1 bg-gray-50 rounded-lg p-4 mb-2">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="w-4 h-4 text-gray-500" />
                  <span className="font-medium text-sm">{step.channel.replace('_', ' ')}</span>
                  {index > 0 && (
                    <span className="text-xs text-gray-400">
                      Wait {step.delay_days}d {step.delay_hours > 0 ? `${step.delay_hours}h` : ''}
                    </span>
                  )}
                  {step.ai_personalization_enabled && (
                    <span className="text-xs text-purple-600 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> AI
                    </span>
                  )}
                </div>
                {step.subject_template && (
                  <p className="text-sm font-medium mb-1">{step.subject_template}</p>
                )}
                <p className="text-sm text-gray-600 whitespace-pre-wrap line-clamp-4">{step.body_template}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-3">Campaign Settings</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Type:</span> {campaign.type.replace('_', ' ')}</div>
          <div><span className="text-gray-500">Timezone:</span> {(campaign.settings as any).timezone}</div>
          <div><span className="text-gray-500">Daily Limit:</span> {(campaign.settings as any).daily_send_limit}</div>
          <div><span className="text-gray-500">Created:</span> {formatDate(campaign.created_at)}</div>
        </div>
      </div>
    </div>
  )
}
