import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Prefix helper for when baseURL doesn't include /api/v1
const prefix = import.meta.env.VITE_API_URL ? '/api/v1' : ''

// Auth
export const login = (email: string, password: string) =>
  api.post(`${prefix}/auth/login`, { email, password })

export const register = (data: { email: string; name: string; password: string; role?: string; team?: string }) =>
  api.post(`${prefix}/auth/register`, data)

export const getMe = () => api.get(`${prefix}/auth/me`)

// Leads
export const getLeads = (params: Record<string, string | number>) =>
  api.get(`${prefix}/leads`, { params })

export const getLead = (id: string) => api.get(`${prefix}/leads/${id}`)
export const createLead = (data: Record<string, unknown>) => api.post(`${prefix}/leads`, data)
export const updateLead = (id: string, data: Record<string, unknown>) => api.put(`${prefix}/leads/${id}`, data)
export const deleteLead = (id: string) => api.delete(`${prefix}/leads/${id}`)
export const bulkCreateLeads = (data: Record<string, unknown>) => api.post(`${prefix}/leads/bulk`, data)
export const uploadLeads = (formData: FormData) => api.post(`${prefix}/leads/upload`, formData)
export const getLeadInteractions = (id: string) => api.get(`${prefix}/leads/${id}/interactions`)
export const addLeadNote = (id: string, note: string) => api.post(`${prefix}/leads/${id}/notes`, { note })
export const getPipelineStats = () => api.get(`${prefix}/leads/stats/pipeline`)

// Campaigns
export const getCampaigns = (params?: Record<string, string>) => api.get(`${prefix}/campaigns`, { params })
export const getCampaign = (id: string) => api.get(`${prefix}/campaigns/${id}`)
export const createCampaign = (data: Record<string, unknown>) => api.post(`${prefix}/campaigns`, data)
export const updateCampaign = (id: string, data: Record<string, unknown>) => api.put(`${prefix}/campaigns/${id}`, data)
export const deleteCampaign = (id: string) => api.delete(`${prefix}/campaigns/${id}`)
export const enrollLead = (campaignId: string, leadId: string) =>
  api.post(`${prefix}/campaigns/${campaignId}/enroll`, { lead_id: leadId, campaign_id: campaignId })
export const bulkEnroll = (campaignId: string, leadIds: string[]) =>
  api.post(`${prefix}/campaigns/${campaignId}/enroll-bulk`, { lead_ids: leadIds })
export const getCampaignStats = (id: string) => api.get(`${prefix}/campaigns/${id}/stats`)

// Agents
export const getAgents = () => api.get(`${prefix}/agents`)
export const getAgent = (id: string) => api.get(`${prefix}/agents/${id}`)
export const updateAgent = (id: string, data: Record<string, unknown>) => api.put(`${prefix}/agents/${id}`, data)

// Handoffs
export const getHandoffs = (params?: Record<string, string>) => api.get(`${prefix}/handoffs`, { params })
export const getHandoff = (id: string) => api.get(`${prefix}/handoffs/${id}`)
export const updateHandoff = (id: string, data: Record<string, unknown>) => api.put(`${prefix}/handoffs/${id}`, data)

// Dashboard
export const getDashboardOverview = () => api.get(`${prefix}/dashboard/overview`)
export const getCampaignPerformance = () => api.get(`${prefix}/dashboard/campaign-performance`)

// Users
export const getUsers = () => api.get(`${prefix}/users`)

// Email Accounts
export const getEmailAccounts = () => api.get(`${prefix}/email-accounts`)
export const createEmailAccount = (data: Record<string, unknown>) => api.post(`${prefix}/email-accounts`, data)
export const updateEmailAccount = (id: string, data: Record<string, unknown>) => api.put(`${prefix}/email-accounts/${id}`, data)
export const deleteEmailAccount = (id: string) => api.delete(`${prefix}/email-accounts/${id}`)

export default api
