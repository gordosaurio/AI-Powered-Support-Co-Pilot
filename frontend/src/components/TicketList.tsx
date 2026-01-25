import type { Ticket } from '../types/ticket'
import { TicketCard } from './TicketCard'
import { Loader2, AlertCircle, Inbox } from 'lucide-react'

interface TicketListProps {
  tickets: Ticket[]
  loading: boolean
  error: string | null
}

export function TicketList({ tickets, loading, error }: TicketListProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-12 h-12 text-teal-600 animate-spin mb-4" />
        <p className="text-slate-600 text-lg font-medium">Cargando tickets...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-rose-50 rounded-3xl border border-rose-200">
        <AlertCircle className="w-16 h-16 text-rose-500 mb-4" />
        <p className="text-rose-700 text-lg font-semibold mb-2">Error al cargar tickets</p>
        <p className="text-rose-600 text-sm">{error}</p>
      </div>
    )
  }

  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-slate-50 rounded-3xl border border-slate-200">
        <Inbox className="w-16 h-16 text-slate-400 mb-4" />
        <p className="text-slate-600 text-lg font-medium">No hay tickets disponibles</p>
        <p className="text-slate-500 text-sm mt-2">Crea tu primer ticket para comenzar</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
      {tickets.map((ticket) => (
        <TicketCard key={ticket.id} ticket={ticket} />
      ))}
    </div>
  )
}
