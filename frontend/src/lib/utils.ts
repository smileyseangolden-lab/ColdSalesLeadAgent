import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | null) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatDateTime(date: string | null) {
  if (!date) return '-'
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function getScoreColor(score: number) {
  if (score >= 81) return 'text-red-600 bg-red-50'
  if (score >= 61) return 'text-orange-600 bg-orange-50'
  if (score >= 41) return 'text-yellow-600 bg-yellow-50'
  if (score >= 21) return 'text-blue-600 bg-blue-50'
  return 'text-gray-600 bg-gray-50'
}

export function getScoreLabel(score: number) {
  if (score >= 81) return 'Hot'
  if (score >= 61) return 'Warm'
  if (score >= 41) return 'Engaged'
  if (score >= 21) return 'Warming'
  return 'Cold'
}

export function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    new: 'bg-gray-100 text-gray-700',
    contacted: 'bg-blue-100 text-blue-700',
    engaged: 'bg-yellow-100 text-yellow-700',
    warm: 'bg-orange-100 text-orange-700',
    hot: 'bg-red-100 text-red-700',
    qualified: 'bg-purple-100 text-purple-700',
    handed_off: 'bg-indigo-100 text-indigo-700',
    converted: 'bg-green-100 text-green-700',
    lost: 'bg-gray-100 text-gray-500',
    do_not_contact: 'bg-red-100 text-red-500',
    // Campaign
    draft: 'bg-gray-100 text-gray-700',
    active: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-blue-100 text-blue-700',
    archived: 'bg-gray-100 text-gray-500',
    // Handoff
    pending: 'bg-yellow-100 text-yellow-700',
    accepted: 'bg-blue-100 text-blue-700',
    rejected: 'bg-red-100 text-red-700',
    in_progress: 'bg-indigo-100 text-indigo-700',
  }
  return colors[status] || 'bg-gray-100 text-gray-700'
}
