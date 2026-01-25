import { AlertCircle, Clock, CheckCircle2 } from 'lucide-react'
import type { Ticket } from '../types/ticket'
import { useState } from 'react'
import { TicketDetailModal } from './TicketDetailModal'

interface TicketListProps {
  tickets: Ticket[]
  loading: boolean
  error: string | null
}

export function TicketList({ tickets, loading, error }: TicketListProps) {
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleTicketClick = (ticket: Ticket) => {
    setSelectedTicket(ticket)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setSelectedTicket(null), 300)
  }

  const getSentimentColor = (sentiment: string | null) => {
    if (!sentiment) return 'border-l-slate-400'
    const s = sentiment.toLowerCase()
    if (s.includes('positivo')) return 'border-l-emerald-500'
    if (s.includes('negativo')) return 'border-l-rose-500'
    return 'border-l-slate-400'
  }

  const getCategoryColor = (category: string | null) => {
    if (!category) return 'bg-slate-100 text-slate-700 ring-slate-600/20'
    const c = category.toLowerCase()
    if (c.includes('técnico')) return 'bg-blue-100 text-blue-700 ring-blue-600/20'
    if (c.includes('facturación')) return 'bg-purple-100 text-purple-700 ring-purple-600/20'
    if (c.includes('comercial')) return 'bg-amber-100 text-amber-700 ring-amber-600/20'
    return 'bg-slate-100 text-slate-700 ring-slate-600/20'
  }

  const getSentimentBadgeColor = (sentiment: string | null) => {
    if (!sentiment) return 'bg-slate-100 text-slate-700 ring-slate-600/20'
    const s = sentiment.toLowerCase()
    if (s.includes('positivo')) return 'bg-emerald-100 text-emerald-700 ring-emerald-600/20'
    if (s.includes('negativo')) return 'bg-rose-100 text-rose-700 ring-rose-600/20'
    return 'bg-slate-100 text-slate-700 ring-slate-600/20'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-teal-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-8 text-center">
        <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
        <p className="text-red-800 font-medium text-lg">{error}</p>
      </div>
    )
  }

  if (tickets.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500 text-xl font-light">No hay tickets disponibles</p>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {tickets.map((ticket) => {
          const borderColor = getSentimentColor(ticket.sentiment)
          const categoryColor = getCategoryColor(ticket.category)
          const sentimentColor = getSentimentBadgeColor(ticket.sentiment)

          return (
            <div
              key={ticket.id}
              onClick={() => handleTicketClick(ticket)}
              className={`group bg-white rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden border-l-4 ${borderColor} hover:-translate-y-1 cursor-pointer`}
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2 text-slate-500">
                    <Clock className="w-4 h-4" />
                    <span className="text-sm font-medium">
                      {new Date(ticket.created_at).toLocaleDateString('es-ES', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  
                  {ticket.processed && (
                    <div className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full">
                      <CheckCircle2 className="w-4 h-4" />
                      <span className="text-sm font-semibold">Procesado</span>
                    </div>
                  )}
                </div>

                <p className="text-slate-800 leading-relaxed mb-6 text-base">
                  {ticket.description}
                </p>

                {(ticket.category || ticket.sentiment) && (
                  <div className="flex flex-wrap gap-2">
                    {ticket.category && (
                      <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ring-1 ring-inset ${categoryColor}`}>
                        {ticket.category}
                      </span>
                    )}
                    {ticket.sentiment && (
                      <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ring-1 ring-inset ${sentimentColor}`}>
                        {ticket.sentiment}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <TicketDetailModal
        ticket={selectedTicket}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </>
  )
}
