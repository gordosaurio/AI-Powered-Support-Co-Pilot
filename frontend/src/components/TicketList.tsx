import { TicketCard } from './TicketCard'
import type { Ticket } from '../types/ticket'

interface TicketListProps {
  tickets: Ticket[]
  loading: boolean
  error: string | null
}

export function TicketList({ tickets, loading, error }: TicketListProps) {
  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
        <p className="mt-6 text-gray-600 text-lg">Cargando tickets...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex justify-center">
        <div className="max-w-2xl bg-red-50 border border-red-200 rounded-2xl p-6 text-red-700">
          <p className="font-medium">{error}</p>
        </div>
      </div>
    )
  }

  if (tickets.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-6">
          <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p className="text-xl text-gray-900 font-medium mb-2">No hay tickets</p>
        <p className="text-gray-500">Crea uno para comenzar</p>
      </div>
    )
  }

  return (
    <div className="flex flex-wrap justify-center gap-6">
      {tickets.map((ticket) => (
        <TicketCard key={ticket.id} ticket={ticket} />
      ))}
    </div>
  )
}
