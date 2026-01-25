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
      setError(err instanceof Error ? err.message : 'Error al cargar tickets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()

    const subscription = supabase
      .channel('tickets-channel')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'tickets' }, () => {
        fetchTickets()
      })
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  return { tickets, loading, error, refetch: fetchTickets }
}
