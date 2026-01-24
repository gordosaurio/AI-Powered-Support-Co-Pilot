import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import type { Ticket } from '../types/ticket'

export function useTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTickets()
    subscribeToTickets()
  }, [])

  async function fetchTickets() {
    try {
      const { data, error: fetchError } = await supabase
        .from('tickets')
        .select('*')
        .order('created_at', { ascending: false })

      if (fetchError) throw fetchError
      
      setTickets(data || [])
      setLoading(false)
    } catch (err) {
      console.error('Error fetching tickets:', err)
      setError('Error al cargar los tickets')
      setLoading(false)
    }
  }

  function subscribeToTickets() {
    const channel = supabase
      .channel('tickets-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tickets'
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setTickets((prev) => [payload.new as Ticket, ...prev])
          } else if (payload.eventType === 'UPDATE') {
            setTickets((prev) =>
              prev.map((ticket) =>
                ticket.id === payload.new.id ? (payload.new as Ticket) : ticket
              )
            )
          } else if (payload.eventType === 'DELETE') {
            setTickets((prev) =>
              prev.filter((ticket) => ticket.id !== payload.old.id)
            )
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }

  return { tickets, loading, error }
}
