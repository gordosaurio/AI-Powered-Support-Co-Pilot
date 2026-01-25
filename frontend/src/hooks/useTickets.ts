import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import type { Ticket } from '../types/ticket'

export function useTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTickets = async () => {
    try {
      setLoading(true)
      const { data, error: fetchError } = await supabase
        .from('tickets')
        .select('*')
        .order('created_at', { ascending: false })

      if (fetchError) throw fetchError

      setTickets(data || [])
      setError(null)
    } catch (err) {
      console.error('Error fetching tickets:', err)
      setError(err instanceof Error ? err.message : 'Error al cargar tickets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()

    const channel = supabase
      .channel('tickets-realtime-channel')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tickets'
        },
        (payload) => {
          console.log('📡 Realtime event received:', payload)
          fetchTickets()
        }
      )
      .subscribe((status) => {
        console.log('📡 Subscription status:', status)
      })

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  return { tickets, loading, error, refetch: fetchTickets }
}
