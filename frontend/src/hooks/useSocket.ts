import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import { useQueryClient } from '@tanstack/react-query'

export function useSocket() {
  const socketRef = useRef<Socket | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    const socket = io(import.meta.env.VITE_API_URL || window.location.origin, {
      path: '/ws/socket.io',
      transports: ['websocket', 'polling'],
    })

    socket.on('connect', () => {
      console.log('Socket connected')
    })

    socket.on('agent_action', () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    })

    socket.on('handoff_created', () => {
      queryClient.invalidateQueries({ queryKey: ['handoffs'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    })

    socket.on('lead_updated', () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    })

    socketRef.current = socket

    return () => {
      socket.disconnect()
    }
  }, [queryClient])

  return socketRef.current
}
