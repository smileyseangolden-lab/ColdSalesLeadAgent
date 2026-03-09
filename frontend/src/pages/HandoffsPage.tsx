import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getHandoffs, updateHandoff, getLead } from '../lib/api'
import { getStatusColor, formatDateTime, getScoreColor } from '../lib/utils'
import { ArrowRightLeft, Check, X, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import type { Handoff } from '../types'

export default function HandoffsPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: handoffs, isLoading } = useQuery({
    queryKey: ['handoffs', statusFilter],
    queryFn: () => getHandoffs(statusFilter ? { status: statusFilter } : {}).then(r => r.data as Handoff[]),
  })

  const acceptMutation = useMutation({
    mutationFn: (id: string) => updateHandoff(id, { status: 'accepted' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['handoffs'] })
      toast.success('Handoff accepted')
    },
  })

  const completeMutation = useMutation({
    mutationFn: ({ id, status, notes }: { id: string; status: string; notes: string }) =>
      updateHandoff(id, { status, outcome_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['handoffs'] })
      toast.success('Handoff updated')
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Handoffs</h1>
          <p className="text-gray-500">Leads ready for human follow-up</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm"
        >
          <option value="">All Statuses</option>
          {['pending', 'accepted', 'in_progress', 'converted', 'lost', 'rejected'].map(s => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-64 mb-3" />
              <div className="h-16 bg-gray-200 rounded" />
            </div>
          ))
        ) : handoffs?.map((handoff) => (
          <div key={handoff.id} className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div
              className="p-6 cursor-pointer"
              onClick={() => setExpandedId(expandedId === handoff.id ? null : handoff.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ArrowRightLeft className="w-5 h-5 text-primary-600" />
                  <div>
                    <p className="font-semibold">Lead #{handoff.lead_id.slice(0, 8)}</p>
                    <p className="text-sm text-gray-500">{handoff.reason}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getScoreColor(handoff.lead_score_at_handoff)}`}>
                    Score: {handoff.lead_score_at_handoff}
                  </span>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(handoff.status)}`}>
                    {handoff.status.replace('_', ' ')}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${expandedId === handoff.id ? 'rotate-180' : ''}`} />
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-2">{formatDateTime(handoff.created_at)}</p>
            </div>

            {expandedId === handoff.id && (
              <div className="px-6 pb-6 border-t pt-4">
                <h4 className="font-medium mb-2">AI Context Briefing</h4>
                <div className="bg-gray-50 rounded-lg p-4 text-sm whitespace-pre-wrap mb-4">
                  {handoff.context_summary}
                </div>

                {handoff.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => acceptMutation.mutate(handoff.id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm flex items-center gap-1.5"
                    >
                      <Check className="w-4 h-4" /> Accept
                    </button>
                    <button
                      onClick={() => completeMutation.mutate({ id: handoff.id, status: 'rejected', notes: '' })}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm flex items-center gap-1.5"
                    >
                      <X className="w-4 h-4" /> Reject
                    </button>
                  </div>
                )}

                {(handoff.status === 'accepted' || handoff.status === 'in_progress') && (
                  <OutcomeForm
                    handoffId={handoff.id}
                    onComplete={(status, notes) =>
                      completeMutation.mutate({ id: handoff.id, status, notes })
                    }
                  />
                )}

                {handoff.outcome_notes && (
                  <div className="mt-4">
                    <h4 className="font-medium text-sm mb-1">Outcome Notes</h4>
                    <p className="text-sm text-gray-600">{handoff.outcome_notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {handoffs?.length === 0 && (
          <div className="text-center py-16">
            <ArrowRightLeft className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-500">No handoffs</h3>
            <p className="text-gray-400 mt-1">Handoffs will appear here when AI agents identify hot leads</p>
          </div>
        )}
      </div>
    </div>
  )
}

function OutcomeForm({ handoffId, onComplete }: { handoffId: string; onComplete: (status: string, notes: string) => void }) {
  const [notes, setNotes] = useState('')
  return (
    <div className="space-y-3">
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Add outcome notes..."
        className="w-full px-3 py-2 border rounded-lg text-sm min-h-[60px]"
      />
      <div className="flex gap-2">
        <button
          onClick={() => onComplete('converted', notes)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm"
        >
          Mark Converted
        </button>
        <button
          onClick={() => onComplete('lost', notes)}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm"
        >
          Mark Lost
        </button>
      </div>
    </div>
  )
}
