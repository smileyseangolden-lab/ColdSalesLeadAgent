import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAgents, updateAgent } from '../lib/api'
import { getStatusColor, formatDateTime } from '../lib/utils'
import { Bot, Play, Pause, Settings } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import type { AIAgent } from '../types'

export default function AgentsPage() {
  const [editingAgent, setEditingAgent] = useState<AIAgent | null>(null)
  const queryClient = useQueryClient()

  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => getAgents().then(r => r.data as AIAgent[]),
    refetchInterval: 15000,
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateAgent(id, { status: status === 'active' ? 'paused' : 'active' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      toast.success('Agent status updated')
    },
  })

  const saveMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => updateAgent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      setEditingAgent(null)
      toast.success('Agent updated')
    },
  })

  const agentTypeInfo: Record<string, { color: string; description: string }> = {
    outbound_email: { color: 'bg-blue-100 text-blue-700', description: 'Sends personalized emails on campaign schedules' },
    reply_handler: { color: 'bg-green-100 text-green-700', description: 'Analyzes replies and responds autonomously' },
    lead_scorer: { color: 'bg-orange-100 text-orange-700', description: 'Evaluates and scores leads based on engagement' },
    research_agent: { color: 'bg-purple-100 text-purple-700', description: 'Enriches leads with company research data' },
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Agents</h1>
      <p className="text-gray-500">Autonomous agents that work your leads 24/7</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-48 mb-4" />
              <div className="h-20 bg-gray-200 rounded" />
            </div>
          ))
        ) : agents?.map((agent) => {
          const info = agentTypeInfo[agent.type] || { color: 'bg-gray-100 text-gray-700', description: '' }
          return (
            <div key={agent.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Bot className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{agent.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${info.color}`}>
                      {agent.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </span>
                </div>
              </div>

              <p className="text-sm text-gray-500 mb-4">{info.description}</p>

              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-gray-50 rounded p-2 text-center">
                  <p className="text-lg font-bold">{agent.stats.messages_sent_today || 0}</p>
                  <p className="text-xs text-gray-500">Today</p>
                </div>
                <div className="bg-gray-50 rounded p-2 text-center">
                  <p className="text-lg font-bold">{agent.stats.total_messages || 0}</p>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
                <div className="bg-gray-50 rounded p-2 text-center">
                  <p className="text-lg font-bold">{agent.stats.errors_today || 0}</p>
                  <p className="text-xs text-gray-500">Errors</p>
                </div>
              </div>

              <p className="text-xs text-gray-400 mb-4">
                Last active: {formatDateTime(agent.last_active_at)}
              </p>

              <div className="flex gap-2">
                <button
                  onClick={() => toggleMutation.mutate({ id: agent.id, status: agent.status })}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1.5 ${
                    agent.status === 'active'
                      ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  {agent.status === 'active' ? <><Pause className="w-3.5 h-3.5" /> Pause</> : <><Play className="w-3.5 h-3.5" /> Activate</>}
                </button>
                <button
                  onClick={() => setEditingAgent(agent)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 flex items-center gap-1.5"
                >
                  <Settings className="w-3.5 h-3.5" /> Configure
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Edit Modal */}
      {editingAgent && (
        <AgentEditModal
          agent={editingAgent}
          onClose={() => setEditingAgent(null)}
          onSave={(data) => saveMutation.mutate({ id: editingAgent.id, data })}
          saving={saveMutation.isPending}
        />
      )}
    </div>
  )
}

function AgentEditModal({ agent, onClose, onSave, saving }: {
  agent: AIAgent
  onClose: () => void
  onSave: (data: Record<string, unknown>) => void
  saving: boolean
}) {
  const [persona, setPersona] = useState(agent.persona)
  const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt)

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
        <h2 className="text-xl font-semibold mb-6">Configure: {agent.name}</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Persona</label>
            <textarea
              value={persona}
              onChange={e => setPersona(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm min-h-[100px]"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">System Prompt</label>
            <textarea
              value={systemPrompt}
              onChange={e => setSystemPrompt(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm min-h-[150px] font-mono"
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg text-sm">Cancel</button>
          <button
            onClick={() => onSave({ persona, system_prompt: systemPrompt })}
            disabled={saving}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
