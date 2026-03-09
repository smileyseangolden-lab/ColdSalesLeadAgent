import { useQuery } from '@tanstack/react-query'
import { getDashboardOverview, getCampaignPerformance } from '../lib/api'
import { getStatusColor, formatDateTime, getScoreColor, getScoreLabel } from '../lib/utils'
import {
  Users, Mail, MessageSquare, TrendingUp, ArrowRightLeft, Activity, Bot,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#6b7280', '#3b82f6', '#eab308', '#f97316', '#ef4444', '#8b5cf6', '#6366f1', '#22c55e', '#9ca3af', '#dc2626']

export default function DashboardPage() {
  const { data: overview } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => getDashboardOverview().then((r) => r.data),
    refetchInterval: 30000,
  })

  const { data: campaignPerf } = useQuery({
    queryKey: ['campaign-performance'],
    queryFn: () => getCampaignPerformance().then((r) => r.data),
    refetchInterval: 60000,
  })

  if (!overview) {
    return <div className="animate-pulse space-y-4"><div className="h-32 bg-gray-200 rounded-xl" /><div className="h-64 bg-gray-200 rounded-xl" /></div>
  }

  const pipelineData = Object.entries(overview.pipeline || {}).map(([name, value]) => ({
    name: name.replace('_', ' '),
    value,
  }))

  const metrics = overview.metrics

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {[
          { label: 'Active Leads', value: metrics.total_active_leads, icon: Users, color: 'text-blue-600' },
          { label: 'Emails Today', value: metrics.emails_sent_today, icon: Mail, color: 'text-green-600' },
          { label: 'Emails This Week', value: metrics.emails_sent_week, icon: Mail, color: 'text-emerald-600' },
          { label: 'Replies Today', value: metrics.replies_today, icon: MessageSquare, color: 'text-purple-600' },
          { label: 'Avg Score', value: metrics.average_lead_score, icon: TrendingUp, color: 'text-orange-600' },
          { label: 'Handoffs This Week', value: metrics.handoffs_this_week, icon: ArrowRightLeft, color: 'text-red-600' },
        ].map((m) => (
          <div key={m.label} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{m.label}</span>
              <m.icon className={`w-5 h-5 ${m.color}`} />
            </div>
            <p className="text-2xl font-bold">{m.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Lead Pipeline</h2>
          {pipelineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pipelineData}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">No lead data yet</p>
          )}
        </div>

        {/* Agent Status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">AI Agent Status</h2>
          <div className="space-y-3">
            {overview.agents.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Bot className="w-5 h-5 text-primary-600" />
                  <div>
                    <p className="font-medium text-sm">{agent.name}</p>
                    <p className="text-xs text-gray-500">
                      Last active: {formatDateTime(agent.last_active_at)}
                    </p>
                  </div>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </span>
              </div>
            ))}
            {overview.agents.length === 0 && (
              <p className="text-gray-400 text-center py-8">No agents configured</p>
            )}
          </div>
        </div>
      </div>

      {/* Campaign Performance */}
      {campaignPerf && campaignPerf.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Campaign Performance</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-3 font-medium">Campaign</th>
                  <th className="pb-3 font-medium">Enrolled</th>
                  <th className="pb-3 font-medium">Sent</th>
                  <th className="pb-3 font-medium">Opens</th>
                  <th className="pb-3 font-medium">Replies</th>
                  <th className="pb-3 font-medium">Open Rate</th>
                  <th className="pb-3 font-medium">Reply Rate</th>
                </tr>
              </thead>
              <tbody>
                {campaignPerf.map((c: any) => (
                  <tr key={c.id} className="border-b last:border-0">
                    <td className="py-3 font-medium">{c.name}</td>
                    <td className="py-3">{c.enrolled}</td>
                    <td className="py-3">{c.sent}</td>
                    <td className="py-3">{c.opens}</td>
                    <td className="py-3">{c.replies}</td>
                    <td className="py-3">{c.open_rate}%</td>
                    <td className="py-3">{c.reply_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Activity Feed */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Today's Activity</h2>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {overview.activity_feed.map((item) => (
            <div key={item.id} className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg">
              <Activity className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm">
                  <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(item.type)}`}>
                    {item.type.replace('_', ' ')}
                  </span>
                  <span className="text-gray-500 ml-2">{item.body}</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">{formatDateTime(item.created_at)}</p>
              </div>
            </div>
          ))}
          {overview.activity_feed.length === 0 && (
            <p className="text-gray-400 text-center py-8">No activity today</p>
          )}
        </div>
      </div>
    </div>
  )
}
