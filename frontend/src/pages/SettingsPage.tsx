import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getEmailAccounts, createEmailAccount, deleteEmailAccount, getUsers } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { Settings, Mail, Users, Shield, Key, Plus, Trash2, X } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const [tab, setTab] = useState('email')
  const user = useAuthStore(s => s.user)

  const tabs = [
    { id: 'email', label: 'Email Accounts', icon: Mail },
    { id: 'team', label: 'Team Management', icon: Users },
    { id: 'scoring', label: 'Lead Scoring', icon: Settings },
    { id: 'compliance', label: 'Compliance', icon: Shield },
    { id: 'api', label: 'API Keys', icon: Key },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="flex gap-2 border-b">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.id ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'email' && <EmailAccountsSection />}
      {tab === 'team' && <TeamSection />}
      {tab === 'scoring' && <ScoringSection />}
      {tab === 'compliance' && <ComplianceSection />}
      {tab === 'api' && <APISection />}
    </div>
  )
}

function EmailAccountsSection() {
  const [showAdd, setShowAdd] = useState(false)
  const queryClient = useQueryClient()

  const { data: accounts } = useQuery({
    queryKey: ['email-accounts'],
    queryFn: () => getEmailAccounts().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteEmailAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-accounts'] })
      toast.success('Account removed')
    },
  })

  const [form, setForm] = useState({
    email_address: '', smtp_host: 'smtp.gmail.com', smtp_port: 587,
    smtp_username: '', smtp_password: '', daily_send_limit: 50,
  })

  const addMutation = useMutation({
    mutationFn: () => createEmailAccount(form as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-accounts'] })
      setShowAdd(false)
      toast.success('Email account added')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Error'),
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Email Accounts</h2>
        <button onClick={() => setShowAdd(true)} className="flex items-center gap-1.5 text-sm text-primary-600">
          <Plus className="w-4 h-4" /> Add Account
        </button>
      </div>

      <div className="space-y-3">
        {accounts?.map((acc: any) => (
          <div key={acc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-sm">{acc.email_address}</p>
              <p className="text-xs text-gray-500">{acc.smtp_host} | {acc.sends_today}/{acc.daily_send_limit} sent today</p>
            </div>
            <button onClick={() => deleteMutation.mutate(acc.id)} className="text-red-400 hover:text-red-600">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        {accounts?.length === 0 && <p className="text-gray-400 text-sm">No email accounts configured</p>}
      </div>

      {showAdd && (
        <div className="mt-4 border-t pt-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <input placeholder="Email address" value={form.email_address} onChange={e => setForm({...form, email_address: e.target.value})} className="px-3 py-2 border rounded-lg text-sm" />
            <input placeholder="SMTP Host" value={form.smtp_host} onChange={e => setForm({...form, smtp_host: e.target.value})} className="px-3 py-2 border rounded-lg text-sm" />
            <input placeholder="SMTP Username" value={form.smtp_username} onChange={e => setForm({...form, smtp_username: e.target.value})} className="px-3 py-2 border rounded-lg text-sm" />
            <input type="password" placeholder="SMTP Password" value={form.smtp_password} onChange={e => setForm({...form, smtp_password: e.target.value})} className="px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div className="flex gap-2">
            <button onClick={() => addMutation.mutate()} disabled={addMutation.isPending} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm disabled:opacity-50">Save</button>
            <button onClick={() => setShowAdd(false)} className="px-4 py-2 border rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}

function TeamSection() {
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: () => getUsers().then(r => r.data) })
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-semibold mb-4">Team Members</h2>
      <div className="space-y-3">
        {users?.map((u: any) => (
          <div key={u.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 text-sm font-medium">
                {u.name.charAt(0)}
              </div>
              <div>
                <p className="font-medium text-sm">{u.name}</p>
                <p className="text-xs text-gray-500">{u.email}</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs px-2 py-1 bg-gray-200 rounded-full">{u.role}</span>
              {u.team && <p className="text-xs text-gray-400 mt-1">{u.team}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ScoringSection() {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-semibold mb-4">Lead Scoring Configuration</h2>
      <div className="space-y-4 text-sm">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium mb-2">Score Thresholds</h3>
            <div className="space-y-2">
              <div className="flex justify-between"><span>Cold</span><span>0-20</span></div>
              <div className="flex justify-between"><span>Warming</span><span>21-40</span></div>
              <div className="flex justify-between"><span>Engaged</span><span>41-60</span></div>
              <div className="flex justify-between"><span>Warm</span><span>61-80</span></div>
              <div className="flex justify-between"><span>Hot (Auto-handoff)</span><span>81-100</span></div>
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium mb-2">Engagement Signals</h3>
            <div className="space-y-2">
              <div className="flex justify-between"><span>Email open</span><span className="text-green-600">+2</span></div>
              <div className="flex justify-between"><span>Email click</span><span className="text-green-600">+5</span></div>
              <div className="flex justify-between"><span>Reply</span><span className="text-green-600">+15</span></div>
              <div className="flex justify-between"><span>Meeting booked</span><span className="text-green-600">+25</span></div>
              <div className="flex justify-between"><span>Bounce</span><span className="text-red-600">-50</span></div>
            </div>
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-yellow-800">
          Score configurations can be adjusted in the backend settings. Contact your admin for changes.
        </div>
      </div>
    </div>
  )
}

function ComplianceSection() {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-semibold mb-4">Compliance Settings</h2>
      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
          <div>
            <p className="font-medium">CAN-SPAM Compliance</p>
            <p className="text-gray-500">Unsubscribe links auto-added to all emails</p>
          </div>
          <span className="text-green-600 font-medium">Active</span>
        </div>
        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
          <div>
            <p className="font-medium">One-Click Unsubscribe</p>
            <p className="text-gray-500">Immediately stops all outreach on unsubscribe</p>
          </div>
          <span className="text-green-600 font-medium">Active</span>
        </div>
        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
          <div>
            <p className="font-medium">Rate Limiting</p>
            <p className="text-gray-500">Per-account daily send limits enforced</p>
          </div>
          <span className="text-green-600 font-medium">Active</span>
        </div>
        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
          <div>
            <p className="font-medium">Human Override</p>
            <p className="text-gray-500">Any user can pause agent activity on any lead</p>
          </div>
          <span className="text-green-600 font-medium">Active</span>
        </div>
      </div>
    </div>
  )
}

function APISection() {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <h2 className="text-lg font-semibold mb-4">API Access</h2>
      <div className="space-y-4 text-sm">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-medium mb-2">API Endpoints</h3>
          <code className="text-xs bg-gray-200 px-2 py-1 rounded">POST /api/v1/leads</code>
          <span className="text-gray-500 ml-2">Create a lead</span>
          <br /><br />
          <code className="text-xs bg-gray-200 px-2 py-1 rounded">POST /api/v1/leads/bulk</code>
          <span className="text-gray-500 ml-2">Bulk import leads</span>
          <br /><br />
          <code className="text-xs bg-gray-200 px-2 py-1 rounded">POST /api/v1/webhooks/inbound-email/sendgrid</code>
          <span className="text-gray-500 ml-2">Inbound email webhook</span>
        </div>
        <p className="text-gray-500">Use Bearer token authentication with your login token for all API requests.</p>
      </div>
    </div>
  )
}
