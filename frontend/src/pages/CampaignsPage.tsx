import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getCampaigns } from '../lib/api'
import { getStatusColor, formatDate } from '../lib/utils'
import { Plus, Megaphone } from 'lucide-react'
import type { Campaign } from '../types'

export default function CampaignsPage() {
  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: () => getCampaigns().then(r => r.data as Campaign[]),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Campaigns</h1>
        <Link
          to="/campaigns/new"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> New Campaign
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border p-6 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
              <div className="h-20 bg-gray-200 rounded" />
            </div>
          ))
        ) : campaigns?.map((campaign) => (
          <Link
            key={campaign.id}
            to={`/campaigns/${campaign.id}`}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-primary-600" />
                <h3 className="font-semibold">{campaign.name}</h3>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(campaign.status)}`}>
                {campaign.status}
              </span>
            </div>
            {campaign.description && (
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">{campaign.description}</p>
            )}
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>{campaign.type.replace('_', ' ')}</span>
              <span>{campaign.steps.length} steps</span>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <div className="bg-gray-50 rounded p-2">
                <p className="text-lg font-bold">{campaign.stats_cache.total_enrolled || 0}</p>
                <p className="text-xs text-gray-500">Enrolled</p>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <p className="text-lg font-bold">{campaign.stats_cache.emails_sent || 0}</p>
                <p className="text-xs text-gray-500">Sent</p>
              </div>
              <div className="bg-gray-50 rounded p-2">
                <p className="text-lg font-bold">{campaign.stats_cache.replies || 0}</p>
                <p className="text-xs text-gray-500">Replies</p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-3">{formatDate(campaign.created_at)}</p>
          </Link>
        ))}
      </div>

      {campaigns?.length === 0 && (
        <div className="text-center py-16">
          <Megaphone className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-500">No campaigns yet</h3>
          <p className="text-gray-400 mt-1">Create your first campaign to start nurturing leads</p>
        </div>
      )}
    </div>
  )
}
