import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { getLeads, createLead, uploadLeads } from '../lib/api'
import { getStatusColor, getScoreColor, getScoreLabel, formatDate } from '../lib/utils'
import { Plus, Upload, Search, Filter, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import type { LeadListResponse } from '../types'

export default function LeadsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['leads', page, search, statusFilter],
    queryFn: () =>
      getLeads({ page, page_size: 50, search, status: statusFilter, sort_by: 'created_at', sort_order: 'desc' })
        .then((r) => r.data as LeadListResponse),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Leads</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
          >
            <Upload className="w-4 h-4" /> Upload CSV
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> Add Lead
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search leads..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">All Statuses</option>
          {['new','contacted','engaged','warm','hot','qualified','handed_off','converted','lost','do_not_contact'].map(s => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-gray-500 border-b">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} className="border-b animate-pulse">
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-32" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-24" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-28" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-16" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-12" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-20" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-200 rounded w-20" /></td>
                  </tr>
                ))
              ) : data?.leads.map((lead) => (
                <tr
                  key={lead.id}
                  onClick={() => navigate(`/leads/${lead.id}`)}
                  className="border-b hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium">{lead.full_name}</p>
                      <p className="text-gray-500 text-xs">{lead.email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">{lead.company_name}</td>
                  <td className="px-4 py-3 text-gray-600">{lead.job_title}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(lead.status)}`}>
                      {lead.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getScoreColor(lead.lead_score)}`}>
                      {lead.lead_score} - {getScoreLabel(lead.lead_score)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{lead.source.replace('_', ' ')}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(lead.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && (
          <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
            <p className="text-sm text-gray-500">
              Showing {((page - 1) * 50) + 1}-{Math.min(page * 50, data.total)} of {data.total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="p-1.5 rounded border disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(Math.min(data.total_pages, page + 1))}
                disabled={page >= data.total_pages}
                className="p-1.5 rounded border disabled:opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Lead Modal */}
      {showCreateModal && (
        <CreateLeadModal onClose={() => setShowCreateModal(false)} onCreated={() => {
          setShowCreateModal(false)
          queryClient.invalidateQueries({ queryKey: ['leads'] })
        }} />
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadModal onClose={() => setShowUploadModal(false)} onUploaded={() => {
          setShowUploadModal(false)
          queryClient.invalidateQueries({ queryKey: ['leads'] })
        }} />
      )}
    </div>
  )
}

function CreateLeadModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', phone: '', company_name: '',
    job_title: '', industry: '', linkedin_url: '', location_city: '',
    location_state: '', location_country: '', tags: '',
  })
  const mutation = useMutation({
    mutationFn: () => createLead({
      ...form,
      tags: form.tags ? form.tags.split(',').map(t => t.trim()) : [],
    }),
    onSuccess: () => { toast.success('Lead created'); onCreated() },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Error'),
  })

  const update = (key: string, val: string) => setForm({ ...form, [key]: val })

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Add New Lead</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">First Name *</label>
              <input required value={form.first_name} onChange={e => update('first_name', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Last Name *</label>
              <input required value={form.last_name} onChange={e => update('last_name', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email *</label>
              <input required type="email" value={form.email} onChange={e => update('email', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone</label>
              <input value={form.phone} onChange={e => update('phone', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Company *</label>
              <input required value={form.company_name} onChange={e => update('company_name', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Job Title *</label>
              <input required value={form.job_title} onChange={e => update('job_title', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Industry</label>
              <input value={form.industry} onChange={e => update('industry', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">LinkedIn URL</label>
              <input value={form.linkedin_url} onChange={e => update('linkedin_url', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="https://linkedin.com/in/..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">City</label>
              <input value={form.location_city} onChange={e => update('location_city', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">State</label>
              <input value={form.location_state} onChange={e => update('location_state', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Tags (comma-separated)</label>
            <input value={form.tags} onChange={e => update('tags', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="enterprise, manufacturing" />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg text-sm">Cancel</button>
            <button type="submit" disabled={mutation.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50">
              {mutation.isPending ? 'Creating...' : 'Create Lead'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function UploadModal({ onClose, onUploaded }: { onClose: () => void; onUploaded: () => void }) {
  const [result, setResult] = useState<any>(null)
  const [uploading, setUploading] = useState(false)
  const [tags, setTags] = useState('')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('tags', tags)
      const res = await uploadLeads(formData)
      setResult(res.data)
      toast.success(`${res.data.created} leads imported`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [tags])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
  })

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Upload Leads CSV</h2>
          <button onClick={onClose}><X className="w-5 h-5" /></button>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Tags for all imported leads</label>
          <input value={tags} onChange={e => setTags(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="q1_import, manufacturing" />
        </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
          {uploading ? (
            <p className="text-gray-600">Uploading...</p>
          ) : (
            <>
              <p className="text-gray-600 font-medium">Drop your CSV file here</p>
              <p className="text-sm text-gray-400 mt-1">or click to browse</p>
            </>
          )}
        </div>

        {result && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg text-sm space-y-1">
            <p className="font-medium">Import Results:</p>
            <p className="text-green-600">Created: {result.created}</p>
            <p className="text-yellow-600">Duplicates: {result.duplicates}</p>
            <p className="text-red-600">Errors: {result.errors}</p>
            {result.error_details?.length > 0 && (
              <details className="mt-2">
                <summary className="cursor-pointer text-gray-500">Error details</summary>
                <ul className="mt-1 space-y-1">
                  {result.error_details.map((e: any, i: number) => (
                    <li key={i} className="text-red-500">Row {e.row}: {e.error}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}

        <div className="flex justify-end gap-3 mt-4">
          <button onClick={result ? onUploaded : onClose} className="px-4 py-2 border rounded-lg text-sm">
            {result ? 'Done' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  )
}
